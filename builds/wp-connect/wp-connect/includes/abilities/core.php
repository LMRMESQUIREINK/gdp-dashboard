<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Core abilities: always available regardless of mode. Site overview,
 * the playbook, feedback/lessons, the abilities report, Claude-written
 * abilities, and skills.
 */

WPC_Abilities::register(
	array(
		'name'        => 'wpc_site_overview',
		'label'       => __( 'Site overview', 'wp-connect' ),
		'category'    => 'core',
		'description' => __( 'Get the basics about this WordPress site: theme, page builder, SEO plugin, WP-Connect mode and what is allowed. Call this first.', 'wp-connect' ),
		'locked'      => true,
		'callback'    => function ( $input ) {
			global $wp_version;

			$theme        = wp_get_theme();
			$parent       = $theme->parent();
			$active_plugins = array();
			foreach ( (array) get_option( 'active_plugins', array() ) as $plugin_file ) {
				$data             = get_plugin_data( WP_PLUGIN_DIR . '/' . $plugin_file, false, false );
				$active_plugins[] = array(
					'plugin'  => $plugin_file,
					'name'    => $data['Name'],
					'version' => $data['Version'],
				);
			}

			$page_builder = 'none';
			if ( class_exists( '\Elementor\Plugin' ) ) {
				$page_builder = 'elementor';
			} elseif ( defined( 'ET_BUILDER_PLUGIN_VERSION' ) ) {
				$page_builder = 'divi';
			} elseif ( class_exists( 'FLBuilder' ) ) {
				$page_builder = 'beaver-builder';
			}

			$seo_plugin = false;
			if ( defined( 'WPSEO_VERSION' ) ) {
				$seo_plugin = 'yoast';
			} elseif ( defined( 'RANK_MATH_VERSION' ) || class_exists( 'RankMath' ) ) {
				$seo_plugin = 'rankmath';
			} elseif ( defined( 'SEOPRESS_VERSION' ) ) {
				$seo_plugin = 'seopress';
			}

			$counts = wp_count_posts( 'page' );

			return array(
				'site'        => get_bloginfo( 'name' ),
				'url'         => home_url( '/' ),
				'wordpress'   => $wp_version,
				'php'         => PHP_VERSION,
				'theme'       => array(
					'name'   => $theme->get( 'Name' ),
					'parent' => $parent ? $parent->get( 'Name' ) : null,
				),
				'page_builder'  => $page_builder,
				'seo_plugin'    => $seo_plugin,
				'woocommerce'   => class_exists( 'WooCommerce' ),
				'active_plugins' => $active_plugins,
				'pages'         => array(
					'published' => (int) $counts->publish,
					'draft'     => (int) $counts->draft,
				),
				'wp_connect'  => array(
					'mode'            => WPC_Plugin::instance()->mode(),
					'allow_publish'   => (bool) WPC_Plugin::instance()->get_setting( 'allow_publish' ),
					'abilities_count' => count( WPC_Abilities::usable_names() ),
					'playbook_topics' => array( 'general', 'site_care', 'abilities' ),
				),
			);
		},
	)
);

WPC_Abilities::register(
	array(
		'name'         => 'wpc_playbook',
		'label'        => __( 'Read the playbook', 'wp-connect' ),
		'category'     => 'core',
		'description'  => __( 'Read the how-to guide for an area before working in it, plus every lesson saved for that area. Topics: general, site_care, abilities.', 'wp-connect' ),
		'locked'       => true,
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array(
				'topic' => array( 'type' => 'string', 'enum' => array( 'general', 'site_care', 'abilities' ) ),
			),
			'required'   => array( 'topic' ),
		),
		'callback'     => function ( $input ) {
			$topic = $input['topic'];
			$guide = wpc_playbook_text( $topic );

			$lessons = array();
			foreach ( WPC_Abilities::lessons( $topic ) as $lesson ) {
				$lessons[] = $lesson->lesson;
			}
			foreach ( WPC_Abilities::all() as $name => $ability ) {
				if ( $ability['category'] === $topic ) {
					foreach ( WPC_Abilities::lessons( $name ) as $lesson ) {
						$lessons[] = '[' . $name . '] ' . $lesson->lesson;
					}
				}
			}

			return array(
				'guide'   => $guide,
				'lessons' => $lessons,
			);
		},
	)
);

