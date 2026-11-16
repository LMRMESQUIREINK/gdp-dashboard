<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * AI Agent mode: the plugin drives Claude itself via the Anthropic API,
 * one step (one API call) per tick, with risky tool calls pausing for
 * the owner's approval and recurring jobs re-queuing themselves.
 */
class WPC_Agent {

	const LOCK_SECONDS = 180;

	public static $models = array(
		'claude-sonnet-5-5' => 'Claude Sonnet 5.5 (recommended)',
		'claude-opus-5-5'   => 'Claude Opus 5.5 (most capable)',
		'claude-haiku-5-5'  => 'Claude Haiku 5.5 (fastest)',
	);

	private static $instance = null;

	public static function instance() {
		if ( null === self::$instance ) {
			self::$instance = new self();
		}
		return self::$instance;
	}

	public function boot() {
		add_action( 'wpc_agent_scheduler', array( $this, 'run_scheduler' ) );
		add_action( 'wpc_agent_tick', array( $this, 'tick' ) );
	}

	/* ------------------------------------------------------------------ */
	/* Anthropic API                                                        */
	/* ------------------------------------------------------------------ */

	private function system_prompt() {
		return sprintf(
			'You are the AI agent for the WordPress site "%1$s" (%2$s), running inside the WP-Connect plugin. The site owner gave you a job and is not watching live. Work it out step by step using your tools, then finish with a short plain-English summary for the owner: what you did, links to anything you made, and anything they need to do. Rules: start with wpc_site_overview and wpc_playbook topic site_care. Read before you write. Some actions pause for the owner\'s approval; that is normal. If the owner declines one, carry on without it. When something fails and you learn why, save a lesson with wpc_lesson_save. Don\'t invent results: if you couldn\'t do something, say so. Keep going until the job is done, but stop when it is.',
			get_bloginfo( 'name' ),
			home_url( '/' )
		);
	}

	private function agent_tools() {
		$tools = array();
		foreach ( WPC_Abilities::usable_names( 'agent', true ) as $name ) {
			$def = WPC_Abilities::tool_definition( $name );
			if ( ! $def ) {
				continue;
			}
			$description = $def['description'];
			if ( strlen( $description ) > 4000 ) {
				$description = substr( $description, 0, 4000 );
			}
			$tools[] = array(
				'name'         => $def['name'],
				'description'  => $description,
				'input_schema' => $def['inputSchema'],
			);
		}
		return $tools;
	}

	public function call_api( $messages ) {
		$api_key = WPC_Plugin::instance()->api_key();
		if ( '' === $api_key ) {
			return new WP_Error( 'no_key', __( 'No Anthropic API key is saved.', 'wp-connect' ) );
		}

		$response = wp_remote_post(
			'https://api.anthropic.com/v1/messages',
			array(
				'timeout' => 150,
				'headers' => array(
					'x-api-key'         => $api_key,
					'anthropic-version' => '2023-06-01',
					'content-type'      => 'application/json',
				),
				'body'    => wp_json_encode(
					array(
						'model'      => WPC_Plugin::instance()->get_setting( 'model', 'claude-sonnet-5-5' ),
						'max_tokens' => 8000,
						'system'     => $this->system_prompt(),
						'tools'      => $this->agent_tools(),
						'messages'   => $messages,
					)
				),
			)
		);

		if ( is_wp_error( $response ) ) {
			return $response;
		}

		$code = wp_remote_retrieve_response_code( $response );
		$body = json_decode( wp_remote_retrieve_body( $response ), true );

		if ( 401 === $code ) {
			return new WP_Error( 'unauthorized', __( 'The API key was rejected. Check it in WP-Connect -> Settings.', 'wp-connect' ) );
		}
		if ( $code >= 400 ) {
			$message = isset( $body['error']['message'] ) ? $body['error']['message'] : 'HTTP ' . $code;
			return new WP_Error( 'api_error', $message );
		}

		return $body;
	}

	public function test_key( $api_key ) {
		$response = wp_remote_post(
			'https://api.anthropic.com/v1/messages',
			array(
				'timeout' => 30,
				'headers' => array(
					'x-api-key'         => $api_key,
					'anthropic-version' => '2023-06-01',
					'content-type'      => 'application/json',
				),
				'body'    => wp_json_encode(
					array(
						'model'      => 'claude-haiku-5-5',
						'max_tokens' => 4,
						'messages'   => array( array( 'role' => 'user', 'content' => 'hi' ) ),
					)
				),
			)
		);
		if ( is_wp_error( $response ) ) {
			return $response;
		}
		$code = wp_remote_retrieve_response_code( $response );
		if ( 401 === $code ) {
			return new WP_Error( 'unauthorized', __( 'The API key was rejected.', 'wp-connect' ) );
		}
		if ( $code >= 400 ) {
			$body = json_decode( wp_remote_retrieve_body( $response ), true );
			return new WP_Error( 'api_error', isset( $body['error']['message'] ) ? $body['error']['message'] : 'HTTP ' . $code );
		}
		return true;
	}

