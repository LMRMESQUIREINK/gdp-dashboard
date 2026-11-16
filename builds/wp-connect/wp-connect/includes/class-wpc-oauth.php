<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * A real, minimal OAuth 2.1 authorization server so Claude (or any MCP
 * client) can sign in as a WordPress admin without sharing a password:
 * discovery, dynamic client registration, the authorize/consent screen,
 * and the token endpoint (authorization_code + refresh_token).
 */
class WPC_OAuth {

	private static $instance = null;

	public static function instance() {
		if ( null === self::$instance ) {
			self::$instance = new self();
		}
		return self::$instance;
	}

	public function boot() {
		add_action( 'init', array( $this, 'maybe_serve_discovery' ), 0 );
		add_action( 'rest_api_init', array( $this, 'register_routes' ) );
		add_action( 'admin_post_nopriv_wpc_authorize', array( $this, 'authorize_redirect_to_login' ) );
		add_action( 'admin_post_wpc_authorize', array( $this, 'authorize' ) );
		add_action( 'admin_post_wpc_authorize_decision', array( $this, 'authorize_decision' ) );
	}

	/* ------------------------------------------------------------------ */
	/* Discovery                                                            */
	/* ------------------------------------------------------------------ */

	public function mcp_url() {
		return rest_url( 'wp-connect/v1/mcp' );
	}

	private function cors_headers() {
		if ( headers_sent() ) {
			return;
		}
		header( 'Access-Control-Allow-Origin: *' );
		header( 'Access-Control-Allow-Methods: GET, POST, OPTIONS' );
		header( 'Access-Control-Allow-Headers: Authorization, Content-Type, Mcp-Protocol-Version, Mcp-Session-Id' );
		header( 'Cache-Control: no-store' );
	}

	public function maybe_serve_discovery() {
		$path = isset( $_SERVER['REQUEST_URI'] ) ? wp_parse_url( $_SERVER['REQUEST_URI'], PHP_URL_PATH ) : '';
		if ( ! $path ) {
			return;
		}

		if ( false !== strpos( $path, '/.well-known/oauth-protected-resource' ) ) {
			$this->cors_headers();
			wp_send_json(
				array(
					'resource'               => $this->mcp_url(),
					'authorization_servers'  => array( untrailingslashit( home_url() ) ),
					'bearer_methods_supported' => array( 'header' ),
					'scopes_supported'       => array( 'wp-connect' ),
					'resource_name'          => get_bloginfo( 'name' ) . ' (WP-Connect)',
				)
			);
		}

		if ( false !== strpos( $path, '/.well-known/oauth-authorization-server' ) || false !== strpos( $path, '/.well-known/openid-configuration' ) ) {
			$this->cors_headers();
			wp_send_json( $this->server_metadata() );
		}
	}

	private function server_metadata() {
		return array(
			'issuer'                                => untrailingslashit( home_url() ),
			'authorization_endpoint'                => admin_url( 'admin-post.php?action=wpc_authorize' ),
			'token_endpoint'                        => rest_url( 'wp-connect/v1/oauth/token' ),
			'registration_endpoint'                 => rest_url( 'wp-connect/v1/oauth/register' ),
			'response_types_supported'              => array( 'code' ),
			'grant_types_supported'                 => array( 'authorization_code', 'refresh_token' ),
			'code_challenge_methods_supported'       => array( 'S256' ),
			'token_endpoint_auth_methods_supported'  => array( 'none', 'client_secret_post', 'client_secret_basic' ),
			'scopes_supported'                       => array( 'wp-connect' ),
		);
	}

	public function register_routes() {
		register_rest_route(
			'wp-connect/v1',
			'/oauth/metadata',
			array(
				'methods'             => 'GET',
				'permission_callback' => '__return_true',
				'callback'            => function () {
					return $this->server_metadata();
				},
			)
		);

		register_rest_route(
			'wp-connect/v1',
			'/oauth/register',
			array(
				'methods'             => 'POST',
				'permission_callback' => '__return_true',
				'callback'            => array( $this, 'rest_register_client' ),
			)
		);

		register_rest_route(
			'wp-connect/v1',
			'/oauth/token',
			array(
				'methods'             => 'POST',
				'permission_callback' => '__return_true',
				'callback'            => array( $this, 'rest_token' ),
			)
		);
	}

