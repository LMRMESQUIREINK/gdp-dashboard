<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Optimize abilities: speed, images, database cleanup, plugin security
 * and conflicts, broken links.
 */

if ( ! function_exists( 'wpc_known_caching_plugins' ) ) {
	function wpc_known_caching_plugins() {
		return array(
			'wp-rocket', 'w3-total-cache', 'wp-super-cache', 'litespeed-cache',
			'wp-fastest-cache', 'sg-cachepress', 'breeze', 'hummingbird-performance',
			'autoptimize', 'perfmatters', 'flying-press', 'nitropack',
			'cache-enabler', 'wp-optimize', 'swift-performance-lite', 'comet-cache',
		);
	}

	function wpc_active_plugin_slugs() {
		$slugs = array();
		foreach ( (array) get_option( 'active_plugins', array() ) as $file ) {
			$slugs[] = strtok( $file, '/' );
		}
		return $slugs;
	}
}

WPC_Abilities::register(
	array(
		'name'        => 'speed_audit',
		'label'       => __( 'Speed audit', 'wp-connect' ),
		'category'    => 'optimize',
		'description' => __( 'Find out why the site is slow: homepage load time and size, number of scripts/styles/images, compression and caching headers, caching plugin, object cache, autoloaded options, database junk, and oversized images. Each finding says which ability fixes it. Run it before and after optimizing to compare.', 'wp-connect' ),
		'callback'    => function ( $input ) {
			global $wpdb;

			$start    = microtime( true );
			$response = wp_remote_get( home_url( '/' ), array( 'timeout' => 20 ) );
			$load_ms  = (int) round( ( microtime( true ) - $start ) * 1000 );
			$body     = is_wp_error( $response ) ? '' : wp_remote_retrieve_body( $response );
			$headers  = is_wp_error( $response ) ? array() : wp_remote_retrieve_headers( $response );

			$findings    = array();
			$deduct      = 0;
			$add_finding = function ( $severity, $text, $fix ) use ( &$findings, &$deduct ) {
				$findings[] = array( 'severity' => $severity, 'finding' => $text, 'fix' => $fix );
				$deduct    += 'high' === $severity ? 15 : ( 'medium' === $severity ? 7 : 3 );
			};

			if ( $load_ms > 1500 ) {
				$add_finding( 'high', sprintf( __( 'Homepage took %dms to load.', 'wp-connect' ), $load_ms ), 'db_cleanup, image_compress' );
			} elseif ( $load_ms > 800 ) {
				$add_finding( 'medium', sprintf( __( 'Homepage took %dms to load.', 'wp-connect' ), $load_ms ), 'db_cleanup, image_compress' );
			}

			$script_count = substr_count( $body, '<script' );
			$style_count  = substr_count( $body, 'rel="stylesheet"' ) + substr_count( $body, "rel='stylesheet'" );
			if ( $script_count > 25 ) {
				$add_finding( 'medium', sprintf( __( '%d scripts loaded on the homepage.', 'wp-connect' ), $script_count ), 'plugin_conflicts' );
			}
			if ( $style_count > 15 ) {
				$add_finding( 'medium', sprintf( __( '%d stylesheets loaded on the homepage.', 'wp-connect' ), $style_count ), 'plugin_conflicts' );
			}

			$encoding = isset( $headers['content-encoding'] ) ? $headers['content-encoding'] : '';
			if ( '' === $encoding ) {
				$add_finding( 'medium', __( 'The server is not compressing responses (no Content-Encoding header).', 'wp-connect' ), 'Ask your host to enable gzip/brotli' );
			}

			$active_slugs   = wpc_active_plugin_slugs();
			$caching_plugin = array_values( array_intersect( wpc_known_caching_plugins(), $active_slugs ) );
			if ( empty( $caching_plugin ) ) {
				$add_finding( 'high', __( 'No caching plugin is active.', 'wp-connect' ), 'plugin_install + plugin_activate a caching plugin' );
			}

			$has_object_cache = wp_using_ext_object_cache();
			if ( ! $has_object_cache ) {
				$add_finding( 'low', __( 'No persistent object cache is configured.', 'wp-connect' ), 'Ask your host about Redis/Memcached' );
			}

			$autoload_bytes = (int) $wpdb->get_var(
				"SELECT SUM(LENGTH(option_value)) FROM {$wpdb->options} WHERE autoload IN ('yes','on','auto-on','auto')" // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
			);
			$autoload_kb = round( $autoload_bytes / 1024 );
			if ( $autoload_kb > 2000 ) {
				$add_finding( 'high', sprintf( __( 'Autoloaded options total %dKB.', 'wp-connect' ), $autoload_kb ), 'db_cleanup' );
			} elseif ( $autoload_kb > 800 ) {
				$add_finding( 'medium', sprintf( __( 'Autoloaded options total %dKB.', 'wp-connect' ), $autoload_kb ), 'db_cleanup' );
			}

			$top_autoload = $wpdb->get_results(
				"SELECT option_name, LENGTH(option_value) AS bytes FROM {$wpdb->options} WHERE autoload IN ('yes','on','auto-on','auto') ORDER BY bytes DESC LIMIT 8" // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
			);

			$junk = wpc_db_junk_counts();
			if ( $junk['revisions'] > 200 ) {
				$add_finding( 'medium', sprintf( __( '%d post revisions stored.', 'wp-connect' ), $junk['revisions'] ), 'db_cleanup' );
			}
			if ( $junk['expired_transients'] > 100 ) {
				$add_finding( 'medium', sprintf( __( '%d expired transients.', 'wp-connect' ), $junk['expired_transients'] ), 'db_cleanup' );
			}
			if ( ( $junk['auto_drafts'] + $junk['trash'] ) > 50 ) {
				$add_finding( 'medium', sprintf( __( '%d auto-drafts/trashed posts.', 'wp-connect' ), $junk['auto_drafts'] + $junk['trash'] ), 'db_cleanup' );
			}
			if ( $junk['spam_comments'] > 100 ) {
				$add_finding( 'medium', sprintf( __( '%d spam comments.', 'wp-connect' ), $junk['spam_comments'] ), 'db_cleanup' );
			}

			$images       = wpc_large_images();
			$oversized    = array_filter(
				$images,
				function ( $img ) {
					return $img['kb'] > 300 || $img['width'] > 2560;
				}
			);
			if ( count( $oversized ) > 10 ) {
				$add_finding( 'high', sprintf( __( '%d images are larger than they need to be.', 'wp-connect' ), count( $oversized ) ), 'image_compress' );
			} elseif ( count( $oversized ) > 0 ) {
				$add_finding( 'medium', sprintf( __( '%d images are larger than they need to be.', 'wp-connect' ), count( $oversized ) ), 'image_compress' );
			}

			$plugin_count = count( (array) get_option( 'active_plugins', array() ) );
			if ( $plugin_count > 30 ) {
				$add_finding( 'low', sprintf( __( '%d plugins are active.', 'wp-connect' ), $plugin_count ), 'plugin_conflicts' );
			}
			if ( version_compare( PHP_VERSION, '8.1', '<' ) ) {
				$add_finding( 'low', __( 'PHP is older than 8.1.', 'wp-connect' ), 'Ask your host to upgrade PHP' );
			}

			$score = max( 1, 100 - $deduct );

			return array(
				'speed_score'    => $score,
				'load_ms'        => $load_ms,
				'script_count'   => $script_count,
				'style_count'    => $style_count,
				'caching_plugin' => $caching_plugin,
				'object_cache'   => $has_object_cache,
				'autoload_kb'    => $autoload_kb,
				'top_autoload'   => array_map(
					function ( $row ) {
						return array( 'option' => $row->option_name, 'kb' => round( $row->bytes / 1024, 1 ) );
					},
					(array) $top_autoload
				),
				'db_junk'        => $junk,
				'large_images'   => array_slice( $images, 0, 40 ),
				'findings'       => $findings,
			);
		},
	)
);