	/* ------------------------------------------------------------------ */
	/* Task storage                                                         */
	/* ------------------------------------------------------------------ */

	private function table() {
		return WPC_Plugin::instance()->table( 'tasks' );
	}

	public function get_task( $id ) {
		global $wpdb;
		return $wpdb->get_row( $wpdb->prepare( 'SELECT * FROM ' . $this->table() . ' WHERE id = %d', $id ) ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
	}

	public function tasks( $limit = 30 ) {
		global $wpdb;
		return $wpdb->get_results( $wpdb->prepare( 'SELECT * FROM ' . $this->table() . ' ORDER BY id DESC LIMIT %d', $limit ) ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
	}

	public function waiting_count() {
		global $wpdb;
		return (int) $wpdb->get_var( "SELECT COUNT(*) FROM " . $this->table() . " WHERE status = 'needs_approval'" ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
	}

	private function update_task( $id, $fields ) {
		global $wpdb;
		$fields['updated'] = current_time( 'mysql', true );
		$wpdb->update( $this->table(), $fields, array( 'id' => $id ) );
	}

	private function log_entry( $task, $type, $text ) {
		$log   = json_decode( $task->log, true ) ?: array();
		$log[] = array( 't' => current_time( 'mysql' ), 'type' => $type, 'text' => $text );
		if ( count( $log ) > 200 ) {
			$log = array_slice( $log, -200 );
		}
		return wp_json_encode( $log );
	}

	public function status_label( $status ) {
		$labels = array(
			'queued'         => __( 'Queued', 'wp-connect' ),
			'running'        => __( 'Working', 'wp-connect' ),
			'needs_approval' => __( 'Needs your OK', 'wp-connect' ),
			'done'           => __( 'Done', 'wp-connect' ),
			'failed'         => __( 'Failed', 'wp-connect' ),
			'cancelled'      => __( 'Cancelled', 'wp-connect' ),
			'scheduled'      => __( 'Scheduled', 'wp-connect' ),
		);
		return isset( $labels[ $status ] ) ? $labels[ $status ] : $status;
	}

	/* ------------------------------------------------------------------ */
	/* Lifecycle                                                            */
	/* ------------------------------------------------------------------ */

	public function create( $prompt, $recurrence = 'once', $run_at = null ) {
		global $wpdb;

		$status = $run_at ? 'scheduled' : 'queued';
		$wpdb->insert(
			$this->table(),
			array(
				'prompt'     => $prompt,
				'user_id'    => get_current_user_id(),
				'status'     => $status,
				'recurrence' => $recurrence,
				'run_at'     => $run_at,
				'messages'   => wp_json_encode( array( array( 'role' => 'user', 'content' => $prompt ) ) ),
				'log'        => wp_json_encode( array() ),
				'steps'      => 0,
				'created'    => current_time( 'mysql', true ),
				'updated'    => current_time( 'mysql', true ),
			)
		);
		$id = (int) $wpdb->insert_id;

		if ( 'queued' === $status ) {
			wp_schedule_single_event( time(), 'wpc_agent_tick', array( $id ) );
			if ( function_exists( 'spawn_cron' ) ) {
				spawn_cron();
			}
		}

		return $id;
	}

	public function cancel( $id ) {
		$this->update_task( $id, array( 'status' => 'cancelled' ) );
	}

	/**
	 * One step: one API call, plus running any tool calls that don't need
	 * approval. Locks for LOCK_SECONDS so an overlapping poll/cron run
	 * can't double-process the same task.
	 */
	public function tick( $id ) {
		$lock_key = 'wpc_agent_lock_' . $id;
		if ( get_transient( $lock_key ) ) {
			return;
		}
		set_transient( $lock_key, 1, self::LOCK_SECONDS );

		try {
			$this->tick_locked( $id );
		} finally {
			delete_transient( $lock_key );
		}
	}

	private function tick_locked( $id ) {
		$task = $this->get_task( $id );
		if ( ! $task || ! in_array( $task->status, array( 'queued', 'running' ), true ) ) {
			return;
		}

		$this->update_task( $id, array( 'status' => 'running' ) );
		$task = $this->get_task( $id );

		$max_steps = (int) WPC_Plugin::instance()->get_setting( 'agent_max_steps', 25 );
		if ( (int) $task->steps >= $max_steps ) {
			$this->finish(
				$task,
				'failed',
				sprintf( __( 'Stopped after %d steps (the limit in Settings). Raise the limit or give a narrower job.', 'wp-connect' ), $max_steps )
			);
			return;
		}

		$messages = json_decode( $task->messages, true ) ?: array();
		$response = $this->call_api( $messages );

		if ( is_wp_error( $response ) ) {
			$log = $this->log_entry( $task, 'error', $response->get_error_message() );
			$this->update_task( $id, array( 'log' => $log ) );
			$this->finish( $this->get_task( $id ), 'failed', $response->get_error_message() );
			return;
		}

		$content = isset( $response['content'] ) ? $response['content'] : array();
		$messages[] = array( 'role' => 'assistant', 'content' => $content );

		$log = json_decode( $task->log, true ) ?: array();
		$text_summary = '';
		foreach ( $content as $block ) {
			if ( 'text' === $block['type'] ) {
				$log[]        = array( 't' => current_time( 'mysql' ), 'type' => 'text', 'text' => $block['text'] );
				$text_summary = $block['text'];
			}
		}

		$tool_uses = array_values( array_filter( $content, function ( $b ) { return 'tool_use' === $b['type']; } ) );

		if ( empty( $tool_uses ) ) {
			$this->update_task(
				$id,
				array(
					'messages' => wp_json_encode( $messages ),
					'log'      => wp_json_encode( $log ),
					'steps'    => (int) $task->steps + 1,
				)
			);
			$this->finish( $this->get_task( $id ), 'done', $text_summary );
			return;
		}

		$results       = array();
		$pending_calls = array();

		foreach ( $tool_uses as $tool_use ) {
			$needs_approval = WPC_Abilities::needs_approval( $tool_use['name'] );
			if ( $needs_approval ) {
				$pending_calls[] = $tool_use;
				continue;
			}
			// Run the ability exactly once: this block feeds both the log
			// line and the tool_result sent back to the model, so a write
			// ability never fires twice for one tool_use.
			$block     = $this->tool_result_block( $tool_use, $id );
			$results[] = $block;
			if ( $block['is_error'] ) {
				$decoded = json_decode( $block['content'], true );
				$log[]   = array(
					't'    => current_time( 'mysql' ),
					'type' => 'error',
					'text' => $tool_use['name'] . ' ✗ ' . ( isset( $decoded['error'] ) ? $decoded['error'] : '' ),
				);
			} else {
				$log[] = array( 't' => current_time( 'mysql' ), 'type' => 'tool', 'text' => $tool_use['name'] . ' ✓' );
			}
		}

		if ( ! empty( $pending_calls ) ) {
			foreach ( $pending_calls as $call ) {
				$log[] = array( 't' => current_time( 'mysql' ), 'type' => 'approval', 'text' => sprintf( __( '%s needs your OK.', 'wp-connect' ), $call['name'] ) );
			}
			$this->update_task(
				$id,
				array(
					'status'   => 'needs_approval',
					'messages' => wp_json_encode( $messages ),
					'pending'  => wp_json_encode( array( 'results' => $results, 'waiting' => $pending_calls ) ),
					'log'      => wp_json_encode( $log ),
					'steps'    => (int) $task->steps + 1,
				)
			);
			$this->maybe_email( $this->get_task( $id ), 'approval' );
			return;
		}

		$messages[] = array( 'role' => 'user', 'content' => $results );

		$this->update_task(
			$id,
			array(
				'status'   => 'queued',
				'messages' => wp_json_encode( $messages ),
				'log'      => wp_json_encode( $log ),
				'steps'    => (int) $task->steps + 1,
			)
		);
		wp_schedule_single_event( time(), 'wpc_agent_tick', array( $id ) );
		if ( function_exists( 'spawn_cron' ) ) {
			spawn_cron();
		}
	}

	private function tool_result_block( $tool_use, $task_id, $declined = false ) {
		if ( $declined ) {
			$text = wp_json_encode(
				array(
					'error' => __( 'The site owner declined this action. Do not retry it; continue without it or explain what you would need.', 'wp-connect' ),
				)
			);
			return array(
				'type'        => 'tool_result',
				'tool_use_id' => $tool_use['id'],
				'content'     => $text,
				'is_error'    => true,
			);
		}

		$run = WPC_Abilities::run( $tool_use['name'], $tool_use['input'], 'agent', 0, $task_id );
		$payload = $run['success']
			? array( 'result' => $run['result'], 'run_id' => $run['run_id'] )
			: array( 'error' => $run['error'], 'run_id' => $run['run_id'] );

		return array(
			'type'        => 'tool_result',
			'tool_use_id' => $tool_use['id'],
			'content'     => wp_json_encode( $payload ),
			'is_error'    => ! $run['success'],
		);
	}

	/**
	 * Run or decline every call a needs_approval task is waiting on, then
	 * resume the loop.
	 */
	public function resolve( $id, $approve ) {
		$task = $this->get_task( $id );
		if ( ! $task || 'needs_approval' !== $task->status ) {
			return false;
		}

		$pending  = json_decode( $task->pending, true );
		$messages = json_decode( $task->messages, true );
		$log      = json_decode( $task->log, true ) ?: array();
		$results  = isset( $pending['results'] ) ? $pending['results'] : array();

		foreach ( (array) $pending['waiting'] as $call ) {
			$block     = $this->tool_result_block( $call, $id, ! $approve );
			$results[] = $block;

			if ( ! $approve ) {
				$text = $call['name'] . ' declined by owner';
				$type = 'approval';
			} elseif ( $block['is_error'] ) {
				$decoded = json_decode( $block['content'], true );
				$text    = $call['name'] . ' ✗ (approved) ' . ( isset( $decoded['error'] ) ? $decoded['error'] : '' );
				$type    = 'error';
			} else {
				$text = $call['name'] . ' ✓ (approved)';
				$type = 'tool';
			}

			$log[] = array(
				't'    => current_time( 'mysql' ),
				'type' => $type,
				'text' => $text,
			);
		}

		$messages[] = array( 'role' => 'user', 'content' => $results );

		$this->update_task(
			$id,
			array(
				'status'   => 'queued',
				'messages' => wp_json_encode( $messages ),
				'pending'  => null,
				'log'      => wp_json_encode( $log ),
			)
		);
		wp_schedule_single_event( time(), 'wpc_agent_tick', array( $id ) );
		if ( function_exists( 'spawn_cron' ) ) {
			spawn_cron();
		}
		return true;
	}

	private function finish( $task, $status, $result_text ) {
		$this->update_task( $task->id, array( 'status' => $status, 'result' => $result_text ) );
		$this->maybe_email( $this->get_task( $task->id ), $status );

		if ( 'done' === $status && 'once' !== $task->recurrence ) {
			$next = 'daily' === $task->recurrence ? time() + DAY_IN_SECONDS : time() + WEEK_IN_SECONDS;
			$this->create( $task->prompt, $task->recurrence, gmdate( 'Y-m-d H:i:s', $next ) );
		}
	}

	private function maybe_email( $task, $event ) {
		if ( ! WPC_Plugin::instance()->get_setting( 'email_on_done', true ) ) {
			return;
		}
		$admin = get_option( 'admin_email' );
		if ( 'approval' === $event ) {
			wp_mail( $admin, __( 'WP-Connect: a job needs your OK', 'wp-connect' ), sprintf( __( 'Job: %s', 'wp-connect' ), $task->prompt ) . "\n" . admin_url( 'admin.php?page=wp-connect&tab=agent' ) );
		} elseif ( in_array( $event, array( 'done', 'failed' ), true ) ) {
			wp_mail( $admin, __( 'WP-Connect: a job finished', 'wp-connect' ), sprintf( __( 'Job: %s', 'wp-connect' ), $task->prompt ) . "\n" . admin_url( 'admin.php?page=wp-connect&tab=agent' ) );
		}
	}

	/**
	 * Hourly: queue any scheduled tasks that are due.
	 */
	public function run_scheduler() {
		global $wpdb;
		$due = $wpdb->get_results(
			$wpdb->prepare( 'SELECT * FROM ' . $this->table() . " WHERE status = 'scheduled' AND run_at <= %s", current_time( 'mysql', true ) ) // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
		);
		foreach ( (array) $due as $task ) {
			$this->update_task( $task->id, array( 'status' => 'queued' ) );
			wp_schedule_single_event( time(), 'wpc_agent_tick', array( (int) $task->id ) );
		}
	}

	/**
	 * Used by the dashboard's 3s poll so a slow WP-Cron doesn't stall a
	 * queued task.
	 */
	public function poll( $id ) {
		$task = $this->get_task( $id );
		if ( $task && in_array( $task->status, array( 'queued' ), true ) ) {
			$this->tick( $id );
			$task = $this->get_task( $id );
		}
		return $task;
	}
}
