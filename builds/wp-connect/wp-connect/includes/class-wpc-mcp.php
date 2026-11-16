<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * The MCP endpoint: streamable HTTP with plain JSON responses (no SSE),
 * JSON-RPC batching, and the tool/prompt surface Claude actually talks to.
 */
class WPC_MCP {

	const SUPPORTED_PROTOCOL_VERSIONS = array( '2025-06-18', '2025-03-26', '2024-11-05' );
	const DEFAULT_PROTOCOL_VERSION    = '2025-06-18';

	private static $instance = null;

	public static function instance() {
		if ( null === self::$instance ) {
			self::$instance = new self();
		}
		return self::$instance;
	}

	public function boot() {
		add_action( 'rest_api_init', array( $this, 'register_routes' ) );
	}

	public function register_routes() {
		register_rest_route(
			'wp-connect/v1',
			'/mcp',
			array(
				array(
					'methods'             => WP_REST_Server::CREATABLE,
					'permission_callback' => '__return_true',
					'callback'            => array( $this, 'handle_post' ),
				),
				array(
					'methods'             => WP_REST_Server::READABLE,
					'permission_callback' => '__return_true',
					'callback'            => array( $this, 'handle_get' ),
				),
				array(
					'methods'             => WP_REST_Server::DELETABLE,
					'permission_callback' => '__return_true',
					'callback'            => array( $this, 'handle_delete' ),
				),
			)
		);
	}

	public function handle_get() {
		return new WP_REST_Response( null, 405, array( 'Allow' => 'POST, DELETE' ) );
	}

	public function handle_delete() {
		return new WP_REST_Response( null, 204 );
	}

	/* ------------------------------------------------------------------ */
	/* Authentication                                                       */
	/* ------------------------------------------------------------------ */

	private function authenticated_user() {
		if ( function_exists( 'rest_get_authenticated_app_password' ) && rest_get_authenticated_app_password() ) {
			set_transient( 'wpc_app_password_used', 1, 7 * DAY_IN_SECONDS );
			return get_current_user_id();
		}

		$header = $this->bearer_header();
		if ( '' !== $header ) {
			$row = WPC_OAuth::instance()->lookup_token( $header, 'access' );
			if ( ! $row ) {
				return new WP_Error( 'invalid_token', __( 'Sign in required.', 'wp-connect' ), array( 'status' => 401 ) );
			}
			WPC_OAuth::instance()->touch_token( $row->id );
			return (int) $row->user_id;
		}

		return new WP_Error( 'unauthorized', __( 'Sign in required.', 'wp-connect' ), array( 'status' => 401 ) );
	}

	private function bearer_header() {
		$header = '';
		if ( ! empty( $_SERVER['HTTP_AUTHORIZATION'] ) ) {
			$header = $_SERVER['HTTP_AUTHORIZATION']; // phpcs:ignore WordPress.Security.ValidatedSanitizedInput
		} elseif ( ! empty( $_SERVER['REDIRECT_HTTP_AUTHORIZATION'] ) ) {
			$header = $_SERVER['REDIRECT_HTTP_AUTHORIZATION']; // phpcs:ignore WordPress.Security.ValidatedSanitizedInput
		} elseif ( function_exists( 'getallheaders' ) ) {
			$all = getallheaders();
			foreach ( $all as $k => $v ) {
				if ( 'authorization' === strtolower( $k ) ) {
					$header = $v;
					break;
				}
			}
		}
		if ( 0 === stripos( $header, 'Bearer ' ) ) {
			return trim( substr( $header, 7 ) );
		}
		return '';
	}

	private function www_authenticate_response() {
		return new WP_REST_Response(
			array( 'error' => 'unauthorized', 'error_description' => __( 'Sign in required.', 'wp-connect' ) ),
			401,
			array( 'WWW-Authenticate' => 'Bearer resource_metadata="' . home_url( '/.well-known/oauth-protected-resource' ) . '"' )
		);
	}

	/* ------------------------------------------------------------------ */
	/* Request handling                                                     */
	/* ------------------------------------------------------------------ */