	/* ------------------------------------------------------------------ */
	/* Dynamic client registration                                         */
	/* ------------------------------------------------------------------ */

	private function clients() {
		return (array) get_option( 'wpc_oauth_clients', array() );
	}

	private function save_clients( $clients ) {
		if ( count( $clients ) > 100 ) {
			$clients = array_slice( $clients, -100, null, true );
		}
		update_option( 'wpc_oauth_clients', $clients, false );
	}

	private function is_valid_redirect_uri( $uri ) {
		$parts = wp_parse_url( $uri );
		if ( ! $parts || empty( $parts['scheme'] ) || ! empty( $parts['fragment'] ) ) {
			return false;
		}
		if ( 'https' === $parts['scheme'] ) {
			return true;
		}
		if ( 'http' === $parts['scheme'] && in_array( $parts['host'], array( 'localhost', '127.0.0.1', '::1' ), true ) ) {
			return true;
		}
		return false;
	}

	public function rest_register_client( WP_REST_Request $request ) {
		$body = $request->get_json_params();
		if ( ! is_array( $body ) ) {
			$body = array();
		}

		$redirect_uris = isset( $body['redirect_uris'] ) ? (array) $body['redirect_uris'] : array();
		if ( empty( $redirect_uris ) ) {
			return new WP_REST_Response( array( 'error' => 'invalid_redirect_uri', 'error_description' => 'redirect_uris is required.' ), 400 );
		}
		foreach ( $redirect_uris as $uri ) {
			if ( ! $this->is_valid_redirect_uri( $uri ) ) {
				return new WP_REST_Response( array( 'error' => 'invalid_redirect_uri', 'error_description' => 'redirect_uris must be https, or http on localhost, with no fragment.' ), 400 );
			}
		}

		$auth_method = isset( $body['token_endpoint_auth_method'] ) ? $body['token_endpoint_auth_method'] : 'none';
		$client_id   = 'wpc_' . wp_generate_password( 24, false );
		$secret      = '';
		$secret_hash = '';
		if ( 'none' !== $auth_method ) {
			$secret      = wp_generate_password( 40, false );
			$secret_hash = hash( 'sha256', $secret );
		}

		$clients               = $this->clients();
		$clients[ $client_id ] = array(
			'client_id'                   => $client_id,
			'client_name'                 => isset( $body['client_name'] ) ? sanitize_text_field( $body['client_name'] ) : '',
			'redirect_uris'               => $redirect_uris,
			'token_endpoint_auth_method'  => $auth_method,
			'secret_hash'                 => $secret_hash,
			'created'                     => time(),
		);
		$this->save_clients( $clients );

		$response = array(
			'client_id'                  => $client_id,
			'client_name'                => $clients[ $client_id ]['client_name'],
			'redirect_uris'              => $redirect_uris,
			'token_endpoint_auth_method' => $auth_method,
			'grant_types'                => array( 'authorization_code', 'refresh_token' ),
			'response_types'             => array( 'code' ),
		);
		if ( '' !== $secret ) {
			$response['client_secret'] = $secret;
		}

		return new WP_REST_Response( $response, 201 );
	}

	/* ------------------------------------------------------------------ */
	/* Authorize / consent                                                  */
	/* ------------------------------------------------------------------ */

	public function authorize_redirect_to_login() {
		// Preserve client_id/redirect_uri/PKCE/state so the authorize request
		// can be re-run, unchanged, once the owner is logged in.
		$current     = isset( $_SERVER['REQUEST_URI'] ) ? wp_unslash( $_SERVER['REQUEST_URI'] ) : '/wp-admin/admin-post.php';
		$redirect_to = home_url( $current );
		wp_safe_redirect( wp_login_url( $redirect_to ) );
		exit;
	}