if ( ! function_exists( 'wpc_db_junk_counts' ) ) {
	function wpc_db_junk_counts() {
		global $wpdb;
		return array(
			'revisions'          => (int) $wpdb->get_var( "SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_type = 'revision'" ), // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
			'auto_drafts'        => (int) $wpdb->get_var( "SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_status = 'auto-draft'" ), // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
			'trash'              => (int) $wpdb->get_var( "SELECT COUNT(*) FROM {$wpdb->posts} WHERE post_status = 'trash'" ), // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
			'spam_comments'      => (int) $wpdb->get_var( "SELECT COUNT(*) FROM {$wpdb->comments} WHERE comment_approved = 'spam'" ), // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
			'trash_comments'     => (int) $wpdb->get_var( "SELECT COUNT(*) FROM {$wpdb->comments} WHERE comment_approved = 'trash'" ), // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
			'expired_transients' => (int) $wpdb->get_var(
				$wpdb->prepare(
					"SELECT COUNT(*) FROM {$wpdb->options} WHERE option_name LIKE %s AND CAST(option_value AS UNSIGNED) < %d", // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
					$wpdb->esc_like( '_transient_timeout_' ) . '%',
					time()
				)
			),
			'orphan_postmeta'    => (int) $wpdb->get_var(
				"SELECT COUNT(*) FROM {$wpdb->postmeta} WHERE post_id NOT IN (SELECT ID FROM {$wpdb->posts})" // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
			),
		);
	}

	function wpc_large_images() {
		$ids = get_posts(
			array(
				'post_type'      => 'attachment',
				'post_mime_type' => 'image',
				'post_status'    => 'inherit',
				'posts_per_page' => 300,
				'fields'         => 'ids',
			)
		);
		$out = array();
		foreach ( $ids as $id ) {
			$path = get_attached_file( $id );
			if ( ! $path || ! file_exists( $path ) ) {
				continue;
			}
			$size = filesize( $path );
			$meta = wp_get_attachment_metadata( $id );
			$out[] = array(
				'id'    => $id,
				'file'  => basename( $path ),
				'kb'    => round( $size / 1024 ),
				'width' => isset( $meta['width'] ) ? (int) $meta['width'] : 0,
			);
		}
		usort( $out, function ( $a, $b ) { return $b['kb'] <=> $a['kb']; } );
		return $out;
	}
}

