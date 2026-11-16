<?php
/**
 * Plugin Name:       WP-Connect
 * Plugin URI:        https://example.com/wp-connect
 * Description:       Connects Claude to this WordPress site over MCP. Choose how much Claude can do, let it learn from real use, and run whole jobs with Auto-Optimize.
 * Version:           1.1.0
 * Requires at least: 6.2
 * Requires PHP:      7.4
 * Author:            WP-Connect
 * License:           GPL v2 or later
 * License URI:       https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain:       wp-connect
 */

if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

define( 'WPC_VERSION', '1.1.0' );
define( 'WPC_DB_VERSION', '2' );
define( 'WPC_FILE', __FILE__ );
define( 'WPC_DIR', plugin_dir_path( __FILE__ ) );
define( 'WPC_URL', plugin_dir_url( __FILE__ ) );

/**
 * Activation: create tables and schedule cron. Kept out of WPC_Plugin so it
 * runs even before the rest of the plugin has booted (plugins_loaded hasn't
 * fired yet during activation).
 */
function wpc_activate() {
	require_once WPC_DIR . 'includes/class-wpc-plugin.php';
	WPC_Plugin::instance()->install();

	if ( ! wp_next_scheduled( 'wpc_agent_scheduler' ) ) {
		wp_schedule_event( time() + 60, 'hourly', 'wpc_agent_scheduler' );
	}
	if ( ! wp_next_scheduled( 'wpc_daily_cleanup' ) ) {
		wp_schedule_event( time() + 120, 'daily', 'wpc_daily_cleanup' );
	}
}
register_activation_hook( __FILE__, 'wpc_activate' );

/**
 * Deactivation: clear scheduled hooks. Data stays unless the owner has
 * opted in to "delete on uninstall" (handled in uninstall.php).
 */
function wpc_deactivate() {
	wp_clear_scheduled_hook( 'wpc_agent_scheduler' );
	wp_clear_scheduled_hook( 'wpc_daily_cleanup' );
	wp_clear_scheduled_hook( 'wpc_agent_tick' );
}
register_deactivation_hook( __FILE__, 'wpc_deactivate' );

/**
 * Boot the plugin once all plugins have loaded, so abilities registered by
 * other plugins (e.g. SEO plugin detection) have had a chance to load too.
 */
function wpc_boot() {
	require_once WPC_DIR . 'includes/class-wpc-plugin.php';
	require_once WPC_DIR . 'includes/class-wpc-backups.php';
	require_once WPC_DIR . 'includes/class-wpc-verify.php';
	require_once WPC_DIR . 'includes/class-wpc-abilities.php';
	require_once WPC_DIR . 'includes/class-wpc-skills.php';
	require_once WPC_DIR . 'includes/class-wpc-oauth.php';
	require_once WPC_DIR . 'includes/class-wpc-mcp.php';
	require_once WPC_DIR . 'includes/class-wpc-agent.php';
	require_once WPC_DIR . 'includes/class-wpc-admin.php';

	WPC_Plugin::instance()->boot();
	WPC_Verify::boot();
	WPC_OAuth::instance()->boot();
	WPC_MCP::instance()->boot();
	WPC_Agent::instance()->boot();
	WPC_Admin::instance()->boot();
}
add_action( 'plugins_loaded', 'wpc_boot' );
