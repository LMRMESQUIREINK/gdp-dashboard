<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Skills: whole jobs saved as step-by-step instructions naming which
 * abilities to use. One built-in skill (auto-optimize); the owner or
 * Claude can save more.
 */
class WPC_Skills {

	const FIX_MODES = array(
		'ask'    => 'Ask me before each change',
		'safe'   => 'Fix safe things, ask before risky ones',
		'report' => 'Report only, change nothing',
	);

	private static function builtin_skills() {
		return array(
			'auto-optimize' => array(
				'title'        => __( 'Auto-Optimize', 'wp-connect' ),
				'icon'         => 'dashicons-performance',
				'description'  => __( 'Full site audit and tune-up: finds why the site is slow and fixes it, compresses images, writes missing alt text, cleans the database, checks plugins for vulnerabilities and conflicts, and fixes broken links. Ends with a before/after report.', 'wp-connect' ),
				'default_mode' => 'safe',
				'abilities'    => array(
					'wpc_site_overview', 'speed_audit', 'image_compress', 'media_list', 'media_set_alt',
					'db_cleanup_preview', 'db_cleanup', 'plugin_security_check', 'plugin_update',
					'plugin_conflicts', 'broken_links', 'link_fix', 'wpc_report_save',
				),
				'instructions' => self::auto_optimize_instructions(),
			),
		);
	}