WPC_Abilities::register(
	array(
		'name'         => 'image_compress',
		'label'        => __( 'Compress images', 'wp-connect' ),
		'category'     => 'optimize',
		'description'  => __( 'Shrink large images: resizes anything wider than max_width (default 2048px) and re-saves at quality 82. Up to 10 images per call. The original file is kept in a backup folder so Undo puts it back. Images that would not get smaller are left alone.', 'wp-connect' ),
		'writes'       => true,
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array(
				'ids'       => array( 'type' => 'array' ),
				'max_width' => array( 'type' => 'integer' ),
				'quality'   => array( 'type' => 'integer' ),
			),
			'required'   => array( 'ids' ),
		),
		'callback'     => function ( $input ) {
			$ids       = array_slice( array_map( 'intval', (array) $input['ids'] ), 0, 10 );
			$max_width = isset( $input['max_width'] ) ? max( 800, min( 4000, (int) $input['max_width'] ) ) : 2048;
			$quality   = isset( $input['quality'] ) ? max( 60, min( 95, (int) $input['quality'] ) ) : 82;

			$upload_dir = wp_upload_dir();
			$backup_dir = trailingslashit( $upload_dir['basedir'] ) . 'wpc-backups';
			if ( ! file_exists( $backup_dir ) ) {
				wp_mkdir_p( $backup_dir );
				file_put_contents( $backup_dir . '/index.php', "<?php\n// Silence is golden.\n" );
				file_put_contents( $backup_dir . '/.htaccess', "Deny from all\n" );
			}

			$results    = array();
			$saved_kb   = 0;

			foreach ( $ids as $id ) {
				$path = get_attached_file( $id );
				if ( ! $path || ! file_exists( $path ) ) {
					$results[] = array( 'id' => $id, 'changed' => false, 'reason' => 'file not found' );
					continue;
				}

				$before_size = filesize( $path );

				$editor = wp_get_image_editor( $path );
				if ( is_wp_error( $editor ) ) {
					$results[] = array( 'id' => $id, 'changed' => false, 'reason' => $editor->get_error_message() );
					continue;
				}

				$size = $editor->get_size();
				if ( $size['width'] > $max_width ) {
					$editor->resize( $max_width, null, false );
				}
				$editor->set_quality( $quality );

				$tmp   = $path . '.wpc-tmp';
				$saved = $editor->save( $tmp );
				if ( is_wp_error( $saved ) ) {
					$results[] = array( 'id' => $id, 'changed' => false, 'reason' => $saved->get_error_message() );
					continue;
				}

				$after_size = filesize( $saved['path'] );
				if ( $after_size >= $before_size ) {
					unlink( $saved['path'] );
					$results[] = array( 'id' => $id, 'changed' => false, 'reason' => 'already optimal' );
					continue;
				}

				// Back up the real, still-uncompressed original BEFORE it is
				// overwritten, so Undo restores the true original rather than
				// a copy of the already-compressed file.
				WPC_Backups::file( $path, 'Compressed ' . basename( $path ), $id, $backup_dir );
				rename( $saved['path'], $path );

				$meta = wp_generate_attachment_metadata( $id, $path );
				wp_update_attachment_metadata( $id, $meta );

				$results[]  = array(
					'id'            => $id,
					'changed'       => true,
					'before_kb'     => round( $before_size / 1024 ),
					'after_kb'      => round( $after_size / 1024 ),
				);
				$saved_kb += round( ( $before_size - $after_size ) / 1024 );
			}

			return array(
				'results'            => $results,
				'saved_kb'           => $saved_kb,
				'note'               => __( 'Thumbnails were not regenerated.', 'wp-connect' ),
			);
		},
	)
);

