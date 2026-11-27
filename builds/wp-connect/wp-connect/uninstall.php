<?php
if ( ! defined( 'WP_UNINSTALL_PLUGIN' ) ) {
	exit;
}

$wpc_settings = get_option( 'wpc_settings', array() );
if ( empty( $wpc_settings['delete_on_uninstall'] ) ) {
	return;
}

global $wpdb;

$wpc_tables = array(
	$wpdb->prefix . 'wpc_runs',
	$wpdb->prefix . 'wpc_backups',
	$wpdb->prefix . 'wpc_tokens',
	$wpdb->prefix . 'wpc_custom',
	$wpdb->prefix . 'wpc_tasks',
	$wpdb->prefix . 'wpc_lessons',
);

foreach ( $wpc_tables as $wpc_table ) {
	// Table names come from our own fixed prefix list above, never from
	// user input, so direct interpolation here is safe.
	$wpdb->query( "DROP TABLE IF EXISTS `{$wpc_table}`" ); // phpcs:ignore WordPress.DB.PreparedSQL.NotPrepared
}

$wpc_options = array(
	'wpc_settings',
	'wpc_db_version',
	'wpc_oauth_clients',
	'wpc_skills_custom',
	'wpc_skills_overrides',
	'wpc_skill_settings',
	'wpc_reports',
);

foreach ( $wpc_options as $wpc_option ) {
	delete_option( $wpc_option );
}
