<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

class WPC_Ability_Error extends Exception {}

/**
 * The ability registry: definitions, execution, input validation, the
 * 1-100 rating, lessons, and Claude-written (custom) abilities.
 */
class WPC_Abilities {

	private static $registered = false;
	private static $abilities  = array();

	public static $categories = array(
		'core'        => array( 'label' => 'Core', 'icon' => 'dashicons-admin-generic' ),
		'site_care'   => array( 'label' => 'Site Care', 'icon' => 'dashicons-heart' ),
		'optimize'    => array( 'label' => 'Optimize', 'icon' => 'dashicons-performance' ),
		'full_access' => array( 'label' => 'Full Access', 'icon' => 'dashicons-unlock' ),
		'custom'      => array( 'label' => 'Custom', 'icon' => 'dashicons-superhero-alt' ),
	);

	/* ------------------------------------------------------------------ */
	/* Registration                                                         */
	/* ------------------------------------------------------------------ */

	public static function register( $args ) {
		$args = wp_parse_args(
			$args,
			array(
				'name'          => '',
				'label'         => '',
				'category'      => 'custom',
				'description'   => '',
				'input_schema'  => array( 'type' => 'object', 'properties' => array() ),
				'callback'      => null,
				'writes'        => false,
				'risky'         => false,
				'modes'         => array( 'full', 'abilities', 'agent' ),
				'agent'         => true,
				'available'     => null,
				'locked'        => false,
			)
		);
		if ( '' === $args['name'] || ! is_callable( $args['callback'] ) ) {
			return;
		}
		self::$abilities[ $args['name'] ] = $args;
	}

	public static function ensure_loaded() {
		if ( self::$registered ) {
			return;
		}
		self::$registered = true;

		require_once WPC_DIR . 'includes/abilities/core.php';
		require_once WPC_DIR . 'includes/abilities/site-care.php';
		require_once WPC_DIR . 'includes/abilities/optimize.php';
		require_once WPC_DIR . 'includes/abilities/full-access.php';

		/**
		 * Fires once the built-in ability files have loaded, so other
		 * plugins/mu-plugins can register additional abilities.
		 */
		do_action( 'wpc_register_abilities' );

		self::load_custom_abilities();
	}

	public static function all() {
		self::ensure_loaded();
		return self::$abilities;
	}

	public static function get( $name ) {
		self::ensure_loaded();
		return isset( self::$abilities[ $name ] ) ? self::$abilities[ $name ] : null;
	}

	/* ------------------------------------------------------------------ */
	/* Usability                                                            */
	/* ------------------------------------------------------------------ */

	public static function is_disabled( $name ) {
		$disabled = WPC_Plugin::instance()->get_setting( 'disabled', array() );
		return in_array( $name, (array) $disabled, true );
	}

	public static function toggle( $name, $on ) {
		$ability = self::get( $name );
		if ( ! $ability || ! empty( $ability['locked'] ) ) {
			return false;
		}
		$disabled = (array) WPC_Plugin::instance()->get_setting( 'disabled', array() );
		if ( $on ) {
			$disabled = array_values( array_diff( $disabled, array( $name ) ) );
		} elseif ( ! in_array( $name, $disabled, true ) ) {
			$disabled[] = $name;
		}
		WPC_Plugin::instance()->update_settings( array( 'disabled' => $disabled ) );
		return true;
	}

	public static function is_usable( $name, $mode = null ) {
		$ability = self::get( $name );
		if ( ! $ability ) {
			return false;
		}
		$mode = $mode ?: WPC_Plugin::instance()->mode();

		if ( ! in_array( $mode, (array) $ability['modes'], true ) ) {
			return false;
		}
		if ( empty( $ability['locked'] ) && self::is_disabled( $name ) ) {
			return false;
		}
		if ( is_callable( $ability['available'] ) && ! call_user_func( $ability['available'] ) ) {
			return false;
		}
		return true;
	}

