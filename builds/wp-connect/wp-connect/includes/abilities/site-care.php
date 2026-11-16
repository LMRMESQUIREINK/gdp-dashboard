<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Site Care abilities: health, plugins, SEO, media, page checks.
 */

if ( ! function_exists( 'wpc_activate_plugin_with_check' ) ) {
	/**
	 * Shared "activate and verify" path used by plugin_install and
	 * plugin_activate: back up, activate, check the homepage, and roll
	 * back (deactivate again) if the check fails.
	 */
	function wpc_activate_plugin_with_check( $plugin_file ) {
		if ( plugin_basename( WPC_FILE ) === $plugin_file ) {
			throw new WPC_Ability_Error( __( "WP-Connect can't deactivate or reactivate itself.", 'wp-connect' ) );
		}

		WPC_Backups::plugin_activated( $plugin_file, 'Before activating ' . $plugin_file );

		try {
			$result = activate_plugin( $plugin_file );
		} catch ( \Throwable $e ) {
			$result = new WP_Error( 'wpc_activate_exception', $e->getMessage() );
		}
		if ( is_wp_error( $result ) ) {
			throw new WPC_Ability_Error( $result->get_error_message() );
		}

		$check = WPC_Verify::check_url( home_url( '/' ) );
		if ( false === $check['verified'] ) {
			deactivate_plugins( $plugin_file );
			return array(
				'activated'   => false,
				'rolled_back' => true,
				'reason'      => $check['reason'],
			);
		}

		return array(
			'activated'   => true,
			'rolled_back' => false,
			'_verified'   => $check['verified'],
		);
	}
}

WPC_Abilities::register(
	array(
		'name'        => 'site_health',
		'label'       => __( 'Site health', 'wp-connect' ),
		'category'    => 'site_care',
		'description' => __( 'Versions, pending updates and common problems (debug mode on, search engines blocked, no HTTPS, plain permalinks, file editor on). Start site checks here.', 'wp-connect' ),
		'callback'    => function ( $input ) {
			global $wp_version;

			if ( ! function_exists( 'get_core_updates' ) ) {
				require_once ABSPATH . 'wp-admin/includes/update.php';
			}

			$warnings = array();

			$core_updates = get_core_updates();
			$core_update_available = is_array( $core_updates ) && ! empty( $core_updates ) && 'latest' !== $core_updates[0]->response;
			if ( $core_update_available ) {
				$warnings[] = __( 'A WordPress core update is available.', 'wp-connect' );
			}

			$plugin_updates = get_plugin_updates();
			if ( ! empty( $plugin_updates ) ) {
				$warnings[] = sprintf( __( '%d plugin(s) have an update waiting.', 'wp-connect' ), count( $plugin_updates ) );
			}

			if ( ! is_ssl() ) {
				$warnings[] = __( 'The site is not using HTTPS.', 'wp-connect' );
			}
			if ( '0' === get_option( 'blog_public' ) ) {
				$warnings[] = __( 'Search engines are discouraged from indexing this site.', 'wp-connect' );
			}
			if ( '' === get_option( 'permalink_structure' ) ) {
				$warnings[] = __( 'Permalinks are set to the plain, non-SEO-friendly format.', 'wp-connect' );
			}
			if ( defined( 'WP_DEBUG_DISPLAY' ) && WP_DEBUG_DISPLAY ) {
				$warnings[] = __( 'Debug output is shown to visitors (WP_DEBUG_DISPLAY).', 'wp-connect' );
			}
			if ( ! defined( 'DISALLOW_FILE_EDIT' ) || ! DISALLOW_FILE_EDIT ) {
				$warnings[] = __( 'The in-admin file editor is enabled.', 'wp-connect' );
			}
			if ( version_compare( PHP_VERSION, '8.1', '<' ) ) {
				$warnings[] = __( 'PHP is older than 8.1.', 'wp-connect' );
			}

			$inactive = array_diff( array_keys( get_plugins() ), (array) get_option( 'active_plugins', array() ) );
			if ( ! empty( $inactive ) ) {
				$warnings[] = sprintf( __( '%d installed plugin(s) are not active.', 'wp-connect' ), count( $inactive ) );
			}

			return array(
				'wordpress'      => $wp_version,
				'php'            => PHP_VERSION,
				'core_update'    => $core_update_available,
				'plugin_updates' => count( $plugin_updates ),
				'warnings'       => $warnings,
			);
		},
	)
);