	private static function auto_optimize_instructions() {
		return <<<'MD'
# Auto-Optimize
Goal: make this site faster, cleaner and safer, then give the owner a clear before/after report.
Fix mode: {fix_mode}
- "ask": explain each change and wait for the owner's OK before making it.
- "safe": make the safe changes yourself (image compression, alt text, fixing internal links). Always ask first before risky ones: db_cleanup, plugin_update, installing or switching off plugins.
- "report": change nothing. Audit everything and report what you would fix.
In AI Agent mode, risky steps pause for the owner's approval automatically.
## Steps
1. **Baseline.** Call wpc_site_overview, then speed_audit. Note the speed_score and the main causes. This is your "before".
2. **Images.** From speed_audit's large_images, call image_compress in batches of 10 ids until all are done (or until 50 images, then tell the owner how many are left). Add up saved_kb.
3. **Alt text.** Call media_list with missing_alt true (limit 200). For each image, write short, specific alt text (5-12 words) from the file name, title and where it's used. Don't start with "image of". Skip purely decorative files like spacers. Save with media_set_alt, 50 at a time.
4. **Database.** Call db_cleanup_preview. If there is meaningful junk, ask the owner (it can't be undone; suggest a host backup first), then run db_cleanup. Call it again if revisions remain.
5. **Plugin security.** Call plugin_security_check. Vulnerable or removed plugins are the top priority in the report. Offer plugin_update for plugins with updates, but never update without the owner's OK. If there's no vulnerability database connected, say so once.
6. **Plugin conflicts.** Call plugin_conflicts. Report overlapping plugins (recommend which one to keep and why), plugins throwing errors, and any paused after a crash. Never switch plugins off yourself.
7. **Broken links.** Call broken_links, passing next_offset until done is true (stop after 10 batches and say how far you got). For internal links, fix with link_fix when the correct new address is obvious. Otherwise list them for the owner. Treat 403/999 from big sites as "check by hand".
8. **Caching.** If speed_audit found no caching plugin, recommend one that suits the host and offer to install it (plugin_install, then plugin_activate). Only with the owner's OK.
9. **After.** Run speed_audit again and compare with step 1.
10. **Report.** Call wpc_report_save with skill "auto-optimize", score_before and score_after, a 2-3 sentence summary, and sections for Speed, Images, Alt text, Database, Security, Conflicts, Broken links. Each section has a status (good, warn or bad) and short items saying what you found and what you did. Then tell the owner the same in plain English, top problems first.
## Rules
- Never touch plugins, the database or settings outside these steps.
- If a step fails, note it, save a lesson with wpc_lesson_save if you learned why, and carry on with the next step.
- Don't claim something was fixed unless the ability said it was.
MD;
	}

	public static function is_builtin( $slug ) {
		return isset( self::builtin_skills()[ $slug ] );
	}

	public static function all_slugs() {
		return array_merge( array_keys( self::builtin_skills() ), array_keys( (array) get_option( 'wpc_skills_custom', array() ) ) );
	}

	public static function fix_mode( $slug ) {
		$settings = (array) get_option( 'wpc_skill_settings', array() );
		if ( isset( $settings[ $slug ]['fix_mode'] ) ) {
			return $settings[ $slug ]['fix_mode'];
		}
		$builtin = self::builtin_skills();
		return isset( $builtin[ $slug ]['default_mode'] ) ? $builtin[ $slug ]['default_mode'] : 'ask';
	}

	public static function set_fix_mode( $slug, $mode ) {
		if ( ! array_key_exists( $mode, self::FIX_MODES ) ) {
			return false;
		}
		$settings           = (array) get_option( 'wpc_skill_settings', array() );
		$settings[ $slug ]  = array_merge( isset( $settings[ $slug ] ) ? $settings[ $slug ] : array(), array( 'fix_mode' => $mode ) );
		update_option( 'wpc_skill_settings', $settings, false );
		return true;
	}

	public static function raw_instructions( $slug ) {
		$overrides = (array) get_option( 'wpc_skills_overrides', array() );
		if ( isset( $overrides[ $slug ] ) ) {
			return $overrides[ $slug ];
		}

		$builtin = self::builtin_skills();
		if ( isset( $builtin[ $slug ] ) ) {
			return $builtin[ $slug ]['instructions'];
		}

		$custom = (array) get_option( 'wpc_skills_custom', array() );
		return isset( $custom[ $slug ]['instructions'] ) ? $custom[ $slug ]['instructions'] : '';
	}

	public static function meta( $slug ) {
		$builtin = self::builtin_skills();
		if ( isset( $builtin[ $slug ] ) ) {
			return array_merge( $builtin[ $slug ], array( 'slug' => $slug, 'is_builtin' => true, 'author' => 'builtin' ) );
		}
		$custom = (array) get_option( 'wpc_skills_custom', array() );
		if ( isset( $custom[ $slug ] ) ) {
			return array_merge(
				$custom[ $slug ],
				array(
					'slug'       => $slug,
					'is_builtin' => false,
					'icon'       => 'dashicons-admin-generic',
					'abilities'  => self::abilities_mentioned( $custom[ $slug ]['instructions'] ),
				)
			);
		}
		return null;
	}

	private static function abilities_mentioned( $text ) {
		$names = array_keys( WPC_Abilities::all() );
		$found = array();
		foreach ( $names as $name ) {
			if ( false !== strpos( $text, $name ) ) {
				$found[] = $name;
			}
		}
		return $found;
	}

	public static function list_summaries() {
		$out = array();
		foreach ( self::all_slugs() as $slug ) {
			$meta = self::meta( $slug );
			if ( ! $meta ) {
				continue;
			}
			$out[] = array(
				'name'        => $slug,
				'title'       => $meta['title'],
				'description' => $meta['description'],
			);
		}
		return $out;
	}

	public static function get( $slug ) {
		$meta = self::meta( $slug );
		if ( ! $meta ) {
			return null;
		}

		$fix_mode      = self::fix_mode( $slug );
		$instructions  = str_replace( '{fix_mode}', $fix_mode . ' (' . self::FIX_MODES[ $fix_mode ] . ')', self::raw_instructions( $slug ) );

		$unavailable = array();
		foreach ( (array) $meta['abilities'] as $ability_name ) {
			if ( ! WPC_Abilities::is_usable( $ability_name ) ) {
				$unavailable[] = $ability_name;
			}
		}

		return array(
			'skill'               => $slug,
			'title'               => $meta['title'],
			'fix_mode'            => $fix_mode,
			'instructions'        => $instructions,
			'unavailable_abilities' => $unavailable,
		);
	}

	public static function save_custom( $slug, $title, $description, $instructions, $author = 'owner' ) {
		$slug = sanitize_title( $slug );
		if ( self::is_builtin( $slug ) ) {
			return false;
		}
		$custom           = (array) get_option( 'wpc_skills_custom', array() );
		$custom[ $slug ]  = array(
			'title'        => sanitize_text_field( $title ),
			'description'  => sanitize_textarea_field( $description ),
			'instructions' => $instructions,
			'author'       => $author,
			'created'      => isset( $custom[ $slug ]['created'] ) ? $custom[ $slug ]['created'] : current_time( 'mysql' ),
		);
		update_option( 'wpc_skills_custom', $custom, false );
		return true;
	}

	public static function delete_custom( $slug ) {
		$custom = (array) get_option( 'wpc_skills_custom', array() );
		unset( $custom[ $slug ] );
		update_option( 'wpc_skills_custom', $custom, false );
	}

	public static function override_instructions( $slug, $instructions ) {
		$overrides          = (array) get_option( 'wpc_skills_overrides', array() );
		$overrides[ $slug ] = $instructions;
		update_option( 'wpc_skills_overrides', $overrides, false );
	}

	public static function reset_instructions( $slug ) {
		$overrides = (array) get_option( 'wpc_skills_overrides', array() );
		unset( $overrides[ $slug ] );
		update_option( 'wpc_skills_overrides', $overrides, false );
	}

	public static function is_overridden( $slug ) {
		$overrides = (array) get_option( 'wpc_skills_overrides', array() );
		return isset( $overrides[ $slug ] );
	}

	/* ------------------------------------------------------------------ */
	/* Reports                                                              */
	/* ------------------------------------------------------------------ */

	public static function save_report( $args ) {
		$sections = array_slice( (array) $args['sections'], 0, 15 );
		foreach ( $sections as &$section ) {
			$section['items'] = array_slice( (array) ( isset( $section['items'] ) ? $section['items'] : array() ), 0, 30 );
		}
		unset( $section );

		$report = array(
			'skill'        => sanitize_title( $args['skill'] ),
			'summary'      => sanitize_textarea_field( $args['summary'] ),
			'score_before' => isset( $args['score_before'] ) ? (int) $args['score_before'] : null,
			'score_after'  => isset( $args['score_after'] ) ? (int) $args['score_after'] : null,
			'sections'     => $sections,
			'created'      => current_time( 'mysql' ),
		);

		$reports   = (array) get_option( 'wpc_reports', array() );
		array_unshift( $reports, $report );
		$reports = array_slice( $reports, 0, 20 );
		update_option( 'wpc_reports', $reports, false );

		return $report;
	}

	public static function last_report( $slug ) {
		foreach ( (array) get_option( 'wpc_reports', array() ) as $report ) {
			if ( $report['skill'] === $slug ) {
				return $report;
			}
		}
		return null;
	}

	/**
	 * Average rating across a skill's abilities that have a rating,
	 * shown on the Skills tab as "skill health".
	 */
	public static function health( $slug ) {
		$meta = self::meta( $slug );
		if ( ! $meta ) {
			return null;
		}
		$scores = array();
		foreach ( (array) $meta['abilities'] as $ability_name ) {
			$rating = WPC_Abilities::rating( $ability_name );
			if ( null !== $rating['score'] ) {
				$scores[] = $rating['score'];
			}
		}
		if ( ! $scores ) {
			return null;
		}
		return (int) round( array_sum( $scores ) / count( $scores ) );
	}
}