	public static function usable_names( $mode = null, $agent_only = false ) {
		$mode = $mode ?: WPC_Plugin::instance()->mode();
		$out  = array();
		foreach ( self::all() as $name => $ability ) {
			if ( 'run_php' === $name && $agent_only ) {
				continue; // run_php is never offered to the AI Agent loop.
			}
			if ( $agent_only && empty( $ability['agent'] ) ) {
				continue;
			}
			if ( self::is_usable( $name, $mode ) ) {
				$out[] = $name;
			}
		}
		return $out;
	}

	/* ------------------------------------------------------------------ */
	/* Execution                                                            */
	/* ------------------------------------------------------------------ */

	/**
	 * Run an ability by name with $input, logging a run row, taking
	 * backups through WPC_Backups, and returning a plain result array.
	 *
	 * @return array{success:bool, result:mixed, error:string, run_id:int, undo:bool}
	 */
	public static function run( $name, $input, $source = 'chat', $user_id = 0, $task_id = null ) {
		global $wpdb;

		$ability = self::get( $name );
		if ( ! $ability ) {
			return array(
				'success' => false,
				'result'  => null,
				'error'   => sprintf( __( 'Unknown ability "%s".', 'wp-connect' ), $name ),
				'run_id'  => 0,
				'undo'    => false,
			);
		}

		$version = 1;
		if ( 'custom' === $ability['category'] && isset( $ability['_version'] ) ) {
			$version = (int) $ability['_version'];
		}

		$runs_table = WPC_Plugin::instance()->table( 'runs' );
		$wpdb->insert(
			$runs_table,
			array(
				'ability'         => $name,
				'ability_version' => $version,
				'source'          => $source,
				'user_id'         => $user_id ?: get_current_user_id(),
				'task_id'         => $task_id,
				'input'           => wp_json_encode( $input ),
				'success'         => 0,
				'created'         => current_time( 'mysql', true ),
			),
			array( '%s', '%d', '%s', '%d', '%d', '%s', '%d', '%s' )
		);
		$run_id            = (int) $wpdb->insert_id;
		WPC_Backups::$run_id = $run_id;

		$start = microtime( true );

		try {
			$clean   = self::validate_input( $ability['input_schema'], $input );
			$result  = call_user_func( $ability['callback'], $clean );
			$verified = null;
			if ( is_array( $result ) && array_key_exists( '_verified', $result ) ) {
				$verified = $result['_verified'];
				unset( $result['_verified'] );
			}
			$success = ( false !== $verified );
			$error   = $success ? '' : __( 'Saved, but the check afterwards failed.', 'wp-connect' );
		} catch ( WPC_Ability_Error $e ) {
			$result   = null;
			$verified = null;
			$success  = false;
			$error    = $e->getMessage();
		} catch ( Throwable $e ) {
			$result   = null;
			$verified = null;
			$success  = false;
			$error    = sprintf( 'PHP error: %s (%s:%d)', $e->getMessage(), basename( $e->getFile() ), $e->getLine() );
		}

		$duration_ms = (int) round( ( microtime( true ) - $start ) * 1000 );

		$output_json = wp_json_encode( $result );
		if ( is_string( $output_json ) && strlen( $output_json ) > 20000 ) {
			$output_json = substr( $output_json, 0, 20000 );
		}

		$wpdb->update(
			$runs_table,
			array(
				'output'      => $output_json,
				'success'     => $success ? 1 : 0,
				'verified'    => null === $verified ? null : ( $verified ? 1 : 0 ),
				'error'       => $error,
				'duration_ms' => $duration_ms,
			),
			array( 'id' => $run_id ),
			array( '%s', '%d', '%d', '%s', '%d' ),
			array( '%d' )
		);

		$has_undo = (bool) $wpdb->get_var(
			$wpdb->prepare( 'SELECT COUNT(*) FROM ' . WPC_Plugin::instance()->table( 'backups' ) . ' WHERE run_id = %d', $run_id ) // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
		);

		return array(
			'success' => $success,
			'result'  => $result,
			'error'   => $error,
			'run_id'  => $run_id,
			'undo'    => $has_undo && ! empty( $ability['writes'] ),
		);
	}