WPC_Abilities::register(
	array(
		'name'        => 'plugins_list',
		'label'       => __( 'List plugins', 'wp-connect' ),
		'category'    => 'site_care',
		'description' => __( 'Every installed plugin with version, whether it is active and whether an update is waiting.', 'wp-connect' ),
		'callback'    => function ( $input ) {
			if ( ! function_exists( 'get_plugin_updates' ) ) {
				require_once ABSPATH . 'wp-admin/includes/update.php';
			}
			$active  = (array) get_option( 'active_plugins', array() );
			$updates = get_plugin_updates();

			$out = array();
			foreach ( get_plugins() as $file => $data ) {
				$out[] = array(
					'plugin'  => $file,
					'name'    => $data['Name'],
					'version' => $data['Version'],
					'active'  => in_array( $file, $active, true ),
					'update'  => isset( $updates[ $file ] ),
				);
			}
			return array( 'plugins' => $out );
		},
	)
);

WPC_Abilities::register(
	array(
		'name'         => 'plugin_install',
		'label'        => __( 'Install a plugin', 'wp-connect' ),
		'category'     => 'site_care',
		'description'  => __( 'Install a plugin from the official WordPress.org directory by its slug (e.g. "seo-by-rank-math"). It is installed switched off unless activate is true; activating checks the site still loads and switches it off again if not. Undo removes it.', 'wp-connect' ),
		'writes'       => true,
		'risky'        => true,
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array(
				'slug'     => array( 'type' => 'string' ),
				'activate' => array( 'type' => 'boolean' ),
			),
			'required'   => array( 'slug' ),
		),
		'callback'     => function ( $input ) {
			require_once ABSPATH . 'wp-admin/includes/plugin-install.php';
			require_once ABSPATH . 'wp-admin/includes/class-plugin-upgrader.php';
			require_once ABSPATH . 'wp-admin/includes/class-wp-ajax-upgrader-skin.php';
			require_once ABSPATH . 'wp-admin/includes/plugin.php';

			$slug = sanitize_title( $input['slug'] );

			foreach ( get_plugins() as $file => $data ) {
				if ( 0 === strpos( $file, $slug . '/' ) || $file === $slug . '.php' ) {
					throw new WPC_Ability_Error( sprintf( __( '"%s" is already installed.', 'wp-connect' ), $slug ) );
				}
			}

			$info = plugins_api( 'plugin_information', array( 'slug' => $slug, 'fields' => array( 'sections' => false ) ) );
			if ( is_wp_error( $info ) ) {
				throw new WPC_Ability_Error( sprintf( __( 'Could not find "%1$s" on WordPress.org: %2$s', 'wp-connect' ), $slug, $info->get_error_message() ) );
			}

			if ( ! WP_Filesystem() ) {
				throw new WPC_Ability_Error( __( 'Could not access the filesystem to install the plugin.', 'wp-connect' ) );
			}

			$upgrader = new Plugin_Upgrader( new WP_Ajax_Upgrader_Skin() );
			$result   = $upgrader->install( $info->download_link );
			if ( is_wp_error( $result ) || ! $result ) {
				throw new WPC_Ability_Error( __( 'Plugin install failed.', 'wp-connect' ) );
			}

			$plugin_file = $upgrader->plugin_info();
			if ( ! $plugin_file ) {
				throw new WPC_Ability_Error( __( 'Installed, but could not determine the plugin file.', 'wp-connect' ) );
			}

			WPC_Backups::plugin_installed( $plugin_file, 'Installed ' . $slug );

			if ( empty( $input['activate'] ) ) {
				return array( 'installed' => true, 'activated' => false, 'plugin' => $plugin_file );
			}

			$activation = wpc_activate_plugin_with_check( $plugin_file );
			return array_merge( array( 'installed' => true, 'plugin' => $plugin_file ), $activation );
		},
	)
);

