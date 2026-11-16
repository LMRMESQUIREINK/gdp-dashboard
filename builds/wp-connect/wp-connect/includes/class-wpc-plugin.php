<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Settings, the encrypted API key, database tables, and the daily cleanup
 * cron. Everything else (abilities, OAuth, MCP, the agent, the admin UI)
 * reads its configuration through this class rather than touching options
 * or $wpdb directly.
 */
class WPC_Plugin {

	private static $instance = null;

	private $settings = null;

	public static function instance() {
		if ( null === self::$instance ) {
			self::$instance = new self();
		}
		return self::$instance;
	}

	private function __construct() {}

	public function boot() {
		$this->maybe_upgrade_db();
		add_action( 'wpc_daily_cleanup', array( $this, 'daily_cleanup' ) );
		add_action( 'init', array( $this, 'load_textdomain' ) );
	}

	public function load_textdomain() {
		load_plugin_textdomain( 'wp-connect', false, dirname( plugin_basename( WPC_FILE ) ) . '/languages' );
	}

	/* ------------------------------------------------------------------ */
	/* Settings                                                            */
	/* ------------------------------------------------------------------ */

	public function default_settings() {
		return array(
			'mode'                => 'abilities',
			'allow_publish'       => false,
			'api_key'             => '',
			'wpscan_token'        => '',
			'model'               => 'claude-sonnet-5-5',
			'agent_max_steps'     => 25,
			'email_on_done'       => true,
			'disabled'            => array(),
			'tuning'              => array(),
			'delete_on_uninstall' => false,
		);
	}

	public function settings() {
		if ( null === $this->settings ) {
			$stored         = get_option( 'wpc_settings', array() );
			$this->settings = wp_parse_args( is_array( $stored ) ? $stored : array(), $this->default_settings() );
		}
		return $this->settings;
	}

	public function get_setting( $key, $default = null ) {
		$settings = $this->settings();
		return array_key_exists( $key, $settings ) ? $settings[ $key ] : $default;
	}

	/**
	 * Merge $changes into the stored settings and persist (not autoloaded).
	 */
	public function update_settings( $changes ) {
		$settings            = array_merge( $this->settings(), $changes );
		$this->settings      = $settings;
		update_option( 'wpc_settings', $settings, false );
		return $settings;
	}

	/**
	 * Mode falls back to 'abilities' if 'agent' is selected but no API key
	 * has been saved, so a site never silently runs with no model behind it.
	 */
	public function mode() {
		$mode = $this->get_setting( 'mode', 'abilities' );
		if ( 'agent' === $mode && '' === $this->api_key() ) {
			return 'abilities';
		}
		return $mode;
	}

	public function mode_label( $mode = null ) {
		$mode   = $mode ?: $this->mode();
		$labels = array(
			'full'      => __( 'Full Access', 'wp-connect' ),
			'abilities' => __( 'Abilities', 'wp-connect' ),
			'agent'     => __( 'AI Agent', 'wp-connect' ),
		);
		return isset( $labels[ $mode ] ) ? $labels[ $mode ] : $mode;
	}

	/* ------------------------------------------------------------------ */
	/* Encrypted API key                                                   */
	/* ------------------------------------------------------------------ */

	private function encryption_key() {
		return hash( 'sha256', wp_salt( 'auth' ) . 'wp-connect', true );
	}

	public function set_api_key( $raw_key ) {
		$raw_key = trim( (string) $raw_key );
		if ( '' === $raw_key ) {
			$this->update_settings( array( 'api_key' => '' ) );
			return;
		}
		$this->update_settings( array( 'api_key' => $this->encrypt( $raw_key ) ) );
	}

	public function api_key() {
		$stored = $this->get_setting( 'api_key', '' );
		if ( '' === $stored ) {
			return '';
		}
		return $this->decrypt( $stored );
	}

	public function api_key_hint() {
		$key = $this->api_key();
		if ( '' === $key ) {
			return '';
		}
		$len = strlen( $key );
		if ( $len <= 8 ) {
			return str_repeat( '•', max( 0, $len - 2 ) ) . substr( $key, -2 );
		}
		return substr( $key, 0, 3 ) . str_repeat( '•', 4 ) . substr( $key, -4 );
	}

	private function encrypt( $value ) {
		if ( function_exists( 'openssl_encrypt' ) ) {
			$iv  = openssl_random_pseudo_bytes( 16 );
			$enc = openssl_encrypt( $value, 'aes-256-cbc', $this->encryption_key(), OPENSSL_RAW_DATA, $iv );
			if ( false !== $enc ) {
				return 'enc:' . base64_encode( $iv . $enc );
			}
		}
		return 'raw:' . base64_encode( $value );
	}

	private function decrypt( $stored ) {
		if ( 0 === strpos( $stored, 'enc:' ) && function_exists( 'openssl_decrypt' ) ) {
			$raw = base64_decode( substr( $stored, 4 ) );
			if ( false === $raw || strlen( $raw ) < 16 ) {
				return '';
			}
			$iv  = substr( $raw, 0, 16 );
			$enc = substr( $raw, 16 );
			$dec = openssl_decrypt( $enc, 'aes-256-cbc', $this->encryption_key(), OPENSSL_RAW_DATA, $iv );
			return false === $dec ? '' : $dec;
		}
		if ( 0 === strpos( $stored, 'raw:' ) ) {
			return (string) base64_decode( substr( $stored, 4 ) );
		}
		return '';
	}

	/* ------------------------------------------------------------------ */
	/* Database                                                             */
	/* ------------------------------------------------------------------ */