	/* ------------------------------------------------------------------ */
	/* Validation                                                           */
	/* ------------------------------------------------------------------ */

	public static function validate_input( $schema, $input ) {
		$input = is_array( $input ) ? $input : array();
		$props = isset( $schema['properties'] ) ? $schema['properties'] : array();
		$req   = isset( $schema['required'] ) ? $schema['required'] : array();

		foreach ( $req as $field ) {
			if ( ! array_key_exists( $field, $input ) || '' === $input[ $field ] ) {
				throw new WPC_Ability_Error( sprintf( __( 'Invalid input: "%s" is required.', 'wp-connect' ), $field ) );
			}
		}

		$clean = array();
		foreach ( $props as $field => $spec ) {
			if ( ! array_key_exists( $field, $input ) ) {
				continue;
			}
			$clean[ $field ] = self::coerce_and_check( $field, $input[ $field ], $spec );
		}

		foreach ( $input as $field => $value ) {
			if ( ! array_key_exists( $field, $clean ) && ! isset( $props[ $field ] ) ) {
				$clean[ $field ] = $value; // Unspecified fields pass through unchanged.
			}
		}

		return $clean;
	}

	private static function coerce_and_check( $field, $value, $spec ) {
		$type = isset( $spec['type'] ) ? $spec['type'] : null;

		if ( 'integer' === $type && is_string( $value ) && ctype_digit( ltrim( $value, '-' ) ) ) {
			$value = (int) $value;
		}
		if ( 'boolean' === $type && is_string( $value ) ) {
			$lower = strtolower( $value );
			if ( in_array( $lower, array( 'true', '1', 'yes' ), true ) ) {
				$value = true;
			} elseif ( in_array( $lower, array( 'false', '0', 'no' ), true ) ) {
				$value = false;
			}
		}
		if ( in_array( $type, array( 'array', 'object' ), true ) && is_string( $value ) ) {
			$decoded = json_decode( $value, true );
			if ( null !== $decoded || 'null' === trim( $value ) ) {
				$value = $decoded;
			}
		}

		if ( $type && ! self::matches_type( $value, $type ) ) {
			throw new WPC_Ability_Error( sprintf( __( 'Invalid input: "%1$s" must be a %2$s.', 'wp-connect' ), $field, $type ) );
		}

		if ( isset( $spec['enum'] ) && ! in_array( $value, $spec['enum'], true ) ) {
			throw new WPC_Ability_Error(
				sprintf(
					__( 'Invalid input: "%1$s" must be one of: %2$s.', 'wp-connect' ),
					$field,
					implode( ', ', $spec['enum'] )
				)
			);
		}

		return $value;
	}

	private static function matches_type( $value, $type ) {
		switch ( $type ) {
			case 'string':
				return is_string( $value );
			case 'integer':
				return is_int( $value );
			case 'number':
				return is_int( $value ) || is_float( $value );
			case 'boolean':
				return is_bool( $value );
			case 'array':
				return is_array( $value ) && ( empty( $value ) || array_is_list( $value ) );
			case 'object':
				return is_array( $value );
			default:
				return true;
		}
	}

	/* ------------------------------------------------------------------ */
	/* Rating                                                               */
	/* ------------------------------------------------------------------ */