	public function handle_post( WP_REST_Request $request ) {
		$user_id = $this->authenticated_user();
		if ( is_wp_error( $user_id ) ) {
			return $this->www_authenticate_response();
		}
		if ( ! user_can( $user_id, 'manage_options' ) ) {
			return new WP_REST_Response( array( 'error' => 'forbidden' ), 403 );
		}
		wp_set_current_user( $user_id );

		$body = $request->get_json_params();
		if ( null === $body ) {
			return new WP_REST_Response( $this->error_response( null, -32700, 'Parse error' ), 200 );
		}

		$is_batch   = wp_is_numeric_array( $body ) && isset( $body[0] );
		$messages   = $is_batch ? $body : array( $body );
		$responses  = array();
		$all_notifications = true;

		foreach ( $messages as $message ) {
			$has_id = is_array( $message ) && array_key_exists( 'id', $message );
			if ( $has_id ) {
				$all_notifications = false;
			}
			$result = $this->dispatch( $message, $user_id );
			if ( null !== $result ) {
				$responses[] = $result;
			}
		}

		if ( $all_notifications ) {
			return new WP_REST_Response( null, 202 );
		}

		// Most dispatch() results are plain arrays, but a bare "ping" result
		// is a stdClass; nested isset() on array syntax throws on that in
		// PHP 8+, so the array check must come first and short-circuit.
		$headers = array();
		if ( ! $is_batch && isset( $responses[0]['result'] ) && is_array( $responses[0]['result'] ) && isset( $responses[0]['result']['_session_id'] ) ) {
			$headers['Mcp-Session-Id'] = $responses[0]['result']['_session_id'];
			unset( $responses[0]['result']['_session_id'] );
		}
		$payload = $is_batch ? $responses : ( isset( $responses[0] ) ? $responses[0] : null );

		return new WP_REST_Response( $payload, 200, $headers );
	}

	/**
	 * Dispatch one JSON-RPC message. Returns null for notifications
	 * (messages with no "id"), otherwise a JSON-RPC response array.
	 */
	private function dispatch( $message, $user_id ) {
		$has_id = is_array( $message ) && array_key_exists( 'id', $message );
		$id     = $has_id ? $message['id'] : null;
		$method = isset( $message['method'] ) ? $message['method'] : '';
		$params = isset( $message['params'] ) && is_array( $message['params'] ) ? $message['params'] : array();

		switch ( $method ) {
			case 'initialize':
				$result = $this->handle_initialize( $params );
				break;
			case 'ping':
				$result = new stdClass();
				break;
			case 'tools/list':
				$result = $this->handle_tools_list();
				break;
			case 'tools/call':
				$result = $this->handle_tools_call( $params, $user_id );
				break;
			case 'resources/list':
				$result = array( 'resources' => array() );
				break;
			case 'resources/templates/list':
				$result = array( 'resourceTemplates' => array() );
				break;
			case 'prompts/list':
				$result = $this->handle_prompts_list();
				break;
			case 'prompts/get':
				$result = $this->handle_prompts_get( $params );
				break;
			default:
				if ( ! $has_id ) {
					return null; // Unknown notification: nothing to report.
				}
				return $this->error_response( $id, -32601, 'Method not found' );
		}

		if ( ! $has_id ) {
			return null;
		}

		return array(
			'jsonrpc' => '2.0',
			'id'      => $id,
			'result'  => $result,
		);
	}

	private function error_response( $id, $code, $message ) {
		return array(
			'jsonrpc' => '2.0',
			'id'      => $id,
			'error'   => array( 'code' => $code, 'message' => $message ),
		);
	}

	/* ------------------------------------------------------------------ */
	/* initialize                                                           */
	/* ------------------------------------------------------------------ */

	private function handle_initialize( $params ) {
		$requested = isset( $params['protocolVersion'] ) ? $params['protocolVersion'] : '';
		$version   = in_array( $requested, self::SUPPORTED_PROTOCOL_VERSIONS, true ) ? $requested : self::DEFAULT_PROTOCOL_VERSION;

		return array(
			'protocolVersion' => $version,
			'capabilities'    => array(
				'tools'   => array( 'listChanged' => false ),
				'prompts' => array( 'listChanged' => false ),
			),
			'serverInfo'      => array(
				'name'  => 'wp-connect',
				'title' => 'WP-Connect: ' . get_bloginfo( 'name' ),
			),
			'instructions'    => $this->server_instructions(),
			'_session_id'     => wp_generate_password( 32, false ),
		);
	}