WPC_Abilities::register(
	array(
		'name'        => 'db_cleanup_preview',
		'label'       => __( 'Database cleanup preview', 'wp-connect' ),
		'category'    => 'optimize',
		'description' => __( 'Count database junk without deleting anything: post revisions, auto-drafts, trashed posts, spam and trashed comments, expired transients, and orphaned post meta. Run this before db_cleanup and show the owner the numbers.', 'wp-connect' ),
		'callback'    => function ( $input ) {
			return wpc_db_junk_counts();
		},
	)
);

WPC_Abilities::register(
	array(
		'name'         => 'db_cleanup',
		'label'        => __( 'Clean up database', 'wp-connect' ),
		'category'     => 'optimize',
		'description'  => __( 'Delete database junk. This can NOT be undone, so run db_cleanup_preview first and get the owner\'s OK (suggest a host backup). items picks what to clean: revisions, auto_drafts, trash, spam_comments, trash_comments, expired_transients, orphan_postmeta (default: all). Keeps the newest keep_revisions (default 3) per post. Removes up to 2000 revisions per call; run again if more remain.', 'wp-connect' ),
		'writes'       => true,
		'risky'        => true,
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array(
				'items'          => array( 'type' => 'array' ),
				'keep_revisions' => array( 'type' => 'integer' ),
			),
		),
		'callback'     => function ( $input ) {
			global $wpdb;

			$all_items = array( 'revisions', 'auto_drafts', 'trash', 'spam_comments', 'trash_comments', 'expired_transients', 'orphan_postmeta' );
			$items     = ! empty( $input['items'] ) ? array_intersect( (array) $input['items'], $all_items ) : $all_items;
			$keep      = isset( $input['keep_revisions'] ) ? max( 0, (int) $input['keep_revisions'] ) : 3;

			$removed = array_fill_keys( $all_items, 0 );

			if ( in_array( 'revisions', $items, true ) ) {
				$parents = $wpdb->get_col(
					"SELECT DISTINCT post_parent FROM {$wpdb->posts} WHERE post_type = 'revision' AND post_parent != 0" // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
				);
				$budget = 2000;
				foreach ( $parents as $parent_id ) {
					if ( $budget <= 0 ) {
						break;
					}
					$revisions = $wpdb->get_col(
						$wpdb->prepare( "SELECT ID FROM {$wpdb->posts} WHERE post_type = 'revision' AND post_parent = %d ORDER BY post_date DESC", $parent_id ) // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
					);
					$to_delete = array_slice( $revisions, $keep );
					foreach ( $to_delete as $rev_id ) {
						if ( $budget <= 0 ) {
							break;
						}
						wp_delete_post_revision( $rev_id );
						++$removed['revisions'];
						--$budget;
					}
				}
			}

			if ( in_array( 'auto_drafts', $items, true ) ) {
				$ids = $wpdb->get_col(
					$wpdb->prepare( "SELECT ID FROM {$wpdb->posts} WHERE post_status = 'auto-draft' AND post_date < %s LIMIT 1000", gmdate( 'Y-m-d H:i:s', time() - 7 * DAY_IN_SECONDS ) ) // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
				);
				foreach ( $ids as $id ) {
					wp_delete_post( $id, true );
					++$removed['auto_drafts'];
				}
			}

			if ( in_array( 'trash', $items, true ) ) {
				$ids = $wpdb->get_col(
					$wpdb->prepare( "SELECT ID FROM {$wpdb->posts} WHERE post_status = 'trash' AND post_modified < %s LIMIT 1000", gmdate( 'Y-m-d H:i:s', time() - 7 * DAY_IN_SECONDS ) ) // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
				);
				foreach ( $ids as $id ) {
					wp_delete_post( $id, true );
					++$removed['trash'];
				}
			}

			if ( in_array( 'spam_comments', $items, true ) ) {
				$ids = $wpdb->get_col( "SELECT comment_ID FROM {$wpdb->comments} WHERE comment_approved = 'spam' LIMIT 2000" ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
				foreach ( $ids as $id ) {
					wp_delete_comment( $id, true );
					++$removed['spam_comments'];
				}
			}

			if ( in_array( 'trash_comments', $items, true ) ) {
				$ids = $wpdb->get_col( "SELECT comment_ID FROM {$wpdb->comments} WHERE comment_approved = 'trash' LIMIT 2000" ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
				foreach ( $ids as $id ) {
					wp_delete_comment( $id, true );
					++$removed['trash_comments'];
				}
			}

			if ( in_array( 'expired_transients', $items, true ) ) {
				$before = (int) wpc_db_junk_counts()['expired_transients'];
				delete_expired_transients( true );
				$removed['expired_transients'] = $before;
			}

			if ( in_array( 'orphan_postmeta', $items, true ) ) {
				$removed['orphan_postmeta'] = (int) $wpdb->query(
					"DELETE FROM {$wpdb->postmeta} WHERE post_id NOT IN (SELECT ID FROM {$wpdb->posts})" // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
				);
			}

			return array(
				'removed'   => $removed,
				'remaining' => wpc_db_junk_counts(),
			);
		},
	)
);

WPC_Abilities::register(
	array(
		'name'        => 'plugin_security_check',
		'label'       => __( 'Plugin security check', 'wp-connect' ),
		'category'    => 'optimize',
		'description' => __( "Check every installed plugin for security risks: known vulnerabilities in the installed version (needs a free WPScan API token in WP-Connect -> Settings), plugins removed from WordPress.org (often for security), plugins not updated in over 2 years, and plugins with updates waiting. Fixing usually means plugin_update (ask the owner first) or replacing the plugin.", 'wp-connect' ),
		'callback'    => function ( $input ) {
			require_once ABSPATH . 'wp-admin/includes/plugin-install.php';
			if ( ! function_exists( 'get_plugin_updates' ) ) {
				require_once ABSPATH . 'wp-admin/includes/update.php';
			}

			$token       = WPC_Plugin::instance()->get_setting( 'wpscan_token', '' );
			$updates     = get_plugin_updates();
			$findings    = array();
			$checked     = 0;

			foreach ( get_plugins() as $file => $data ) {
				$slug   = strtok( $file, '/' );
				$result = array( 'plugin' => $file, 'name' => $data['Name'], 'risk' => 'none', 'reasons' => array() );

				$cache_key = 'wpc_wporg_' . $slug;
				$info      = get_transient( $cache_key );
				if ( false === $info ) {
					$info = plugins_api( 'plugin_information', array( 'slug' => $slug, 'fields' => array( 'sections' => false ) ) );
					set_transient( $cache_key, $info, 12 * HOUR_IN_SECONDS );
				}

				if ( is_wp_error( $info ) ) {
					$result['reasons'][] = __( 'Removed from WordPress.org (or never listed there).', 'wp-connect' );
					$result['risk']      = 'medium';
				} elseif ( isset( $info->last_updated ) && strtotime( $info->last_updated ) < time() - 2 * YEAR_IN_SECONDS ) {
					$result['reasons'][] = __( 'Not updated in over 2 years.', 'wp-connect' );
					$result['risk']      = 'medium';
				}

				if ( isset( $updates[ $file ] ) ) {
					$result['reasons'][] = __( 'An update is waiting.', 'wp-connect' );
					if ( 'none' === $result['risk'] ) {
						$result['risk'] = 'low';
					}
				}

				if ( $token && $checked < 25 ) {
					++$checked;
					$wpscan_cache_key = 'wpc_wpscan_' . $slug;
					$vuln             = get_transient( $wpscan_cache_key );
					if ( false === $vuln ) {
						$response = wp_remote_get(
							'https://wpscan.com/api/v3/plugins/' . rawurlencode( $slug ),
							array(
								'headers' => array( 'Authorization' => 'Token token=' . $token ),
								'timeout' => 15,
							)
						);
						if ( ! is_wp_error( $response ) ) {
							$code = wp_remote_retrieve_response_code( $response );
							if ( 429 === $code ) {
								$result['reasons'][] = __( 'WPScan daily limit reached.', 'wp-connect' );
							} elseif ( 404 !== $code ) {
								$vuln = json_decode( wp_remote_retrieve_body( $response ), true );
							}
						}
						set_transient( $wpscan_cache_key, $vuln ?: array(), DAY_IN_SECONDS );
					}

					if ( is_array( $vuln ) && isset( $vuln[ $slug ]['vulnerabilities'] ) ) {
						foreach ( $vuln[ $slug ]['vulnerabilities'] as $v ) {
							$fixed_in = isset( $v['fixed_in'] ) ? $v['fixed_in'] : null;
							if ( null === $fixed_in || version_compare( $data['Version'], $fixed_in, '<' ) ) {
								$result['reasons'][] = sprintf( __( 'Known vulnerability: %s', 'wp-connect' ), $v['title'] );
								$result['risk']      = 'high';
							}
						}
					}
				}

				if ( ! empty( $result['reasons'] ) ) {
					$findings[] = $result;
				}
			}

			$order = array( 'high' => 0, 'medium' => 1, 'low' => 2 );
			usort( $findings, function ( $a, $b ) use ( $order ) { return $order[ $a['risk'] ] <=> $order[ $b['risk'] ]; } );

			return array(
				'checked_with_wpscan' => (bool) $token,
				'findings'            => $findings,
			);
		},
	)
);

if ( ! function_exists( 'wpc_plugin_overlap_groups' ) ) {
	function wpc_plugin_overlap_groups() {
		return array(
			'SEO'                 => array( 'wordpress-seo', 'seo-by-rank-math', 'all-in-one-seo-pack', 'autodescription', 'wp-seopress', 'squirrly-seo' ),
			'Caching / speed'     => wpc_known_caching_plugins(),
			'Security / firewall' => array( 'wordfence', 'better-wp-security', 'sucuri-scanner', 'all-in-one-wp-security-and-firewall', 'ninjafirewall', 'defender-security', 'shield-security' ),
			'Image optimization'  => array( 'ewww-image-optimizer', 'imagify', 'shortpixel-image-optimiser', 'wp-smushit', 'optimole-wp', 'tiny-compress-images', 'robin-image-optimizer', 'webp-express' ),
			'Page builder'        => array( 'elementor', 'beaver-builder-lite-version', 'divi-builder', 'brizy', 'oxygen', 'siteorigin-panels', 'kingcomposer', 'js_composer' ),
			'Email (SMTP)'        => array( 'wp-mail-smtp', 'post-smtp', 'easy-wp-smtp', 'fluent-smtp', 'smtp-mailer' ),
		);
	}
}

WPC_Abilities::register(
	array(
		'name'        => 'plugin_conflicts',
		'label'       => __( 'Plugin conflict check', 'wp-connect' ),
		'category'    => 'optimize',
		'description' => __( "Look for plugins that clash: two or more active plugins doing the same job (SEO, caching, security, image optimization, page builders, SMTP), PHP errors in the error log grouped by plugin, plugins WordPress paused after a crash, and plugins needing a newer PHP or WordPress. Never deactivate anything without the owner's OK.", 'wp-connect' ),
		'callback'    => function ( $input ) {
			global $wp_version;

			$active = wpc_active_plugin_slugs();
			$overlaps = array();
			foreach ( wpc_plugin_overlap_groups() as $group => $slugs ) {
				$match = array_values( array_intersect( $slugs, $active ) );
				if ( count( $match ) > 1 ) {
					$overlaps[] = array( 'group' => $group, 'plugins' => $match );
				}
			}

			$errors_by_plugin = array();
			$log_path = ini_get( 'error_log' );
			if ( defined( 'WP_DEBUG_LOG' ) && is_string( WP_DEBUG_LOG ) ) {
				$log_path = WP_DEBUG_LOG;
			} elseif ( defined( 'WP_DEBUG_LOG' ) && WP_DEBUG_LOG ) {
				$log_path = WP_CONTENT_DIR . '/debug.log';
			}

			if ( $log_path && file_exists( $log_path ) && is_readable( $log_path ) ) {
				$size   = filesize( $log_path );
				$handle = fopen( $log_path, 'r' );
				if ( $handle ) {
					if ( $size > 400 * 1024 ) {
						fseek( $handle, -400 * 1024, SEEK_END );
					}
					$chunk = stream_get_contents( $handle );
					fclose( $handle );

					foreach ( preg_split( '/\r?\n/', $chunk ) as $line ) {
						if ( ! preg_match( '/PHP (Fatal error|Warning|Parse error|Notice|Deprecated)/', $line ) ) {
							continue;
						}
						if ( preg_match( '#/plugins/([a-z0-9_-]+)/#i', $line, $m ) ) {
							$plugin_slug = $m[1];
							if ( ! isset( $errors_by_plugin[ $plugin_slug ] ) ) {
								$errors_by_plugin[ $plugin_slug ] = array( 'count' => 0, 'example' => $line );
							}
							++$errors_by_plugin[ $plugin_slug ]['count'];
						}
					}
				}
			}

			$paused = function_exists( 'wp_paused_plugins' ) ? wp_paused_plugins()->get_all() : array();

			$mismatches = array();
			foreach ( get_plugins() as $file => $data ) {
				if ( ! empty( $data['RequiresPHP'] ) && version_compare( PHP_VERSION, $data['RequiresPHP'], '<' ) ) {
					$mismatches[] = array( 'plugin' => $file, 'needs' => 'PHP ' . $data['RequiresPHP'] );
				}
				if ( ! empty( $data['RequiresWP'] ) && version_compare( $wp_version, $data['RequiresWP'], '<' ) ) {
					$mismatches[] = array( 'plugin' => $file, 'needs' => 'WordPress ' . $data['RequiresWP'] );
				}
			}

			return array(
				'overlaps'   => $overlaps,
				'errors'     => $errors_by_plugin,
				'paused'     => $paused,
				'mismatches' => $mismatches,
			);
		},
	)
);

if ( ! function_exists( 'wpc_broken_links_check_one' ) ) {
	function wpc_broken_links_check_one( $url ) {
		$cache_key = 'wpc_link_' . md5( $url );
		$cached    = get_transient( $cache_key );
		if ( false !== $cached ) {
			return $cached;
		}

		$response = wp_remote_head( $url, array( 'timeout' => 6, 'redirection' => 5 ) );
		$code     = is_wp_error( $response ) ? 0 : wp_remote_retrieve_response_code( $response );

		if ( is_wp_error( $response ) || in_array( $code, array( 0, 403, 405, 501 ), true ) ) {
			$response = wp_remote_get( $url, array( 'timeout' => 6, 'redirection' => 5, 'limit_response_size' => 2048 ) );
			$code     = is_wp_error( $response ) ? 0 : wp_remote_retrieve_response_code( $response );
		}

		$broken = ( 0 === $code ) || ( $code >= 400 );
		set_transient( $cache_key, $broken ? array( 'broken' => true, 'code' => $code ) : array( 'broken' => false, 'code' => $code ), 6 * HOUR_IN_SECONDS );
		return array( 'broken' => $broken, 'code' => $code );
	}

	function wpc_extract_links( $post ) {
		$links = array();

		if ( preg_match_all( '/href=["\']([^"\']+)["\']/i', $post->post_content, $m ) ) {
			$links = array_merge( $links, $m[1] );
		}

		$elementor_data = get_post_meta( $post->ID, '_elementor_data', true );
		if ( $elementor_data ) {
			$unescaped = str_replace( '\/', '/', $elementor_data );
			if ( preg_match_all( '/"url"\s*:\s*"([^"]+)"/i', $unescaped, $m ) ) {
				$links = array_merge( $links, $m[1] );
			}
		}

		$home_host = wp_parse_url( home_url(), PHP_URL_HOST );
		$out       = array();
		foreach ( $links as $link ) {
			// Delimiter must not collide with the literal "#" alternative below.
			if ( preg_match( '~^(mailto:|tel:|#|javascript:|sms:)~i', $link ) ) {
				continue;
			}
			if ( 0 === strpos( $link, '/' ) && 0 !== strpos( $link, '//' ) ) {
				$link = home_url( $link );
			}
			$link = strtok( $link, '#' );
			if ( '' === trim( (string) $link ) ) {
				continue;
			}
			$out[ $link ] = true;
		}
		return array_keys( $out );
	}
}

WPC_Abilities::register(
	array(
		'name'         => 'broken_links',
		'label'        => __( 'Find broken links', 'wp-connect' ),
		'category'     => 'optimize',
		'description'  => __( "Scan published pages and posts for links that are broken (404, server errors, or sites that don't respond). Works in batches: pass next_offset back as offset until done is true. Fix internal ones with link_fix when the right new address is clear; report the rest to the owner.", 'wp-connect' ),
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array(
				'offset'   => array( 'type' => 'integer' ),
				'external' => array( 'type' => 'boolean' ),
			),
		),
		'callback'     => function ( $input ) {
			$offset    = isset( $input['offset'] ) ? max( 0, (int) $input['offset'] ) : 0;
			$include_external = ! isset( $input['external'] ) || $input['external'];

			$posts = get_posts(
				array(
					'post_type'      => array( 'post', 'page' ),
					'post_status'    => 'publish',
					'posts_per_page' => 15,
					'offset'         => $offset,
					'orderby'        => 'ID',
					'order'          => 'ASC',
				)
			);

			$home_host   = wp_parse_url( home_url(), PHP_URL_HOST );
			$broken      = array();
			$started     = microtime( true );

			foreach ( $posts as $post ) {
				if ( microtime( true ) - $started > 22 ) {
					break;
				}
				foreach ( wpc_extract_links( $post ) as $link ) {
					if ( microtime( true ) - $started > 22 ) {
						break 2;
					}
					$link_host = wp_parse_url( $link, PHP_URL_HOST );
					$internal  = ( ! $link_host || $link_host === $home_host );
					if ( ! $internal && ! $include_external ) {
						continue;
					}
					$result = wpc_broken_links_check_one( $link );
					if ( $result['broken'] ) {
						$broken[] = array(
							'post_id'  => $post->ID,
							'title'    => $post->post_title,
							'url'      => $link,
							'code'     => $result['code'],
							'internal' => $internal,
						);
					}
				}
			}

			$total      = (int) wp_count_posts( 'post' )->publish + (int) wp_count_posts( 'page' )->publish;
			$next       = $offset + count( $posts );
			$done       = count( $posts ) < 15 || $next >= $total;

			return array(
				'broken'      => $broken,
				'next_offset' => $next,
				'done'        => $done,
				'progress'    => array( 'checked' => $next, 'total' => $total ),
			);
		},
	)
);