	public function authorize() {
		$client_id     = isset( $_GET['client_id'] ) ? sanitize_text_field( wp_unslash( $_GET['client_id'] ) ) : '';
		$redirect_uri  = isset( $_GET['redirect_uri'] ) ? esc_url_raw( wp_unslash( $_GET['redirect_uri'] ) ) : '';
		$response_type = isset( $_GET['response_type'] ) ? sanitize_text_field( wp_unslash( $_GET['response_type'] ) ) : '';
		$state         = isset( $_GET['state'] ) ? sanitize_text_field( wp_unslash( $_GET['state'] ) ) : '';
		$challenge     = isset( $_GET['code_challenge'] ) ? sanitize_text_field( wp_unslash( $_GET['code_challenge'] ) ) : '';
		$challenge_method = isset( $_GET['code_challenge_method'] ) ? sanitize_text_field( wp_unslash( $_GET['code_challenge_method'] ) ) : '';

		$clients = $this->clients();
		if ( '' === $client_id || ! isset( $clients[ $client_id ] ) ) {
			wp_die( esc_html__( 'Unknown client. Ask Claude to reconnect so a new client is registered.', 'wp-connect' ) );
		}
		$client = $clients[ $client_id ];

		if ( ! in_array( $redirect_uri, $client['redirect_uris'], true ) ) {
			if ( 1 !== count( $client['redirect_uris'] ) ) {
				wp_die( esc_html__( 'redirect_uri does not match what was registered.', 'wp-connect' ) );
			}
			$redirect_uri = $client['redirect_uris'][0];
		}
		if ( 'code' !== $response_type ) {
			wp_die( esc_html__( 'Only response_type=code is supported.', 'wp-connect' ) );
		}
		if ( '' === $challenge || 'S256' !== $challenge_method ) {
			wp_die( esc_html__( 'PKCE (code_challenge_method=S256) is required.', 'wp-connect' ) );
		}
		if ( ! current_user_can( 'manage_options' ) ) {
			wp_die( esc_html__( 'Only administrators can connect Claude to this site.', 'wp-connect' ) );
		}

		$this->render_consent_screen( $client, $client_id, $redirect_uri, $state, $challenge );
		exit;
	}