WPC_Abilities::register(
	array(
		'name'         => 'plugin_activate',
		'label'        => __( 'Activate a plugin', 'wp-connect' ),
		'category'     => 'site_care',
		'description'  => __( 'Activate an installed plugin (slug or file). The homepage is checked right after; if it breaks, the plugin is switched off again automatically.', 'wp-connect' ),
		'writes'       => true,
		'risky'        => true,
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array( 'plugin' => array( 'type' => 'string' ) ),
			'required'   => array( 'plugin' ),
		),
		'callback'     => function ( $input ) {
			$plugin_file = wpc_resolve_plugin_file( $input['plugin'] );
			return wpc_activate_plugin_with_check( $plugin_file );
		},
	)
);

WPC_Abilities::register(
	array(
		'name'         => 'plugin_deactivate',
		'label'        => __( 'Deactivate a plugin', 'wp-connect' ),
		'category'     => 'site_care',
		'description'  => __( 'Switch off an active plugin. Undo switches it back on.', 'wp-connect' ),
		'writes'       => true,
		'risky'        => true,
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array( 'plugin' => array( 'type' => 'string' ) ),
			'required'   => array( 'plugin' ),
		),
		'callback'     => function ( $input ) {
			$plugin_file = wpc_resolve_plugin_file( $input['plugin'] );
			if ( plugin_basename( WPC_FILE ) === $plugin_file ) {
				throw new WPC_Ability_Error( __( "WP-Connect can't deactivate itself.", 'wp-connect' ) );
			}
			WPC_Backups::plugin_deactivated( $plugin_file, 'Deactivated ' . $plugin_file );
			deactivate_plugins( $plugin_file );
			return array( 'deactivated' => true );
		},
	)
);

WPC_Abilities::register(
	array(
		'name'         => 'plugin_update',
		'label'        => __( 'Update a plugin', 'wp-connect' ),
		'category'     => 'site_care',
		'description'  => __( 'Update an installed plugin to the latest version. This can NOT be undone automatically, so tell the owner first. The homepage is checked afterwards.', 'wp-connect' ),
		'writes'       => true,
		'risky'        => true,
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array( 'plugin' => array( 'type' => 'string' ) ),
			'required'   => array( 'plugin' ),
		),
		'callback'     => function ( $input ) {
			require_once ABSPATH . 'wp-admin/includes/class-plugin-upgrader.php';
			require_once ABSPATH . 'wp-admin/includes/class-wp-ajax-upgrader-skin.php';
			require_once ABSPATH . 'wp-admin/includes/update.php';

			$plugin_file = wpc_resolve_plugin_file( $input['plugin'] );

			$upgrader = new Plugin_Upgrader( new WP_Ajax_Upgrader_Skin() );
			$result   = $upgrader->upgrade( $plugin_file );
			if ( is_wp_error( $result ) || ! $result ) {
				throw new WPC_Ability_Error( __( 'Update failed.', 'wp-connect' ) );
			}

			$check = WPC_Verify::check_url( home_url( '/' ) );
			return array(
				'updated'   => true,
				'_verified' => $check['verified'],
			);
		},
	)
);

WPC_Abilities::register(
	array(
		'name'         => 'media_list',
		'label'        => __( 'List images', 'wp-connect' ),
		'category'     => 'site_care',
		'description'  => __( 'List images in the media library with their alt text. Set missing_alt to only get images with no alt text.', 'wp-connect' ),
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array(
				'missing_alt' => array( 'type' => 'boolean' ),
				'search'      => array( 'type' => 'string' ),
				'limit'       => array( 'type' => 'integer' ),
			),
		),
		'callback'     => function ( $input ) {
			$args = array(
				'post_type'      => 'attachment',
				'post_mime_type' => 'image',
				'post_status'    => 'inherit',
				'posts_per_page' => min( 500, max( 1, isset( $input['limit'] ) ? (int) $input['limit'] : 50 ) ),
			);
			if ( ! empty( $input['search'] ) ) {
				$args['s'] = $input['search'];
			}

			$items = array();
			foreach ( get_posts( $args ) as $attachment ) {
				$alt = get_post_meta( $attachment->ID, '_wp_attachment_image_alt', true );
				if ( ! empty( $input['missing_alt'] ) && '' !== $alt ) {
					continue;
				}
				$items[] = array(
					'id'    => $attachment->ID,
					'title' => $attachment->post_title,
					'file'  => basename( get_attached_file( $attachment->ID ) ),
					'alt'   => $alt,
				);
			}
			return array( 'images' => $items );
		},
	)
);

