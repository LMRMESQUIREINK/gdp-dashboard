<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Takes a backup before a write, and can put things back. $run_id is set by
 * WPC_Abilities right before it calls an ability's callback, so every
 * backup taken during that call links to the run that caused it.
 */
class WPC_Backups {

	public static $run_id = 0;

	/* ------------------------------------------------------------------ */
	/* Recording backups                                                    */
	/* ------------------------------------------------------------------ */

	private static function record( $type, $target, $label, $data ) {
		global $wpdb;
		$wpdb->insert(
			WPC_Plugin::instance()->table( 'backups' ),
			array(
				'run_id'  => self::$run_id,
				'type'    => $type,
				'target'  => (string) $target,
				'label'   => $label,
				'data'    => wp_json_encode( $data ),
				'undone'  => 0,
				'created' => current_time( 'mysql', true ),
			),
			array( '%d', '%s', '%s', '%s', '%s', '%d', '%s' )
		);
		return (int) $wpdb->insert_id;
	}

	public static function post( $post_id, $label, $meta_keys = array() ) {
		$post = get_post( $post_id, ARRAY_A );
		if ( ! $post ) {
			return 0;
		}
		$meta = array();
		foreach ( $meta_keys as $key ) {
			$meta[ $key ] = array(
				'exists' => metadata_exists( 'post', $post_id, $key ),
				'value'  => get_post_meta( $post_id, $key, true ),
			);
		}
		return self::record(
			'post',
			$post_id,
			$label,
			array(
				'post' => array(
					'ID'           => $post['ID'],
					'post_title'   => $post['post_title'],
					'post_content' => $post['post_content'],
					'post_excerpt' => $post['post_excerpt'],
					'post_status'  => $post['post_status'],
					'post_name'    => $post['post_name'],
					'post_parent'  => $post['post_parent'],
					'menu_order'   => $post['menu_order'],
				),
				'meta' => $meta,
			)
		);
	}

	public static function post_created( $post_id, $label ) {
		return self::record( 'post_created', $post_id, $label, array( 'post_id' => $post_id ) );
	}

	public static function option( $option_name, $label ) {
		return self::record(
			'option',
			$option_name,
			$label,
			array(
				'name'  => $option_name,
				'value' => get_option( $option_name ),
			)
		);
	}

	public static function file( $path, $label, $attachment_id = 0, $backup_dir = null ) {
		$meta = $attachment_id ? wp_get_attachment_metadata( $attachment_id ) : array();
		$copy = $backup_dir
			? trailingslashit( $backup_dir ) . basename( $path ) . '.wpc-bak-' . time()
			: $path . '.wpc-bak-' . time();
		if ( file_exists( $path ) ) {
			copy( $path, $copy );
		}
		return self::record(
			'file',
			$path,
			$label,
			array(
				'path'          => $path,
				'copy'          => $copy,
				'attachment_id' => $attachment_id,
				'meta'          => $meta,
			)
		);
	}

	public static function plugin_installed( $plugin_file, $label ) {
		return self::record( 'plugin_installed', $plugin_file, $label, array( 'plugin' => $plugin_file ) );
	}

	public static function plugin_activated( $plugin_file, $label ) {
		return self::record( 'plugin_activated', $plugin_file, $label, array( 'plugin' => $plugin_file ) );
	}

	public static function plugin_deactivated( $plugin_file, $label ) {
		return self::record( 'plugin_deactivated', $plugin_file, $label, array( 'plugin' => $plugin_file ) );
	}

	/* ------------------------------------------------------------------ */
	/* Undo                                                                 */
	/* ------------------------------------------------------------------ */

	public static function get( $backup_id ) {
		global $wpdb;
		return $wpdb->get_row(
			$wpdb->prepare( 'SELECT * FROM ' . WPC_Plugin::instance()->table( 'backups' ) . ' WHERE id = %d', $backup_id ) // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
		);
	}

	/**
	 * Undo every backup belonging to $run_id, newest first, and mark each
	 * as undone. Returns true if at least one backup was actually undone.
	 */
	public static function undo_run( $run_id ) {
		global $wpdb;
		$table   = WPC_Plugin::instance()->table( 'backups' );
		$backups = $wpdb->get_results(
			$wpdb->prepare( "SELECT * FROM {$table} WHERE run_id = %d AND undone = 0 ORDER BY id DESC", $run_id ) // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
		);

		if ( ! $backups ) {
			return false;
		}

		foreach ( $backups as $backup ) {
			self::undo_one( $backup );
			$wpdb->update( $table, array( 'undone' => 1 ), array( 'id' => $backup->id ), array( '%d' ), array( '%d' ) );
		}
		return true;
	}

	private static function undo_one( $backup ) {
		$data = json_decode( $backup->data, true );
		if ( ! is_array( $data ) ) {
			return;
		}

		switch ( $backup->type ) {
			case 'post':
				$post_id = (int) $backup->target;
				wp_update_post(
					array_merge( array( 'ID' => $post_id ), $data['post'] )
				);
				foreach ( (array) $data['meta'] as $key => $m ) {
					if ( $m['exists'] ) {
						update_post_meta( $post_id, $key, wp_slash( $m['value'] ) );
					} else {
						delete_post_meta( $post_id, $key );
					}
				}
				self::clear_elementor_cache( $post_id );
				break;

			case 'post_created':
				wp_trash_post( (int) $data['post_id'] );
				break;

			case 'option':
				update_option( $data['name'], $data['value'] );
				do_action( 'wpc_after_option_restore', $data['name'] );
				break;

			case 'file':
				if ( file_exists( $data['copy'] ) ) {
					copy( $data['copy'], $data['path'] );
					unlink( $data['copy'] );
				}
				if ( $data['attachment_id'] && $data['meta'] ) {
					wp_update_attachment_metadata( $data['attachment_id'], $data['meta'] );
				}
				break;

			case 'plugin_installed':
				deactivate_plugins( $data['plugin'] );
				if ( ! function_exists( 'delete_plugins' ) ) {
					require_once ABSPATH . 'wp-admin/includes/plugin.php';
				}
				delete_plugins( array( $data['plugin'] ) );
				break;

			case 'plugin_activated':
				deactivate_plugins( $data['plugin'] );
				break;

			case 'plugin_deactivated':
				activate_plugin( $data['plugin'] );
				break;
		}
	}

	private static function clear_elementor_cache( $post_id ) {
		if ( class_exists( '\Elementor\Plugin' ) ) {
			try {
				\Elementor\Plugin::$instance->files_manager->clear_cache();
			} catch ( \Throwable $e ) { // phpcs:ignore Generic.CodeAnalysis.EmptyStatement
				// Elementor not fully loaded; nothing to clear.
			}
		}
	}
}