	private function server_instructions() {
		$mode  = WPC_Plugin::instance()->mode();
		$label = WPC_Plugin::instance()->mode_label( $mode );

		$text = sprintf( __( 'You are connected to "%1$s" in %2$s mode.', 'wp-connect' ), get_bloginfo( 'name' ), $label );

		if ( 'full' === $mode ) {
			$text .= ' ' . __( 'run_php can do anything on this site; the specific abilities back up and can be undone, run_php cannot.', 'wp-connect' );
		} else {
			$text .= ' ' . __( 'Claude can only use the listed abilities and can write a new one with wpc_ability_create.', 'wp-connect' );
		}

		$text .= ' ' . __( 'Start with wpc_site_overview, then wpc_playbook topic site_care. For whole jobs, check wpc_skills_list and run the skill with wpc_skill_get. Read before you write. Save lessons when something fails with wpc_lesson_save. Call wpc_run_feedback when the owner says a result was good or wrong. Explain in plain English for a non-technical owner.', 'wp-connect' );

		return $text;
	}

	/* ------------------------------------------------------------------ */
	/* Tools                                                                */
	/* ------------------------------------------------------------------ */

	private function handle_tools_list() {
		$tools = array();
		foreach ( WPC_Abilities::usable_names() as $name ) {
			$def = WPC_Abilities::tool_definition( $name );
			if ( $def ) {
				$tools[] = $def;
			}
		}
		return array( 'tools' => $tools );
	}

	private function handle_tools_call( $params, $user_id ) {
		$name  = isset( $params['name'] ) ? $params['name'] : '';
		$input = isset( $params['arguments'] ) && is_array( $params['arguments'] ) ? $params['arguments'] : array();

		if ( ! in_array( $name, WPC_Abilities::usable_names(), true ) ) {
			return $this->tool_error( sprintf( __( '"%s" is not an ability available in this mode.', 'wp-connect' ), $name ) );
		}

		$run = WPC_Abilities::run( $name, $input, 'chat', $user_id );

		if ( ! $run['success'] ) {
			return $this->tool_error( $run['error'], $run['run_id'] );
		}

		$payload = array( 'result' => $run['result'], 'run_id' => $run['run_id'] );
		if ( $run['undo'] ) {
			$payload['undo'] = __( 'Backed up. The owner can undo this on WP-Connect -> Activity.', 'wp-connect' );
		}

		return array(
			'content' => array( array( 'type' => 'text', 'text' => $this->clip( wp_json_encode( $payload ) ) ) ),
			'isError' => false,
		);
	}

	private function tool_error( $message, $run_id = 0 ) {
		$payload = array(
			'error'   => $message,
			'next'    => __( 'Fix the problem and try again. If you learn why it failed, save it with wpc_lesson_save so it is not repeated.', 'wp-connect' ),
			'run_id'  => $run_id,
		);
		return array(
			'content' => array( array( 'type' => 'text', 'text' => $this->clip( wp_json_encode( $payload ) ) ) ),
			'isError' => true,
		);
	}

	private function clip( $text ) {
		return is_string( $text ) && strlen( $text ) > 250000 ? substr( $text, 0, 250000 ) : $text;
	}

	/* ------------------------------------------------------------------ */
	/* Prompts (skills)                                                     */
	/* ------------------------------------------------------------------ */

	private function handle_prompts_list() {
		$prompts = array();
		foreach ( WPC_Skills::list_summaries() as $skill ) {
			$prompts[] = array(
				'name'        => $skill['name'],
				'title'       => $skill['title'],
				'description' => $skill['description'],
			);
		}
		return array( 'prompts' => $prompts );
	}

	private function handle_prompts_get( $params ) {
		$slug = isset( $params['name'] ) ? $params['name'] : '';
		return array(
			'messages' => array(
				array(
					'role'    => 'user',
					'content' => array(
						'type' => 'text',
						'text' => sprintf( __( 'Run the "%1$s" skill on my site. Call wpc_skill_get with skill "%1$s" and follow its steps.', 'wp-connect' ), $slug ),
					),
				),
			),
		);
	}
}