WPC_Abilities::register(
	array(
		'name'         => 'media_set_alt',
		'label'        => __( 'Set image alt text', 'wp-connect' ),
		'category'     => 'site_care',
		'description'  => __( "Set alt text on up to 50 images at once. items is a list of {id, alt}. Write alt text that describes the image for someone who can't see it.", 'wp-connect' ),
		'writes'       => true,
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array( 'items' => array( 'type' => 'array' ) ),
			'required'   => array( 'items' ),
		),
		'callback'     => function ( $input ) {
			$items   = array_slice( (array) $input['items'], 0, 50 );
			$updated = 0;
			foreach ( $items as $item ) {
				if ( empty( $item['id'] ) ) {
					continue;
				}
				update_post_meta( (int) $item['id'], '_wp_attachment_image_alt', sanitize_text_field( $item['alt'] ) );
				++$updated;
			}
			return array( 'updated' => $updated );
		},
	)
);

if ( ! function_exists( 'wpc_seo_plugin' ) ) {
	function wpc_seo_plugin() {
		if ( defined( 'WPSEO_VERSION' ) ) {
			return 'yoast';
		}
		if ( defined( 'RANK_MATH_VERSION' ) || class_exists( 'RankMath' ) ) {
			return 'rankmath';
		}
		if ( defined( 'SEOPRESS_VERSION' ) ) {
			return 'seopress';
		}
		return false;
	}

	function wpc_seo_meta_keys( $plugin ) {
		$keys = array(
			'yoast'    => array( '_yoast_wpseo_title', '_yoast_wpseo_metadesc' ),
			'rankmath' => array( 'rank_math_title', 'rank_math_description' ),
			'seopress' => array( '_seopress_titles_title', '_seopress_titles_desc' ),
		);
		return isset( $keys[ $plugin ] ) ? $keys[ $plugin ] : array( '', '' );
	}
}

WPC_Abilities::register(
	array(
		'name'         => 'seo_check',
		'label'        => __( 'SEO check', 'wp-connect' ),
		'category'     => 'site_care',
		'description'  => __( 'Check published pages or posts for missing or badly sized SEO titles and meta descriptions (works with Yoast, Rank Math or SEOPress).', 'wp-connect' ),
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array(
				'post_type' => array( 'type' => 'string' ),
				'limit'     => array( 'type' => 'integer' ),
			),
		),
		'callback'     => function ( $input ) {
			$plugin = wpc_seo_plugin();
			if ( ! $plugin ) {
				throw new WPC_Ability_Error( __( 'No supported SEO plugin (Yoast, Rank Math, SEOPress) is active.', 'wp-connect' ) );
			}
			list( $title_key, $desc_key ) = wpc_seo_meta_keys( $plugin );

			$posts = get_posts(
				array(
					'post_type'      => isset( $input['post_type'] ) ? $input['post_type'] : 'page',
					'post_status'    => 'publish',
					'posts_per_page' => min( 200, max( 1, isset( $input['limit'] ) ? (int) $input['limit'] : 50 ) ),
				)
			);

			$findings = array();
			foreach ( $posts as $post ) {
				$title = get_post_meta( $post->ID, $title_key, true );
				$desc  = get_post_meta( $post->ID, $desc_key, true );
				$issues = array();
				if ( '' === $desc ) {
					$issues[] = 'no description';
				} elseif ( strlen( $desc ) < 70 || strlen( $desc ) > 160 ) {
					$issues[] = 'description outside 70-160 characters';
				}
				if ( '' !== $title && strlen( $title ) < 15 ) {
					$issues[] = 'title under 15 characters';
				}
				if ( $issues ) {
					$findings[] = array(
						'id'     => $post->ID,
						'title'  => $post->post_title,
						'issues' => $issues,
					);
				}
			}

			return array( 'plugin' => $plugin, 'findings' => $findings );
		},
	)
);