WPC_Abilities::register(
	array(
		'name'         => 'wpc_lesson_save',
		'label'        => __( 'Save a lesson', 'wp-connect' ),
		'category'     => 'core',
		'description'  => __( 'Remember something you learned on this site so the next run goes right first time. Save it against an ability name (e.g. plugin_activate) or a topic (site_care, general). Keep it short and specific, e.g. "Rank Math is the SEO plugin here, not Yoast".', 'wp-connect' ),
		'locked'       => true,
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array(
				'topic'  => array( 'type' => 'string' ),
				'lesson' => array( 'type' => 'string' ),
			),
			'required'   => array( 'topic', 'lesson' ),
		),
		'callback'     => function ( $input ) {
			$id = WPC_Abilities::save_lesson( $input['topic'], $input['lesson'], 'claude' );
			return array( 'saved' => (bool) $id );
		},
	)
);

WPC_Abilities::register(
	array(
		'name'         => 'wpc_run_feedback',
		'label'        => __( 'Rate a result', 'wp-connect' ),
		'category'     => 'core',
		'description'  => __( 'Record whether a run actually did what the owner wanted. Use it when the owner says a result was good or wrong. This feeds the ability\'s 1-100 rating.', 'wp-connect' ),
		'locked'       => true,
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array(
				'run_id' => array( 'type' => 'integer' ),
				'good'   => array( 'type' => 'boolean' ),
				'note'   => array( 'type' => 'string' ),
			),
			'required'   => array( 'run_id', 'good' ),
		),
		'callback'     => function ( $input ) {
			$rating = WPC_Abilities::record_feedback( $input['run_id'], $input['good'], isset( $input['note'] ) ? $input['note'] : '' );
			if ( null === $rating ) {
				throw new WPC_Ability_Error( __( 'No run found with that id.', 'wp-connect' ) );
			}
			return array( 'rating' => $rating );
		},
	)
);

WPC_Abilities::register(
	array(
		'name'        => 'wpc_abilities_report',
		'label'       => __( 'Abilities report', 'wp-connect' ),
		'category'    => 'core',
		'description' => __( 'List every ability with its 1-100 rating, run count, success rate and last error. Use it to find weak abilities to improve.', 'wp-connect' ),
		'locked'      => true,
		'callback'    => function ( $input ) {
			$report = array();
			foreach ( WPC_Abilities::all() as $name => $ability ) {
				$rating    = WPC_Abilities::rating( $name );
				$report[]  = array(
					'name'         => $name,
					'label'        => $ability['label'],
					'category'     => $ability['category'],
					'score'        => $rating['score'],
					'runs'         => $rating['runs'],
					'success_rate' => $rating['success_rate'],
					'last_error'   => $rating['last_error'],
				);
			}
			usort(
				$report,
				function ( $a, $b ) {
					if ( null === $a['score'] && null === $b['score'] ) {
						return 0;
					}
					if ( null === $a['score'] ) {
						return 1;
					}
					if ( null === $b['score'] ) {
						return -1;
					}
					return $a['score'] <=> $b['score'];
				}
			);

			return array(
				'abilities' => $report,
				'pending'   => WPC_Abilities::pending_count(),
			);
		},
	)
);

WPC_Abilities::register(
	array(
		'name'         => 'wpc_ability_create',
		'label'        => __( 'Write a new ability', 'wp-connect' ),
		'category'     => 'core',
		'description'  => __( 'Write a brand new ability for this site when none of the existing ones can do the job. It is saved as pending and only goes live after the owner reviews and approves the code on WP-Connect -> Abilities. Read wpc_playbook topic "abilities" first.', 'wp-connect' ),
		'locked'       => true,
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array(
				'name'          => array( 'type' => 'string' ),
				'label'         => array( 'type' => 'string' ),
				'description'   => array( 'type' => 'string' ),
				'input_schema'  => array( 'type' => 'object' ),
				'code'          => array( 'type' => 'string' ),
				'writes'        => array( 'type' => 'boolean' ),
				'risky'         => array( 'type' => 'boolean' ),
			),
			'required'   => array( 'name', 'label', 'description', 'code' ),
		),
		'callback'     => function ( $input ) {
			$result = WPC_Abilities::propose( $input, false );
			$result['review_link'] = admin_url( 'admin.php?page=wp-connect&tab=abilities#pending' );
			return $result;
		},
	)
);