	public function install() {
		$this->create_tables();
		update_option( 'wpc_db_version', WPC_DB_VERSION, true );
		if ( false === get_option( 'wpc_settings', false ) ) {
			update_option( 'wpc_settings', $this->default_settings(), false );
		}
	}

	public function maybe_upgrade_db() {
		if ( get_option( 'wpc_db_version' ) !== WPC_DB_VERSION ) {
			$this->create_tables();
			update_option( 'wpc_db_version', WPC_DB_VERSION, true );
		}
	}

	private function create_tables() {
		global $wpdb;
		require_once ABSPATH . 'wp-admin/includes/upgrade.php';

		$charset_collate = $wpdb->get_charset_collate();
		$p               = $wpdb->prefix;

		$sql = array();

		$sql[] = "CREATE TABLE {$p}wpc_runs (
			id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
			ability VARCHAR(80) NOT NULL,
			ability_version INT NOT NULL DEFAULT 1,
			source VARCHAR(20) NOT NULL DEFAULT 'chat',
			user_id BIGINT UNSIGNED NOT NULL DEFAULT 0,
			task_id BIGINT UNSIGNED NULL,
			input LONGTEXT NULL,
			output LONGTEXT NULL,
			success TINYINT NOT NULL DEFAULT 0,
			verified TINYINT NULL,
			error TEXT NULL,
			duration_ms INT NOT NULL DEFAULT 0,
			feedback TINYINT NULL,
			created DATETIME NOT NULL,
			PRIMARY KEY  (id),
			KEY ability (ability),
			KEY created (created)
		) {$charset_collate};";

		$sql[] = "CREATE TABLE {$p}wpc_backups (
			id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
			run_id BIGINT UNSIGNED NOT NULL DEFAULT 0,
			type VARCHAR(40) NOT NULL,
			target VARCHAR(191) NOT NULL DEFAULT '',
			label VARCHAR(255) NOT NULL DEFAULT '',
			data LONGTEXT NULL,
			undone TINYINT NOT NULL DEFAULT 0,
			created DATETIME NOT NULL,
			PRIMARY KEY  (id),
			KEY run_id (run_id)
		) {$charset_collate};";

		$sql[] = "CREATE TABLE {$p}wpc_tokens (
			id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
			token_hash CHAR(64) NOT NULL,
			type VARCHAR(20) NOT NULL,
			client_id VARCHAR(80) NOT NULL DEFAULT '',
			user_id BIGINT UNSIGNED NOT NULL DEFAULT 0,
			expires DATETIME NOT NULL,
			last_used DATETIME NULL,
			created DATETIME NOT NULL,
			PRIMARY KEY  (id),
			KEY token_hash (token_hash)
		) {$charset_collate};";

		$sql[] = "CREATE TABLE {$p}wpc_custom (
			id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
			name VARCHAR(80) NOT NULL,
			version INT NOT NULL DEFAULT 1,
			label VARCHAR(255) NOT NULL DEFAULT '',
			description TEXT NULL,
			category VARCHAR(40) NOT NULL DEFAULT 'custom',
			input_schema LONGTEXT NULL,
			code LONGTEXT NULL,
			code_hash CHAR(64) NOT NULL DEFAULT '',
			writes TINYINT NOT NULL DEFAULT 0,
			risky TINYINT NOT NULL DEFAULT 0,
			status VARCHAR(20) NOT NULL DEFAULT 'pending',
			change_note TEXT NULL,
			created DATETIME NOT NULL,
			approved DATETIME NULL,
			PRIMARY KEY  (id),
			KEY name (name)
		) {$charset_collate};";

		$sql[] = "CREATE TABLE {$p}wpc_tasks (
			id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
			prompt LONGTEXT NULL,
			user_id BIGINT UNSIGNED NOT NULL DEFAULT 0,
			status VARCHAR(20) NOT NULL DEFAULT 'queued',
			recurrence VARCHAR(10) NOT NULL DEFAULT 'once',
			run_at DATETIME NULL,
			messages LONGTEXT NULL,
			pending LONGTEXT NULL,
			log LONGTEXT NULL,
			result LONGTEXT NULL,
			steps INT NOT NULL DEFAULT 0,
			created DATETIME NOT NULL,
			updated DATETIME NOT NULL,
			PRIMARY KEY  (id)
		) {$charset_collate};";

		$sql[] = "CREATE TABLE {$p}wpc_lessons (
			id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
			topic VARCHAR(80) NOT NULL,
			lesson TEXT NOT NULL,
			source VARCHAR(10) NOT NULL DEFAULT 'claude',
			created DATETIME NOT NULL,
			PRIMARY KEY  (id),
			KEY topic (topic)
		) {$charset_collate};";

		foreach ( $sql as $statement ) {
			dbDelta( $statement );
		}
	}

	public function table( $name ) {
		global $wpdb;
		return $wpdb->prefix . 'wpc_' . $name;
	}

	/* ------------------------------------------------------------------ */
	/* Cleanup                                                              */
	/* ------------------------------------------------------------------ */

	public function daily_cleanup() {
		global $wpdb;

		$tokens = $this->table( 'tokens' );
		$wpdb->query( $wpdb->prepare( "DELETE FROM {$tokens} WHERE expires < %s", current_time( 'mysql', true ) ) ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared

		$runs = $this->table( 'runs' );
		$wpdb->query( $wpdb->prepare( "DELETE FROM {$runs} WHERE created < %s", gmdate( 'Y-m-d H:i:s', time() - 120 * DAY_IN_SECONDS ) ) ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
	}
}