WPC_Abilities::register(
	array(
		'name'         => 'link_fix',
		'label'        => __( 'Fix a link', 'wp-connect' ),
		'category'     => 'optimize',
		'description'  => __( 'Replace a broken link on one page or post with a new address, or remove the link (keeping its text) by leaving new_url empty. Works in normal content and Elementor layouts. Backed up first.', 'wp-connect' ),
		'writes'       => true,
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array(
				'post_id' => array( 'type' => 'integer' ),
				'old_url' => array( 'type' => 'string' ),
				'new_url' => array( 'type' => 'string' ),
			),
			'required'   => array( 'post_id', 'old_url' ),
		),
		'callback'     => function ( $input ) {
			$post = get_post( $input['post_id'] );
			if ( ! $post ) {
				throw new WPC_Ability_Error( __( 'No page or post found with that id.', 'wp-connect' ) );
			}

			$old_url    = $input['old_url'];
			$new_url    = isset( $input['new_url'] ) ? $input['new_url'] : '';
			$found      = false;
			$content    = $post->post_content;
			$elementor  = get_post_meta( $post->ID, '_elementor_data', true );

			if ( false !== strpos( $content, $old_url ) ) {
				$found = true;
			}
			if ( $elementor && ( false !== strpos( $elementor, $old_url ) || false !== strpos( $elementor, addcslashes( $old_url, '/' ) ) ) ) {
				$found = true;
			}
			if ( ! $found ) {
				throw new WPC_Ability_Error( __( 'That link was not found on this page.', 'wp-connect' ) );
			}

			WPC_Backups::post( $input['post_id'], 'Before link_fix', array( '_elementor_data' ) );

			if ( '' === $new_url ) {
				$content = preg_replace( '/<a\s[^>]*href=["\']' . preg_quote( $old_url, '/' ) . '["\'][^>]*>(.*?)<\/a>/is', '$1', $content );
			} else {
				$content = str_replace( '"' . $old_url . '"', '"' . $new_url . '"', $content );
				$content = str_replace( "'" . $old_url . "'", "'" . $new_url . "'", $content );
			}
			wp_update_post( array( 'ID' => $input['post_id'], 'post_content' => $content ) );

			if ( $elementor ) {
				$escaped_old = addcslashes( $old_url, '/' );
				$escaped_new = $new_url ? addcslashes( $new_url, '/' ) : '';
				$elementor   = str_replace( $old_url, $new_url, $elementor );
				$elementor   = str_replace( $escaped_old, $escaped_new, $elementor );
				update_post_meta( $input['post_id'], '_elementor_data', wp_slash( $elementor ) );
			}

			return array( 'fixed' => true );
		},
	)
);