WPC_Abilities::register(
	array(
		'name'         => 'wpc_ability_improve',
		'label'        => __( 'Improve an ability', 'wp-connect' ),
		'category'     => 'core',
		'description'  => __( 'Submit a better version of a custom ability (new code, description or inputs). The current version keeps working until the owner approves the new one. The new version gets its own rating so you can see if it is better. Built-in abilities can\'t be rewritten; save lessons for those instead.', 'wp-connect' ),
		'locked'       => true,
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array(
				'name'          => array( 'type' => 'string' ),
				'label'         => array( 'type' => 'string' ),
				'description'   => array( 'type' => 'string' ),
				'input_schema'  => array( 'type' => 'object' ),
				'code'          => array( 'type' => 'string' ),
				'writes'        => array( 'type' => 'boolean' ),
				'risky'         => array( 'type' => 'boolean' ),
				'change_note'   => array( 'type' => 'string' ),
			),
			'required'   => array( 'name', 'change_note' ),
		),
		'callback'     => function ( $input ) {
			$result = WPC_Abilities::propose( $input, true );
			$result['review_link'] = admin_url( 'admin.php?page=wp-connect&tab=abilities#pending' );
			return $result;
		},
	)
);

/* ---------------------------------------------------------------------- */
/* Skills                                                                  */
/* ---------------------------------------------------------------------- */

WPC_Abilities::register(
	array(
		'name'        => 'wpc_skills_list',
		'label'       => __( 'List skills', 'wp-connect' ),
		'category'    => 'core',
		'description' => __( 'List the skills saved on this site. A skill is a step-by-step job (like auto-optimize) that tells you which abilities to use and in what order. When the owner asks for a whole job, check here first.', 'wp-connect' ),
		'locked'      => true,
		'callback'    => function ( $input ) {
			return array( 'skills' => WPC_Skills::list_summaries() );
		},
	)
);

WPC_Abilities::register(
	array(
		'name'         => 'wpc_skill_get',
		'label'        => __( 'Load a skill', 'wp-connect' ),
		'category'     => 'core',
		'description'  => __( 'Load a skill\'s full instructions and the owner\'s settings for it (like fix mode), then follow them step by step.', 'wp-connect' ),
		'locked'       => true,
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array( 'skill' => array( 'type' => 'string' ) ),
			'required'   => array( 'skill' ),
		),
		'callback'     => function ( $input ) {
			$skill = WPC_Skills::get( $input['skill'] );
			if ( ! $skill ) {
				throw new WPC_Ability_Error( sprintf( __( 'No skill named "%s" exists.', 'wp-connect' ), $input['skill'] ) );
			}
			return $skill;
		},
	)
);

WPC_Abilities::register(
	array(
		'name'         => 'wpc_skill_save',
		'label'        => __( 'Save a skill', 'wp-connect' ),
		'category'     => 'core',
		'description'  => __( 'Save a new skill (a reusable step-by-step job) when the owner asks you to turn a workflow into one. Write clear numbered steps that name the abilities to call. Built-in skills can\'t be overwritten. The owner can edit or delete it on WP-Connect -> Skills.', 'wp-connect' ),
		'locked'       => true,
		'writes'       => true,
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array(
				'skill'        => array( 'type' => 'string' ),
				'title'        => array( 'type' => 'string' ),
				'description'  => array( 'type' => 'string' ),
				'instructions' => array( 'type' => 'string' ),
			),
			'required'   => array( 'skill', 'title', 'description', 'instructions' ),
		),
		'callback'     => function ( $input ) {
			if ( WPC_Skills::is_builtin( $input['skill'] ) ) {
				throw new WPC_Ability_Error( sprintf( __( '"%s" is a built-in skill and can\'t be overwritten. Pick a different slug.', 'wp-connect' ), $input['skill'] ) );
			}
			WPC_Skills::save_custom( $input['skill'], $input['title'], $input['description'], $input['instructions'], 'claude' );
			return array( 'saved' => true );
		},
	)
);