	/**
	 * @return array{score:int|null, label:string, runs:int, success_rate:float, last_error:string}
	 */
	public static function rating( $name ) {
		global $wpdb;
		$runs_table = WPC_Plugin::instance()->table( 'runs' );
		$ability    = self::get( $name );

		$where = $wpdb->prepare( 'ability = %s', $name );
		if ( $ability && 'custom' === $ability['category'] && isset( $ability['_version'] ) ) {
			$where .= $wpdb->prepare( ' AND ability_version = %d', (int) $ability['_version'] );
		}

		$rows = $wpdb->get_results( "SELECT success, verified, feedback, error, created FROM {$runs_table} WHERE {$where} ORDER BY id DESC LIMIT 50" ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared

		$n = count( $rows );
		if ( 0 === $n ) {
			return array(
				'score'        => null,
				'label'        => __( 'New', 'wp-connect' ),
				'runs'         => 0,
				'success_rate' => 0,
				'last_error'   => '',
			);
		}

		$success_n  = 0;
		$verified_n = 0;
		$verified_d = 0;
		$up         = 0;
		$down       = 0;
		$last_error = '';

		foreach ( $rows as $row ) {
			if ( $row->success ) {
				++$success_n;
			}
			if ( null !== $row->verified ) {
				++$verified_d;
				if ( $row->verified ) {
					++$verified_n;
				}
			}
			if ( 1 === (int) $row->feedback ) {
				++$up;
			} elseif ( -1 === (int) $row->feedback ) {
				++$down;
			}
			if ( '' === $last_error && ! empty( $row->error ) ) {
				$last_error = $row->error;
			}
		}

		$success_rate = $success_n / $n;
		$verified_rate = $verified_d > 0 ? ( $verified_n / $verified_d ) : $success_rate;
		$feedback_rate = ( $up + $down ) > 0 ? ( $up / ( $up + $down ) ) : $success_rate;

		$raw      = 0.60 * $success_rate + 0.25 * $verified_rate + 0.15 * $feedback_rate;
		$smoothed = ( $raw * $n + 0.75 * 3 ) / ( $n + 3 );
		$score    = (int) round( min( 1, max( 0, $smoothed ) ) * 100 );
		$score    = max( 1, min( 100, $score ) );

		return array(
			'score'        => $score,
			'label'        => self::rating_label( $score ),
			'runs'         => $n,
			'success_rate' => round( $success_rate * 100, 1 ),
			'last_error'   => 60 > $score ? $last_error : '',
		);
	}

	public static function rating_label( $score ) {
		if ( $score >= 90 ) {
			return __( 'Excellent', 'wp-connect' );
		}
		if ( $score >= 75 ) {
			return __( 'Good', 'wp-connect' );
		}
		if ( $score >= 50 ) {
			return __( 'Needs work', 'wp-connect' );
		}
		return __( 'Poor', 'wp-connect' );
	}

	public static function record_feedback( $run_id, $good, $note = '' ) {
		global $wpdb;
		$runs_table = WPC_Plugin::instance()->table( 'runs' );
		$run        = $wpdb->get_row( $wpdb->prepare( "SELECT * FROM {$runs_table} WHERE id = %d", $run_id ) ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
		if ( ! $run ) {
			return null;
		}

		$wpdb->update(
			$runs_table,
			array( 'feedback' => $good ? 1 : -1 ),
			array( 'id' => $run_id ),
			array( '%d' ),
			array( '%d' )
		);

		if ( ! $good && '' !== trim( $note ) ) {
			self::save_lesson( $run->ability, $note, 'owner' );
		}

		return self::rating( $run->ability );
	}

	/* ------------------------------------------------------------------ */
	/* Lessons                                                              */
	/* ------------------------------------------------------------------ */

	public static function save_lesson( $topic, $lesson, $source = 'claude' ) {
		global $wpdb;
		$lesson = trim( wp_strip_all_tags( $lesson ) );
		if ( '' === $lesson ) {
			return false;
		}
		$lesson = mb_substr( $lesson, 0, 300 );

		$table    = WPC_Plugin::instance()->table( 'lessons' );
		$existing = $wpdb->get_var(
			$wpdb->prepare( "SELECT id FROM {$table} WHERE topic = %s AND lesson = %s", $topic, $lesson ) // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
		);
		if ( $existing ) {
			return (int) $existing;
		}

		$wpdb->insert(
			$table,
			array(
				'topic'   => $topic,
				'lesson'  => $lesson,
				'source'  => $source,
				'created' => current_time( 'mysql', true ),
			),
			array( '%s', '%s', '%s', '%s' )
		);

		$ids = $wpdb->get_col(
			$wpdb->prepare( "SELECT id FROM {$table} WHERE topic = %s ORDER BY id DESC", $topic ) // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
		);
		if ( count( $ids ) > 50 ) {
			$to_delete = array_slice( $ids, 50 );
			$wpdb->query( "DELETE FROM {$table} WHERE id IN (" . implode( ',', array_map( 'intval', $to_delete ) ) . ')' ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared,WordPress.DB.PreparedSQLPlaceholders.UnfinishedPrepare
		}

		return (int) $wpdb->insert_id;
	}

	public static function lessons( $topic, $limit = 0 ) {
		global $wpdb;
		$table = WPC_Plugin::instance()->table( 'lessons' );
		$sql   = $wpdb->prepare( "SELECT * FROM {$table} WHERE topic = %s ORDER BY id DESC", $topic ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
		if ( $limit > 0 ) {
			$sql .= $wpdb->prepare( ' LIMIT %d', $limit );
		}
		return $wpdb->get_results( $sql ); // phpcs:ignore WordPress.DB.PreparedSQL.NotPrepared
	}

	public static function delete_lesson( $id ) {
		global $wpdb;
		return (bool) $wpdb->delete( WPC_Plugin::instance()->table( 'lessons' ), array( 'id' => $id ), array( '%d' ) );
	}

	public static function update_lesson( $id, $text ) {
		global $wpdb;
		$text = trim( wp_strip_all_tags( $text ) );
		if ( '' === $text ) {
			return self::delete_lesson( $id );
		}
		return (bool) $wpdb->update(
			WPC_Plugin::instance()->table( 'lessons' ),
			array( 'lesson' => mb_substr( $text, 0, 300 ) ),
			array( 'id' => $id ),
			array( '%s' ),
			array( '%d' )
		);
	}

	/* ------------------------------------------------------------------ */
	/* Fine-tuning                                                          */
	/* ------------------------------------------------------------------ */

	public static function tuning( $name ) {
		$tuning = (array) WPC_Plugin::instance()->get_setting( 'tuning', array() );
		return isset( $tuning[ $name ] ) ? $tuning[ $name ] : array( 'notes' => '', 'needs_approval' => null );
	}

	public static function save_tuning( $name, $notes, $needs_approval ) {
		$tuning          = (array) WPC_Plugin::instance()->get_setting( 'tuning', array() );
		$tuning[ $name ] = array(
			'notes'          => sanitize_textarea_field( $notes ),
			'needs_approval' => $needs_approval,
		);
		WPC_Plugin::instance()->update_settings( array( 'tuning' => $tuning ) );
	}

	public static function needs_approval( $name ) {
		$tuning  = self::tuning( $name );
		$ability = self::get( $name );
		if ( null !== $tuning['needs_approval'] ) {
			return (bool) $tuning['needs_approval'];
		}
		return $ability ? ! empty( $ability['risky'] ) : true;
	}

	/* ------------------------------------------------------------------ */
	/* Tool description (what Claude actually reads)                       */
	/* ------------------------------------------------------------------ */

	public static function build_description( $name ) {
		$ability = self::get( $name );
		if ( ! $ability ) {
			return '';
		}

		$text = $ability['description'];

		$tuning = self::tuning( $name );
		if ( '' !== trim( (string) $tuning['notes'] ) ) {
			$text .= "\n\nOwner's instructions: " . $tuning['notes'];
		}

		$lessons = self::lessons( $name, 6 );
		if ( $lessons ) {
			$text .= "\n\nLessons learned on this site:";
			foreach ( $lessons as $lesson ) {
				$text .= "\n- " . $lesson->lesson;
			}
		}

		$rating = self::rating( $name );
		if ( null !== $rating['score'] ) {
			$text .= sprintf( "\n\nCurrent rating: %d/100 over %d runs.", $rating['score'], $rating['runs'] );
			if ( $rating['score'] < 60 && '' !== $rating['last_error'] ) {
				$text .= ' Last failure: ' . $rating['last_error'];
			}
		}

		if ( ! empty( $ability['writes'] ) ) {
			$text .= "\n\nThis changes the site. A backup is taken first and the owner can undo it.";
		}

		return $text;
	}

	public static function tool_definition( $name ) {
		$ability = self::get( $name );
		if ( ! $ability ) {
			return null;
		}
		$schema = $ability['input_schema'];
		if ( empty( $schema['properties'] ) ) {
			$schema['properties'] = new stdClass();
		}
		return array(
			'name'        => $name,
			'title'       => $ability['label'],
			'description' => self::build_description( $name ),
			'inputSchema' => $schema,
			'annotations' => array(
				'title'            => $ability['label'],
				'readOnlyHint'     => empty( $ability['writes'] ),
				'destructiveHint'  => ! empty( $ability['risky'] ),
			),
		);
	}

	/* ------------------------------------------------------------------ */
	/* Claude-written abilities                                            */
	/* ------------------------------------------------------------------ */

	private static function normalize_name( $name ) {
		$name = strtolower( trim( (string) $name ) );
		$name = str_replace( '-', '_', $name );
		return $name;
	}

	private static function valid_name( $name ) {
		return (bool) preg_match( '/^[a-z][a-z0-9_]{2,60}$/', $name );
	}

	public static function load_custom_abilities() {
		global $wpdb;
		$table = WPC_Plugin::instance()->table( 'custom' );
		$rows  = $wpdb->get_results( "SELECT * FROM {$table} WHERE status = 'active' ORDER BY name, version DESC" ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared

		$seen = array();
		foreach ( (array) $rows as $row ) {
			if ( isset( $seen[ $row->name ] ) ) {
				continue; // Keep only the newest active version per name.
			}
			$seen[ $row->name ] = true;

			// Never shadow a built-in ability, but do allow refreshing an
			// already-loaded custom one (approve/restore can run again in
			// the same process via the unset()s below).
			if ( isset( self::$abilities[ $row->name ] ) && 'custom' !== self::$abilities[ $row->name ]['category'] ) {
				continue;
			}

			self::$abilities[ $row->name ] = array(
				'name'         => $row->name,
				'label'        => $row->label,
				'category'     => 'custom',
				'description'  => $row->description,
				'input_schema' => json_decode( $row->input_schema, true ) ?: array( 'type' => 'object', 'properties' => array() ),
				'callback'     => self::custom_callback( $row ),
				'writes'       => (bool) $row->writes,
				'risky'        => (bool) $row->risky,
				'modes'        => array( 'full', 'abilities', 'agent' ),
				'agent'        => true,
				'available'    => null,
				'locked'       => false,
				'_version'     => (int) $row->version,
				'_code_hash'   => $row->code_hash,
			);
		}
	}

	private static function custom_callback( $row ) {
		return function ( $input ) use ( $row ) {
			if ( hash( 'sha256', $row->code ) !== $row->code_hash ) {
				throw new WPC_Ability_Error(
					__( "This ability's code changed after it was approved, so it was blocked. Ask the owner to review it again.", 'wp-connect' )
				);
			}
			$fn = self::eval_ability_code( $row->code );
			return $fn( $input );
		};
	}

	/**
	 * Lint without running: wraps the body in `return null; return function...`
	 * so a parse error surfaces as a ParseError without the body ever
	 * executing, then (for real execution) evaluates the real closure.
	 */
	private static function eval_ability_code( $code ) {
		if ( 0 === strpos( ltrim( $code ), '<?php' ) ) {
			throw new WPC_Ability_Error( __( 'Code must not include an opening <?php tag.', 'wp-connect' ) );
		}
		// phpcs:ignore Squiz.PHP.Eval.Discouraged
		return eval( 'return function( array $input ) { ' . $code . ' };' );
	}

	public static function lint_code( $code ) {
		if ( 0 === strpos( ltrim( $code ), '<?php' ) ) {
			return __( 'Code must not include an opening <?php tag.', 'wp-connect' );
		}
		try {
			// phpcs:ignore Squiz.PHP.Eval.Discouraged
			eval( 'return null; return function( array $input ) { ' . $code . ' };' );
			return '';
		} catch ( ParseError $e ) {
			return sprintf( __( 'Syntax error on line %1$d: %2$s', 'wp-connect' ), $e->getLine(), $e->getMessage() );
		}
	}

	public static function propose( $args, $existing_required = false ) {
		$name = self::normalize_name( $args['name'] );
		if ( ! self::valid_name( $name ) ) {
			throw new WPC_Ability_Error( __( 'The ability name must be lowercase letters, numbers and underscores, starting with a letter, 3-61 characters.', 'wp-connect' ) );
		}
		if ( self::is_builtin_name( $name ) ) {
			throw new WPC_Ability_Error( sprintf( __( '"%s" is a built-in ability name. Use wpc_ability_improve on a custom ability instead, or pick a different name.', 'wp-connect' ), $name ) );
		}

		$latest = self::latest_custom_row( $name );
		if ( $existing_required && ! $latest ) {
			throw new WPC_Ability_Error( sprintf( __( 'No custom ability named "%s" exists yet. Use wpc_ability_create to make a new one.', 'wp-connect' ), $name ) );
		}
		if ( ! $existing_required && $latest ) {
			throw new WPC_Ability_Error( sprintf( __( 'A custom ability named "%s" already exists. Use wpc_ability_improve to submit a new version.', 'wp-connect' ), $name ) );
		}

		$label       = ! empty( $args['label'] ) ? $args['label'] : ( $latest ? $latest->label : $name );
		$description = ! empty( $args['description'] ) ? $args['description'] : ( $latest ? $latest->description : '' );
		$code        = ! empty( $args['code'] ) ? $args['code'] : ( $latest ? $latest->code : '' );
		$schema      = ! empty( $args['input_schema'] ) ? $args['input_schema'] : ( $latest ? json_decode( $latest->input_schema, true ) : array( 'type' => 'object', 'properties' => array() ) );
		$writes      = array_key_exists( 'writes', $args ) ? (bool) $args['writes'] : ( $latest ? (bool) $latest->writes : false );
		$risky       = array_key_exists( 'risky', $args ) ? (bool) $args['risky'] : ( $latest ? (bool) $latest->risky : false );

		if ( '' === trim( (string) $code ) ) {
			throw new WPC_Ability_Error( __( 'code is required.', 'wp-connect' ) );
		}

		$lint_error = self::lint_code( $code );
		if ( '' !== $lint_error ) {
			throw new WPC_Ability_Error( $lint_error );
		}

		global $wpdb;
		$table         = WPC_Plugin::instance()->table( 'custom' );
		$next_version  = $latest ? ( (int) $latest->version + 1 ) : 1;

		// Supersede any older pending rows for this name.
		$wpdb->update( $table, array( 'status' => 'superseded' ), array( 'name' => $name, 'status' => 'pending' ), array( '%s' ), array( '%s', '%s' ) );

		$wpdb->insert(
			$table,
			array(
				'name'         => $name,
				'version'      => $next_version,
				'label'        => sanitize_text_field( $label ),
				'description'  => sanitize_textarea_field( $description ),
				'category'     => 'custom',
				'input_schema' => wp_json_encode( $schema ),
				'code'         => $code,
				'code_hash'    => hash( 'sha256', $code ),
				'writes'       => $writes ? 1 : 0,
				'risky'        => $risky ? 1 : 0,
				'status'       => 'pending',
				'change_note'  => isset( $args['change_note'] ) ? sanitize_textarea_field( $args['change_note'] ) : '',
				'created'      => current_time( 'mysql', true ),
			),
			array( '%s', '%d', '%s', '%s', '%s', '%s', '%s', '%s', '%d', '%d', '%s', '%s', '%s' )
		);

		return array(
			'status'  => 'pending_approval',
			'id'      => (int) $wpdb->insert_id,
			'message' => __( 'Saved as pending. The owner needs to review and approve it on WP-Connect → Abilities before it goes live.', 'wp-connect' ),
		);
	}

	public static function is_builtin_name( $name ) {
		self::ensure_loaded();
		foreach ( self::$abilities as $ability_name => $ability ) {
			if ( $ability_name === $name && 'custom' !== $ability['category'] ) {
				return true;
			}
		}
		return false;
	}

	private static function latest_custom_row( $name ) {
		global $wpdb;
		$table = WPC_Plugin::instance()->table( 'custom' );
		return $wpdb->get_row(
			$wpdb->prepare( "SELECT * FROM {$table} WHERE name = %s ORDER BY version DESC LIMIT 1", $name ) // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
		);
	}

	public static function custom_row( $id ) {
		global $wpdb;
		$table = WPC_Plugin::instance()->table( 'custom' );
		return $wpdb->get_row( $wpdb->prepare( "SELECT * FROM {$table} WHERE id = %d", $id ) ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
	}

	public static function custom_versions( $name ) {
		global $wpdb;
		$table = WPC_Plugin::instance()->table( 'custom' );
		return $wpdb->get_results(
			$wpdb->prepare( "SELECT * FROM {$table} WHERE name = %s ORDER BY version DESC", $name ) // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
		);
	}

	public static function pending_count() {
		global $wpdb;
		$table = WPC_Plugin::instance()->table( 'custom' );
		return (int) $wpdb->get_var( "SELECT COUNT(*) FROM {$table} WHERE status = 'pending'" ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
	}

	public static function pending_rows() {
		global $wpdb;
		$table = WPC_Plugin::instance()->table( 'custom' );
		return $wpdb->get_results( "SELECT * FROM {$table} WHERE status = 'pending' ORDER BY created DESC" ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
	}

	public static function approve( $id ) {
		global $wpdb;
		$table = WPC_Plugin::instance()->table( 'custom' );
		$row   = self::custom_row( $id );
		if ( ! $row || 'pending' !== $row->status ) {
			return false;
		}

		$wpdb->update( $table, array( 'status' => 'retired' ), array( 'name' => $row->name, 'status' => 'active' ), array( '%s' ), array( '%s', '%s' ) );
		$wpdb->update(
			$table,
			array( 'status' => 'active', 'code_hash' => hash( 'sha256', $row->code ), 'approved' => current_time( 'mysql', true ) ),
			array( 'id' => $id ),
			array( '%s', '%s', '%s' ),
			array( '%d' )
		);
		unset( self::$abilities[ $row->name ] );
		self::load_custom_abilities();
		return true;
	}

	public static function reject( $id ) {
		global $wpdb;
		return (bool) $wpdb->update(
			WPC_Plugin::instance()->table( 'custom' ),
			array( 'status' => 'rejected' ),
			array( 'id' => $id, 'status' => 'pending' ),
			array( '%s' ),
			array( '%d', '%s' )
		);
	}

	public static function restore_version( $id ) {
		global $wpdb;
		$table = WPC_Plugin::instance()->table( 'custom' );
		$row   = self::custom_row( $id );
		if ( ! $row ) {
			return false;
		}
		$wpdb->update( $table, array( 'status' => 'retired' ), array( 'name' => $row->name, 'status' => 'active' ), array( '%s' ), array( '%s', '%s' ) );
		$wpdb->update(
			$table,
			array( 'status' => 'active', 'code_hash' => hash( 'sha256', $row->code ), 'approved' => current_time( 'mysql', true ) ),
			array( 'id' => $id ),
			array( '%s', '%s', '%s' ),
			array( '%d' )
		);
		unset( self::$abilities[ $row->name ] );
		self::load_custom_abilities();
		return true;
	}

	public static function delete_custom( $name ) {
		global $wpdb;
		$deleted = (bool) $wpdb->delete( WPC_Plugin::instance()->table( 'custom' ), array( 'name' => $name ), array( '%s' ) );
		unset( self::$abilities[ $name ] );
		return $deleted;
	}

	public static function reset_rating( $name ) {
		global $wpdb;
		$table   = WPC_Plugin::instance()->table( 'runs' );
		$ability = self::get( $name );
		$where   = array( 'ability' => $name );
		$formats = array( '%s' );
		if ( $ability && 'custom' === $ability['category'] && isset( $ability['_version'] ) ) {
			$where['ability_version'] = (int) $ability['_version'];
			$formats[]                = '%d';
		}
		return (int) $wpdb->delete( $table, $where, $formats );
	}
}