	private function render_consent_screen( $client, $client_id, $redirect_uri, $state, $challenge ) {
		$mode          = WPC_Plugin::instance()->mode();
		$mode_label    = WPC_Plugin::instance()->mode_label( $mode );
		$ability_count = count( WPC_Abilities::usable_names( $mode ) );
		$user          = wp_get_current_user();
		$client_name   = $client['client_name'] ? $client['client_name'] : __( 'This app', 'wp-connect' );

		?>
<!doctype html>
<html lang="<?php echo esc_attr( get_locale() ); ?>">
<head>
<meta charset="utf-8">
<title><?php esc_html_e( 'Connect Claude', 'wp-connect' ); ?></title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
	body{background:#f6f7fb;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;display:flex;min-height:100vh;align-items:center;justify-content:center;margin:0;}
	.card{background:#fff;max-width:440px;width:100%;padding:36px 32px;border-radius:18px;box-shadow:0 6px 24px rgba(15,23,42,.08);}
	.pill{display:inline-flex;align-items:center;gap:7px;font-size:13px;font-weight:600;padding:6px 12px;border-radius:999px;background:#f1f3f9;margin-bottom:18px;}
	.pill i{width:8px;height:8px;border-radius:50%;background:#16a34a;}
	h1{font-size:19px;margin:0 0 18px;}
	.box{font-size:13.5px;padding:12px 14px;border-radius:12px;background:#f1f3f9;color:#334155;margin:0 0 16px;}
	.box.warn{background:#fff1f3;color:#9f1239;}
	p{font-size:14px;color:#334155;}
	.actions{display:flex;gap:10px;margin-top:22px;}
	button{flex:1;padding:11px 16px;border-radius:10px;font-weight:600;font-size:14px;cursor:pointer;border:1px solid #e5e7ef;}
	.allow{background:#0f172a;color:#fff;border-color:#0f172a;}
	.cancel{background:#fff;color:#0f172a;}
	.muted{color:#64748b;font-size:12.5px;margin-top:14px;}
</style>
</head>
<body>
<div class="card">
	<div class="pill"><i></i><?php echo esc_html( $client_name ); ?></div>
	<h1><?php esc_html_e( 'Allow Claude to connect?', 'wp-connect' ); ?></h1>
	<p><?php echo esc_html( sprintf( __( '%1$s wants to connect to %2$s as %3$s.', 'wp-connect' ), $client_name, get_bloginfo( 'name' ), $user->user_login ) ); ?></p>
	<?php if ( 'full' === $mode ) : ?>
		<div class="box warn"><?php esc_html_e( 'Full Access is on: Claude can run any code and change anything on this site. Code runs are logged but can\'t be undone.', 'wp-connect' ); ?></div>
	<?php else : ?>
		<div class="box"><?php echo esc_html( sprintf( __( 'Claude can use the %d abilities you have switched on. Every change is backed up and can be undone.', 'wp-connect' ), $ability_count ) ); ?></div>
	<?php endif; ?>
	<p class="muted"><?php esc_html_e( 'You can disconnect at any time from WP-Connect -> Connect.', 'wp-connect' ); ?></p>
	<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php?action=wpc_authorize_decision' ) ); ?>">
		<?php wp_nonce_field( 'wpc_authorize', 'wpc_authorize_nonce' ); ?>
		<input type="hidden" name="client_id" value="<?php echo esc_attr( $client_id ); ?>">
		<input type="hidden" name="redirect_uri" value="<?php echo esc_attr( $redirect_uri ); ?>">
		<input type="hidden" name="state" value="<?php echo esc_attr( $state ); ?>">
		<input type="hidden" name="code_challenge" value="<?php echo esc_attr( $challenge ); ?>">
		<div class="actions">
			<button class="cancel" type="submit" name="decision" value="cancel"><?php esc_html_e( 'Cancel', 'wp-connect' ); ?></button>
			<button class="allow" type="submit" name="decision" value="allow"><?php esc_html_e( 'Allow', 'wp-connect' ); ?></button>
		</div>
	</form>
</div>
</body>
</html>
		<?php
	}

	public function authorize_decision() {
		if ( ! isset( $_POST['wpc_authorize_nonce'] ) || ! wp_verify_nonce( sanitize_text_field( wp_unslash( $_POST['wpc_authorize_nonce'] ) ), 'wpc_authorize' ) ) {
			wp_die( esc_html__( 'Security check failed. Please try connecting again.', 'wp-connect' ) );
		}
		if ( ! current_user_can( 'manage_options' ) ) {
			wp_die( esc_html__( 'Only administrators can connect Claude to this site.', 'wp-connect' ) );
		}

		$client_id    = sanitize_text_field( wp_unslash( $_POST['client_id'] ) );
		$redirect_uri = esc_url_raw( wp_unslash( $_POST['redirect_uri'] ) );
		$state        = isset( $_POST['state'] ) ? sanitize_text_field( wp_unslash( $_POST['state'] ) ) : '';
		$challenge    = sanitize_text_field( wp_unslash( $_POST['code_challenge'] ) );
		$decision     = isset( $_POST['decision'] ) ? $_POST['decision'] : 'cancel';

		if ( 'allow' !== $decision ) {
			wp_safe_redirect( add_query_arg( array( 'error' => 'access_denied', 'state' => $state ), $redirect_uri ) );
			exit;
		}

		$code = wp_generate_password( 64, false, false );
		$code = strtolower( preg_replace( '/[^A-Za-z0-9]/', '', $code . wp_generate_password( 64, false, false ) ) );
		$code = substr( $code, 0, 64 );

		set_transient(
			'wpc_authcode_' . $code,
			array(
				'client_id'    => $client_id,
				'redirect_uri' => $redirect_uri,
				'challenge'    => $challenge,
				'user'         => get_current_user_id(),
			),
			10 * MINUTE_IN_SECONDS
		);

		wp_safe_redirect( add_query_arg( array( 'code' => $code, 'state' => $state ), $redirect_uri ) );
		exit;
	}

	/* ------------------------------------------------------------------ */
	/* Token endpoint                                                       */
	/* ------------------------------------------------------------------ */

	private function authenticate_client( WP_REST_Request $request ) {
		$clients = $this->clients();

		$auth_header = $request->get_header( 'authorization' );
		if ( $auth_header && 0 === stripos( $auth_header, 'Basic ' ) ) {
			$decoded = base64_decode( substr( $auth_header, 6 ) );
			if ( false !== $decoded && false !== strpos( $decoded, ':' ) ) {
				list( $client_id, $secret ) = explode( ':', $decoded, 2 );
			}
		}
		if ( empty( $client_id ) ) {
			$client_id = $request->get_param( 'client_id' );
			$secret    = $request->get_param( 'client_secret' );
		}

		if ( empty( $client_id ) || ! isset( $clients[ $client_id ] ) ) {
			return false;
		}
		$client = $clients[ $client_id ];

		if ( '' !== $client['secret_hash'] ) {
			if ( empty( $secret ) || hash( 'sha256', $secret ) !== $client['secret_hash'] ) {
				return false;
			}
		}

		return array( 'client_id' => $client_id, 'client' => $client );
	}

	public function rest_token( WP_REST_Request $request ) {
		$grant_type = $request->get_param( 'grant_type' );
		$auth       = $this->authenticate_client( $request );
		if ( ! $auth ) {
			return new WP_REST_Response( array( 'error' => 'invalid_client', 'error_description' => 'Client authentication failed.' ), 401 );
		}

		if ( 'authorization_code' === $grant_type ) {
			return $this->token_from_code( $request, $auth['client_id'] );
		}
		if ( 'refresh_token' === $grant_type ) {
			return $this->token_from_refresh( $request, $auth['client_id'] );
		}

		return new WP_REST_Response( array( 'error' => 'unsupported_grant_type' ), 400 );
	}

	private function token_from_code( WP_REST_Request $request, $client_id ) {
		$code = $request->get_param( 'code' );
		$data = get_transient( 'wpc_authcode_' . $code );
		if ( ! $data ) {
			return new WP_REST_Response( array( 'error' => 'invalid_grant', 'error_description' => 'The code is invalid, expired, or already used.' ), 400 );
		}
		delete_transient( 'wpc_authcode_' . $code ); // Single use.

		if ( $data['client_id'] !== $client_id ) {
			return new WP_REST_Response( array( 'error' => 'invalid_grant', 'error_description' => 'Code was not issued to this client.' ), 400 );
		}
		if ( $data['redirect_uri'] !== $request->get_param( 'redirect_uri' ) ) {
			return new WP_REST_Response( array( 'error' => 'invalid_grant', 'error_description' => 'redirect_uri does not match.' ), 400 );
		}

		$verifier = (string) $request->get_param( 'code_verifier' );
		$computed = rtrim( strtr( base64_encode( hash( 'sha256', $verifier, true ) ), '+/', '-_' ), '=' );
		if ( '' === $verifier || $computed !== $data['challenge'] ) {
			return new WP_REST_Response( array( 'error' => 'invalid_grant', 'error_description' => 'PKCE verification failed.' ), 400 );
		}

		return new WP_REST_Response( $this->issue_tokens( $client_id, $data['user'] ) );
	}

	private function token_from_refresh( WP_REST_Request $request, $client_id ) {
		$refresh_token = (string) $request->get_param( 'refresh_token' );
		$row           = $this->lookup_token( $refresh_token, 'refresh' );
		if ( ! $row || $row->client_id !== $client_id ) {
			return new WP_REST_Response( array( 'error' => 'invalid_grant', 'error_description' => 'The refresh token is invalid or expired.' ), 400 );
		}
		if ( ! user_can( $row->user_id, 'manage_options' ) ) {
			return new WP_REST_Response( array( 'error' => 'invalid_grant', 'error_description' => 'The connected user is no longer an administrator.' ), 400 );
		}

		$access = $this->create_token( 'access', $client_id, $row->user_id, HOUR_IN_SECONDS );

		return new WP_REST_Response(
			array(
				'access_token'  => $access,
				'token_type'    => 'Bearer',
				'expires_in'    => HOUR_IN_SECONDS,
				'refresh_token' => $refresh_token,
			)
		);
	}

	private function issue_tokens( $client_id, $user_id ) {
		$access  = $this->create_token( 'access', $client_id, $user_id, HOUR_IN_SECONDS );
		$refresh = $this->create_token( 'refresh', $client_id, $user_id, 90 * DAY_IN_SECONDS );

		return array(
			'access_token'  => $access,
			'token_type'    => 'Bearer',
			'expires_in'    => HOUR_IN_SECONDS,
			'refresh_token' => $refresh,
			'scope'         => 'wp-connect',
		);
	}

	private function create_token( $type, $client_id, $user_id, $ttl ) {
		global $wpdb;
		$raw = ( 'access' === $type ? 'wpca_' : 'wpcr_' ) . bin2hex( random_bytes( 24 ) );

		$wpdb->insert(
			WPC_Plugin::instance()->table( 'tokens' ),
			array(
				'token_hash' => hash( 'sha256', $raw ),
				'type'       => $type,
				'client_id'  => $client_id,
				'user_id'    => $user_id,
				'expires'    => gmdate( 'Y-m-d H:i:s', time() + $ttl ),
				'created'    => current_time( 'mysql', true ),
			),
			array( '%s', '%s', '%s', '%d', '%s', '%s' )
		);

		return $raw;
	}

	public function lookup_token( $raw, $type = 'access' ) {
		global $wpdb;
		$table = WPC_Plugin::instance()->table( 'tokens' );
		return $wpdb->get_row(
			$wpdb->prepare(
				"SELECT * FROM {$table} WHERE token_hash = %s AND type = %s AND expires > %s", // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
				hash( 'sha256', $raw ),
				$type,
				current_time( 'mysql', true )
			)
		);
	}

	public function touch_token( $token_id ) {
		global $wpdb;
		$table = WPC_Plugin::instance()->table( 'tokens' );
		$last  = $wpdb->get_var( $wpdb->prepare( "SELECT last_used FROM {$table} WHERE id = %d", $token_id ) ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
		if ( $last && strtotime( $last ) > time() - 5 * MINUTE_IN_SECONDS ) {
			return;
		}
		$wpdb->update( $table, array( 'last_used' => current_time( 'mysql', true ) ), array( 'id' => $token_id ), array( '%s' ), array( '%d' ) );
	}

	public function disconnect_all() {
		global $wpdb;
		$wpdb->query( 'TRUNCATE TABLE ' . WPC_Plugin::instance()->table( 'tokens' ) ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
		update_option( 'wpc_oauth_clients', array(), false );
	}

	public function connected_apps() {
		global $wpdb;
		$table = WPC_Plugin::instance()->table( 'tokens' );
		$rows  = $wpdb->get_results( "SELECT client_id, user_id, MAX(last_used) AS last_used, MAX(created) AS created FROM {$table} GROUP BY client_id, user_id" ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared

		$clients = $this->clients();
		$out     = array();
		foreach ( (array) $rows as $row ) {
			$user = get_user_by( 'id', $row->user_id );
			$out[] = array(
				'client_id'   => $row->client_id,
				'client_name' => isset( $clients[ $row->client_id ] ) ? $clients[ $row->client_id ]['client_name'] : $row->client_id,
				'user'        => $user ? $user->user_login : '#' . $row->user_id,
				'last_used'   => $row->last_used ?: $row->created,
			);
		}
		return $out;
	}

	public function recently_connected( $window_seconds = 7 * DAY_IN_SECONDS ) {
		global $wpdb;
		$table = WPC_Plugin::instance()->table( 'tokens' );
		$count = (int) $wpdb->get_var(
			$wpdb->prepare(
				"SELECT COUNT(*) FROM {$table} WHERE last_used > %s OR created > %s", // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
				gmdate( 'Y-m-d H:i:s', time() - $window_seconds ),
				gmdate( 'Y-m-d H:i:s', time() - $window_seconds )
			)
		);
		return $count > 0 || get_transient( 'wpc_app_password_used' );
	}
}
