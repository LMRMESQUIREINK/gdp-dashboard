<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * "Does the page still load" checks, and private preview links for drafts
 * so Claude can show the owner (or itself) a page that isn't published yet.
 */
class WPC_Verify {

	const ERROR_SIGNATURES = array(
		'There has been a critical error',
		'Fatal error</b>',
		'Parse error</b>',
	);

	/**
	 * @return array{verified: bool|null, reason: string}
	 */
	public static function check_url( $url, $expect = '' ) {
		$response = wp_remote_get(
			$url,
			array(
				'timeout'   => 25,
				'sslverify' => false,
			)
		);

		if ( is_wp_error( $response ) ) {
			return array(
				'verified' => null,
				'reason'   => sprintf(
					/* translators: %s: the underlying HTTP error message. */
					__( 'The site could not load itself to check (%s). Some hosts block this; check the page manually.', 'wp-connect' ),
					$response->get_error_message()
				),
			);
		}

		$code = wp_remote_retrieve_response_code( $response );
		$body = wp_remote_retrieve_body( $response );

		if ( 200 !== (int) $code ) {
			return array(
				'verified' => false,
				/* translators: %d: HTTP status code. */
				'reason'   => sprintf( __( 'The page returned HTTP %d.', 'wp-connect' ), $code ),
			);
		}

		foreach ( self::ERROR_SIGNATURES as $signature ) {
			if ( false !== strpos( $body, $signature ) ) {
				return array(
					'verified' => false,
					'reason'   => __( 'The page shows a PHP error.', 'wp-connect' ),
				);
			}
		}

		if ( '' !== $expect && false === strpos( $body, $expect ) ) {
			return array(
				'verified' => false,
				'reason'   => __( 'The expected text was not found on the page.', 'wp-connect' ),
			);
		}

		return array(
			'verified' => true,
			'reason'   => '',
		);
	}

	/* ------------------------------------------------------------------ */
	/* Preview links                                                        */
	/* ------------------------------------------------------------------ */

	public static function preview_link( $post_id ) {
		$post = get_post( $post_id );
		if ( ! $post ) {
			return '';
		}

		$token = wp_generate_password( 24, false );
		set_transient( 'wpc_prev_' . $token, $post_id, HOUR_IN_SECONDS );

		if ( 'page' === $post->post_type ) {
			$args = array(
				'page_id'      => $post_id,
				'wpc_preview'  => $token,
			);
		} else {
			$args = array(
				'p'            => $post_id,
				'post_type'    => $post->post_type,
				'wpc_preview'  => $token,
			);
		}

		return add_query_arg( $args, home_url( '/' ) );
	}

	public static function boot() {
		add_filter( 'posts_results', array( __CLASS__, 'maybe_publish_preview' ), 10, 2 );
		add_filter( 'redirect_canonical', array( __CLASS__, 'maybe_disable_redirect' ) );
		add_action( 'send_headers', array( __CLASS__, 'maybe_noindex' ) );
	}

	private static function token() {
		if ( empty( $_GET['wpc_preview'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended
			return '';
		}
		// Deliberately NOT sanitize_key(): that lowercases the token and
		// breaks the transient lookup, since wp_generate_password() output
		// is case-sensitive.
		return preg_replace( '/[^A-Za-z0-9]/', '', wp_unslash( $_GET['wpc_preview'] ) ); // phpcs:ignore WordPress.Security.NonceVerification.Recommended
	}

	public static function is_preview_request() {
		return '' !== self::token();
	}

	public static function maybe_publish_preview( $posts, $query ) {
		$token = self::token();
		if ( '' === $token || ! $query->is_main_query() || 1 !== count( $posts ) ) {
			return $posts;
		}

		$post_id = get_transient( 'wpc_prev_' . $token );
		if ( ! $post_id || (int) $posts[0]->ID !== (int) $post_id ) {
			return $posts;
		}

		$posts[0]->post_status = 'publish';
		return $posts;
	}

	public static function maybe_disable_redirect( $redirect_url ) {
		return self::is_preview_request() ? false : $redirect_url;
	}

	public static function maybe_noindex() {
		if ( self::is_preview_request() && ! headers_sent() ) {
			header( 'X-Robots-Tag: noindex' );
		}
	}
}