WPC_Abilities::register(
	array(
		'name'         => 'wpc_report_save',
		'label'        => __( 'Save a report', 'wp-connect' ),
		'category'     => 'core',
		'description'  => __( 'Save the result of a skill run so the owner can read it on WP-Connect -> Skills. sections is a list of {title, status: good|warn|bad, items: [short lines]}.', 'wp-connect' ),
		'locked'       => true,
		'writes'       => true,
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array(
				'skill'        => array( 'type' => 'string' ),
				'summary'      => array( 'type' => 'string' ),
				'score_before' => array( 'type' => 'integer' ),
				'score_after'  => array( 'type' => 'integer' ),
				'sections'     => array( 'type' => 'array' ),
			),
			'required'   => array( 'skill', 'summary', 'sections' ),
		),
		'callback'     => function ( $input ) {
			WPC_Skills::save_report( $input );
			return array( 'saved' => true );
		},
	)
);

/**
 * Playbook text, verbatim from the product spec.
 */
function wpc_playbook_text( $topic ) {
	if ( 'site_care' === $topic ) {
		return "Site care:\n- site_health gives versions, updates and warnings. Start there.\n- plugin_install only installs from the official WordPress.org directory by slug. It installs inactive; activate as a separate step with plugin_activate, which checks the site still loads and switches the plugin off again if it doesn't.\n- plugin_update cannot be undone automatically. Tell the owner before updating.\n- seo_check and seo_set_meta work with Yoast, Rank Math, or SEOPress if one is active.\n- media_list with missing_alt finds images without alt text; media_set_alt fixes them.";
	}

	if ( 'abilities' === $topic ) {
		return "Writing a new ability (wpc_ability_create):\n- code is the BODY of a PHP function: function( array \$input ) { YOUR CODE }. No <?php tag.\n- Return an array (it becomes the result Claude sees). Throw new WPC_Ability_Error('message') when it can't do the job.\n- Before changing anything, take a backup: WPC_Backups::post( \$post_id, 'label', array( 'meta_key' ) ) for posts, WPC_Backups::option( 'option_name', 'label' ) for options. That gives the owner Undo.\n- Use WordPress functions, sanitize every input, no echo/print, no exit/die, no named functions or classes (use closures), no file writes outside uploads.\n- To check the site after a change, return '_verified' => WPC_Verify::check_url( home_url( '/' ) )['verified'].\n- Set writes=true if it changes anything, risky=true if it could break the site or change how the whole site looks.\n- input_schema is a JSON schema object describing the inputs.\n- The owner reviews the code on WP-Connect -> Abilities before it goes live. Explain in plain English what it does.\n- To fix a weak ability, use wpc_abilities_report to see its rating and last errors, then wpc_ability_improve with the new code and a change_note.";
	}

	return "How to work on this site with WP-Connect:\n1. Start with wpc_site_overview so you know the theme, builder and mode.\n2. Read the site_care playbook before changing anything.\n3. Every change is backed up and can be undone by the owner, but still work carefully: read before you write.\n4. Explain changes in plain English for a non-technical owner.\n5. After a change, look at the check result. If a check fails, fix it and run again.\n6. When something fails and you find out why, call wpc_lesson_save with a short, specific lesson for that ability. Lessons appear in the ability's description from then on, so the next run goes right first time.\n7. If the owner says a result was wrong or good, call wpc_run_feedback with the run_id. That feeds the ability's 1-100 rating.\n8. If you keep needing something no ability does, write one with wpc_ability_create (the owner approves it first). Read the 'abilities' playbook first.";
}