WPC_Abilities::register(
	array(
		'name'         => 'seo_set_meta',
		'label'        => __( 'Set SEO title & description', 'wp-connect' ),
		'category'     => 'site_care',
		'description'  => __( 'Set the SEO title and/or meta description of a page or post in the active SEO plugin. Keep descriptions 120-155 characters.', 'wp-connect' ),
		'writes'       => true,
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array(
				'id'          => array( 'type' => 'integer' ),
				'title'       => array( 'type' => 'string' ),
				'description' => array( 'type' => 'string' ),
			),
			'required'   => array( 'id' ),
		),
		'callback'     => function ( $input ) {
			$plugin = wpc_seo_plugin();
			if ( ! $plugin ) {
				throw new WPC_Ability_Error( __( 'No supported SEO plugin (Yoast, Rank Math, SEOPress) is active.', 'wp-connect' ) );
			}
			if ( ! get_post( $input['id'] ) ) {
				throw new WPC_Ability_Error( __( 'No page or post found with that id.', 'wp-connect' ) );
			}
			list( $title_key, $desc_key ) = wpc_seo_meta_keys( $plugin );

			WPC_Backups::post( $input['id'], 'Before SEO meta change', array( $title_key, $desc_key ) );

			if ( isset( $input['title'] ) ) {
				update_post_meta( $input['id'], $title_key, sanitize_text_field( $input['title'] ) );
			}
			if ( isset( $input['description'] ) ) {
				update_post_meta( $input['id'], $desc_key, sanitize_text_field( $input['description'] ) );
			}

			return array( 'updated' => true );
		},
	)
);

WPC_Abilities::register(
	array(
		'name'         => 'check_page',
		'label'        => __( 'Check a page loads', 'wp-connect' ),
		'category'     => 'site_care',
		'description'  => __( 'Load a page (by id or URL on this site) and check it returns 200 with no PHP errors.', 'wp-connect' ),
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array(
				'id'  => array( 'type' => 'integer' ),
				'url' => array( 'type' => 'string' ),
			),
		),
		'callback'     => function ( $input ) {
			if ( ! empty( $input['id'] ) ) {
				$url = get_permalink( $input['id'] );
				if ( ! $url ) {
					throw new WPC_Ability_Error( __( 'No page or post found with that id.', 'wp-connect' ) );
				}
			} elseif ( ! empty( $input['url'] ) ) {
				$url = $input['url'];
				$home_host = wp_parse_url( home_url(), PHP_URL_HOST );
				$url_host  = wp_parse_url( $url, PHP_URL_HOST );
				if ( $url_host && $home_host && $url_host !== $home_host ) {
					throw new WPC_Ability_Error( __( 'check_page only checks pages on this site.', 'wp-connect' ) );
				}
			} else {
				throw new WPC_Ability_Error( __( 'Provide either id or url.', 'wp-connect' ) );
			}

			$check = WPC_Verify::check_url( $url );
			return array(
				'url'      => $url,
				'verified' => $check['verified'],
				'reason'   => $check['reason'],
			);
		},
	)
);

if ( ! function_exists( 'wpc_resolve_plugin_file' ) ) {
	function wpc_resolve_plugin_file( $plugin ) {
		foreach ( get_plugins() as $file => $data ) {
			if ( $file === $plugin || 0 === strpos( $file, rtrim( $plugin, '/' ) . '/' ) ) {
				return $file;
			}
		}
		throw new WPC_Ability_Error( sprintf( __( 'No installed plugin matches "%s".', 'wp-connect' ), $plugin ) );
	}
}
