<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * The WP-Connect dashboard: one top-level admin page with tabs. Forms
 * post to admin-post.php?action=wpc_action&do=...; AJAX handlers cover
 * toggles, feedback and the agent poll.
 */
class WPC_Admin {

	private static $instance = null;
	const PAGE = 'wp-connect';

	public static function instance() {
		if ( null === self::$instance ) {
			self::$instance = new self();
		}
		return self::$instance;
	}

	public function boot() {
		add_action( 'admin_menu', array( $this, 'menu' ) );
		add_filter( 'plugin_action_links_' . plugin_basename( WPC_FILE ), array( $this, 'action_links' ) );
		add_action( 'admin_enqueue_scripts', array( $this, 'assets' ) );
		add_action( 'admin_post_wpc_action', array( $this, 'handle_post' ) );

		add_action( 'wp_ajax_wpc_toggle', array( $this, 'ajax_toggle' ) );
		add_action( 'wp_ajax_wpc_feedback', array( $this, 'ajax_feedback' ) );
		add_action( 'wp_ajax_wpc_poll', array( $this, 'ajax_poll' ) );
	}

	public function menu() {
		$badge = WPC_Abilities::pending_count() + WPC_Agent::instance()->waiting_count();
		$title = 'WP-Connect';
		if ( $badge > 0 ) {
			$title .= ' <span class="update-plugins count-' . $badge . '"><span class="plugin-count">' . $badge . '</span></span>';
		}

		$icon = 'data:image/svg+xml;base64,' . base64_encode(
			'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path fill="#a7aaad" d="M10 2a8 8 0 100 16 8 8 0 000-16zm0 2.2a5.8 5.8 0 015.8 5.8 5.8 5.8 0 01-11.6 0A5.8 5.8 0 0110 4.2zM6.5 12.5l7-4-7-4v8z"/></svg>'
		);

		add_menu_page( 'WP-Connect', $title, 'manage_options', self::PAGE, array( $this, 'render' ), $icon, 3 );
	}

	public function action_links( $links ) {
		array_unshift( $links, '<a href="' . esc_url( admin_url( 'admin.php?page=' . self::PAGE ) ) . '">' . esc_html__( 'Dashboard', 'wp-connect' ) . '</a>' );
		return $links;
	}

	public function assets( $hook ) {
		if ( 'toplevel_page_' . self::PAGE !== $hook ) {
			return;
		}
		wp_enqueue_style( 'wpc-admin', WPC_URL . 'assets/admin.css', array(), WPC_VERSION );
		wp_enqueue_script( 'wpc-admin', WPC_URL . 'assets/admin.js', array(), WPC_VERSION, true );
		wp_localize_script( 'wpc-admin', 'WPC', array( 'ajax' => admin_url( 'admin-ajax.php' ), 'nonce' => wp_create_nonce( 'wpc_ajax' ) ) );
	}

	private function current_tab() {
		$tab   = isset( $_GET['tab'] ) ? sanitize_key( $_GET['tab'] ) : 'overview'; // phpcs:ignore WordPress.Security.NonceVerification.Recommended
		$valid = array( 'overview', 'connect', 'abilities', 'skills', 'activity', 'agent', 'lessons', 'settings' );
		return in_array( $tab, $valid, true ) ? $tab : 'overview';
	}

	private function back_url() {
		return isset( $_SERVER['REQUEST_URI'] ) ? esc_url_raw( wp_unslash( $_SERVER['REQUEST_URI'] ) ) : admin_url( 'admin.php?page=' . self::PAGE );
	}

	private function notice( $message, $type = 'ok' ) {
		set_transient( 'wpc_notice_' . get_current_user_id(), array( 'message' => $message, 'type' => $type ), 60 );
	}

	/* ------------------------------------------------------------------ */
	/* Render                                                               */
	/* ------------------------------------------------------------------ */

	public function render() {
		$tab = $this->current_tab();
		?>
		<div class="wrap wpc">
			<?php $this->render_header(); ?>
			<nav class="wpc-tabs">
				<?php
				$tabs = array(
					'overview'  => __( 'Overview', 'wp-connect' ),
					'connect'   => __( 'Connect', 'wp-connect' ),
					'abilities' => __( 'Abilities', 'wp-connect' ),
					'skills'    => __( 'Skills', 'wp-connect' ),
					'activity'  => __( 'Activity', 'wp-connect' ),
					'agent'     => __( 'AI Agent', 'wp-connect' ),
					'lessons'   => __( 'Lessons', 'wp-connect' ),
					'settings'  => __( 'Settings', 'wp-connect' ),
				);
				foreach ( $tabs as $key => $label ) {
					$class = 'overview' === $key && 'overview' === $tab ? 'is-active' : ( $key === $tab ? 'is-active' : '' );
					$badge = '';
					if ( 'abilities' === $key && WPC_Abilities::pending_count() > 0 ) {
						$badge = '<em>' . WPC_Abilities::pending_count() . '</em>';
					}
					if ( 'agent' === $key && WPC_Agent::instance()->waiting_count() > 0 ) {
						$badge = '<em>' . WPC_Agent::instance()->waiting_count() . '</em>';
					}
					printf(
						'<a class="%1$s" href="%2$s">%3$s%4$s</a>',
						esc_attr( $class ),
						esc_url( admin_url( 'admin.php?page=' . self::PAGE . '&tab=' . $key ) ),
						esc_html( $label ),
						wp_kses_post( $badge )
					);
				}
				?>
			</nav>
			<?php $this->render_toast(); ?>
			<div class="wpc-main">
				<?php
				$method = 'tab_' . $tab;
				$this->$method();
				?>
			</div>
		</div>
		<?php
	}

	private function render_header() {
		$mode       = WPC_Plugin::instance()->mode();
		$mode_class = 'is-' . $mode;
		$connected  = WPC_OAuth::instance()->recently_connected();
		?>
		<div class="wpc-top">
			<div class="wpc-brand">
				<div class="wpc-mark"></div>
				<div>
					<strong>WP-Connect</strong>
					<small><?php echo esc_html( get_bloginfo( 'name' ) ); ?></small>
				</div>
			</div>
			<div class="wpc-top-pills">
				<span class="wpc-pill <?php echo esc_attr( $mode_class ); ?>"><?php echo esc_html( WPC_Plugin::instance()->mode_label( $mode ) ); ?> mode</span>
				<span class="wpc-pill <?php echo $connected ? 'is-on' : ''; ?>"><i></i><?php echo $connected ? esc_html__( 'Claude connected', 'wp-connect' ) : esc_html__( 'Not connected yet', 'wp-connect' ); ?></span>
			</div>
		</div>
		<?php
	}

	private function render_toast() {
		$notice = get_transient( 'wpc_notice_' . get_current_user_id() );
		if ( ! $notice ) {
			return;
		}
		delete_transient( 'wpc_notice_' . get_current_user_id() );
		printf( '<div class="wpc-toast %s">%s</div>', 'warn' === $notice['type'] ? 'is-warn' : '', esc_html( $notice['message'] ) );
	}

	/* ------------------------------------------------------------------ */
	/* Overview                                                             */
	/* ------------------------------------------------------------------ */

	private function tab_overview() {
		$mode = WPC_Plugin::instance()->mode();
		?>
		<section class="wpc-section">
			<div class="wpc-section-head">
				<h2><?php esc_html_e( 'How much can Claude do?', 'wp-connect' ); ?></h2>
				<p><?php esc_html_e( 'Pick a mode. You can change it any time.', 'wp-connect' ); ?></p>
			</div>
			<div class="wpc-modes">
				<?php $this->render_mode_card( 'full', $mode ); ?>
				<?php $this->render_mode_card( 'abilities', $mode ); ?>
				<?php $this->render_mode_card( 'agent', $mode ); ?>
			</div>
		</section>

		<?php $this->render_stats(); ?>

		<section class="wpc-grid-2">
			<div class="wpc-card">
				<div class="wpc-card-head">
					<h3><?php esc_html_e( 'Recent activity', 'wp-connect' ); ?></h3>
					<a href="<?php echo esc_url( admin_url( 'admin.php?page=' . self::PAGE . '&tab=activity' ) ); ?>"><?php esc_html_e( 'See all', 'wp-connect' ); ?></a>
				</div>
				<?php $this->render_run_list( $this->recent_runs( 8 ), false ); ?>
			</div>
			<div class="wpc-card">
				<h3><?php esc_html_e( 'Needs attention', 'wp-connect' ); ?></h3>
				<?php $this->render_attention_list(); ?>
			</div>
		</section>
		<?php
	}

	private function render_mode_card( $mode, $current ) {
		$meta = array(
			'full'      => array( 'icon' => 'dashicons-unlock', 'title' => __( 'Full Access', 'wp-connect' ), 'desc' => __( 'Claude can do anything on the site, including running code. Fastest, but nothing stops a bad command. Code runs are logged but can\'t be undone.', 'wp-connect' ) ),
			'abilities' => array( 'icon' => 'dashicons-shield', 'title' => __( 'Abilities', 'wp-connect' ), 'desc' => __( 'Claude can only use the abilities you switch on. Every change is backed up with one-click undo. Best for most sites.', 'wp-connect' ) ),
			'agent'     => array( 'icon' => 'dashicons-superhero', 'title' => __( 'AI Agent', 'wp-connect' ), 'desc' => __( 'Everything in Abilities, plus the plugin runs jobs on its own with your Anthropic API key, no chat needed. Risky steps wait for your OK.', 'wp-connect' ) ),
		);
		$m      = $meta[ $mode ];
		$needs_key = 'agent' === $mode && '' === WPC_Plugin::instance()->api_key();
		?>
		<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" class="wpc-mode is-<?php echo esc_attr( $mode ); ?> <?php echo $mode === $current ? 'is-current' : ''; ?>" <?php echo 'full' === $mode ? 'data-confirm="' . esc_attr__( 'Full Access lets Claude run any code on your site. Only turn this on if you trust what you ask it to do. Continue?', 'wp-connect' ) . '"' : ''; ?>>
			<input type="hidden" name="action" value="wpc_action">
			<input type="hidden" name="do" value="set_mode">
			<input type="hidden" name="mode" value="<?php echo esc_attr( $mode ); ?>">
			<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>">
			<?php wp_nonce_field( 'wpc_admin' ); ?>
			<?php if ( $needs_key ) : ?><span class="wpc-mode-need"><?php esc_html_e( 'Needs an API key', 'wp-connect' ); ?></span><?php endif; ?>
			<div class="wpc-mode-icon"><span class="dashicons <?php echo esc_attr( $m['icon'] ); ?>"></span></div>
			<h3><?php echo esc_html( $m['title'] ); ?></h3>
			<p><?php echo esc_html( $m['desc'] ); ?></p>
			<?php if ( $mode === $current ) : ?>
				<span class="wpc-mode-on"><?php esc_html_e( 'Current mode', 'wp-connect' ); ?></span>
			<?php else : ?>
				<button type="submit" class="wpc-btn is-ghost"><?php echo esc_html( sprintf( __( 'Switch to %s', 'wp-connect' ), $m['title'] ) ); ?></button>
			<?php endif; ?>
		</form>
		<?php
	}

	private function render_stats() {
		$all          = WPC_Abilities::all();
		$on           = count( WPC_Abilities::usable_names() );
		$scores       = array();
		foreach ( $all as $name => $a ) {
			$r = WPC_Abilities::rating( $name );
			if ( null !== $r['score'] ) {
				$scores[] = $r['score'];
			}
		}
		$avg = $scores ? round( array_sum( $scores ) / count( $scores ) ) : 0;

		global $wpdb;
		$runs_table = WPC_Plugin::instance()->table( 'runs' );
		$week_ago   = gmdate( 'Y-m-d H:i:s', time() - WEEK_IN_SECONDS );
		$actions    = (int) $wpdb->get_var( $wpdb->prepare( "SELECT COUNT(*) FROM {$runs_table} WHERE created > %s", $week_ago ) ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
		$successes  = (int) $wpdb->get_var( $wpdb->prepare( "SELECT COUNT(*) FROM {$runs_table} WHERE created > %s AND success = 1", $week_ago ) ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
		$success_pct = $actions > 0 ? round( ( $successes / $actions ) * 100 ) : 0;
		?>
		<section class="wpc-stats">
			<div class="wpc-stat"><span><?php esc_html_e( 'Abilities on', 'wp-connect' ); ?></span><strong><?php echo esc_html( $on . '/' . count( $all ) ); ?></strong></div>
			<div class="wpc-stat"><span><?php esc_html_e( 'Average rating', 'wp-connect' ); ?></span><strong><?php echo esc_html( $avg ); ?><small>/100</small></strong></div>
			<div class="wpc-stat"><span><?php esc_html_e( 'Actions this week', 'wp-connect' ); ?></span><strong><?php echo esc_html( $actions ); ?></strong></div>
			<div class="wpc-stat"><span><?php esc_html_e( 'Success this week', 'wp-connect' ); ?></span><strong><?php echo esc_html( $success_pct ); ?><small>%</small></strong></div>
		</section>
		<?php
	}

	private function render_attention_list() {
		$items = array();

		foreach ( WPC_Abilities::pending_rows() as $row ) {
			$items[] = array( 'badge' => __( 'Review', 'wp-connect' ), 'text' => sprintf( __( 'Review new ability: %s', 'wp-connect' ), $row->label ), 'url' => admin_url( 'admin.php?page=' . self::PAGE . '&tab=abilities#pending' ) );
		}
		if ( WPC_Agent::instance()->waiting_count() > 0 ) {
			$items[] = array( 'badge' => __( 'Agent', 'wp-connect' ), 'text' => __( 'Agent needs your OK', 'wp-connect' ), 'url' => admin_url( 'admin.php?page=' . self::PAGE . '&tab=agent' ) );
		}
		foreach ( WPC_Abilities::all() as $name => $a ) {
			$r = WPC_Abilities::rating( $name );
			if ( null !== $r['score'] && $r['score'] < 60 ) {
				$items[] = array( 'badge' => __( 'Low rating', 'wp-connect' ), 'text' => sprintf( __( 'Low rating %1$d: %2$s', 'wp-connect' ), $r['score'], $a['label'] ), 'url' => admin_url( 'admin.php?page=' . self::PAGE . '&tab=abilities&ability=' . $name ) );
			}
		}
		if ( ! WPC_OAuth::instance()->recently_connected() ) {
			$items[] = array( 'badge' => __( 'Connect', 'wp-connect' ), 'text' => __( 'Connect Claude - Takes about a minute', 'wp-connect' ), 'url' => admin_url( 'admin.php?page=' . self::PAGE . '&tab=connect' ) );
		}

		if ( empty( $items ) ) {
			echo '<p class="wpc-empty">' . esc_html__( 'All good. Nothing needs you right now.', 'wp-connect' ) . '</p>';
			return;
		}

		echo '<ul class="wpc-attn">';
		foreach ( $items as $item ) {
			printf( '<li><a href="%1$s"><b>%2$s</b>%3$s</a></li>', esc_url( $item['url'] ), esc_html( $item['badge'] ), esc_html( $item['text'] ) );
		}
		echo '</ul>';
	}

	/* ------------------------------------------------------------------ */
	/* Connect                                                              */
	/* ------------------------------------------------------------------ */

	private function tab_connect() {
		$mcp_url = WPC_OAuth::instance()->mcp_url();
		?>
		<div class="wpc-card">
			<h3><?php esc_html_e( 'Connect Claude (claude.ai, desktop, mobile)', 'wp-connect' ); ?></h3>
			<div class="wpc-copy"><code><?php echo esc_html( $mcp_url ); ?></code><button type="button" class="wpc-btn is-small is-ghost" data-copy="<?php echo esc_attr( $mcp_url ); ?>"><?php esc_html_e( 'Copy', 'wp-connect' ); ?></button></div>
			<ol class="wpc-steps">
				<li><?php esc_html_e( 'Open Settings -> Connectors and choose Add custom connector.', 'wp-connect' ); ?></li>
				<li><?php esc_html_e( 'Name it and paste the address above.', 'wp-connect' ); ?></li>
				<li><?php esc_html_e( "Click Connect and you'll be sent here to log in and click Allow.", 'wp-connect' ); ?></li>
				<li><?php esc_html_e( 'Start a chat and ask Claude to "check my site".', 'wp-connect' ); ?></li>
			</ol>
			<p class="wpc-muted"><?php esc_html_e( 'Only administrators can connect. No API key is needed for this; it uses your Claude plan.', 'wp-connect' ); ?></p>
		</div>

		<div class="wpc-card" id="app-password">
			<h3><?php esc_html_e( 'Claude Code or a config file', 'wp-connect' ); ?></h3>
			<?php $this->render_app_password_tool( $mcp_url ); ?>
		</div>

		<div class="wpc-card">
			<h3><?php esc_html_e( 'Connected apps', 'wp-connect' ); ?></h3>
			<?php $apps = WPC_OAuth::instance()->connected_apps(); ?>
			<?php if ( empty( $apps ) ) : ?>
				<p class="wpc-empty"><?php esc_html_e( 'Nothing connected yet.', 'wp-connect' ); ?></p>
			<?php else : ?>
				<table class="wpc-table">
					<thead><tr><th><?php esc_html_e( 'App', 'wp-connect' ); ?></th><th><?php esc_html_e( 'Connected as', 'wp-connect' ); ?></th><th><?php esc_html_e( 'Last used', 'wp-connect' ); ?></th></tr></thead>
					<tbody>
					<?php foreach ( $apps as $app ) : ?>
						<tr><td><?php echo esc_html( $app['client_name'] ); ?></td><td><?php echo esc_html( $app['user'] ); ?></td><td><?php echo esc_html( human_time_diff( strtotime( $app['last_used'] ) ) . ' ago' ); ?></td></tr>
					<?php endforeach; ?>
					</tbody>
				</table>
			<?php endif; ?>
			<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" class="wpc-actions" data-confirm="<?php esc_attr_e( 'Disconnect every connected app?', 'wp-connect' ); ?>">
				<input type="hidden" name="action" value="wpc_action">
				<input type="hidden" name="do" value="disconnect_all">
				<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>">
				<?php wp_nonce_field( 'wpc_admin' ); ?>
				<button type="submit" class="wpc-btn is-danger"><?php esc_html_e( 'Disconnect all', 'wp-connect' ); ?></button>
			</form>
		</div>

		<div class="wpc-card" id="test">
			<h3><?php esc_html_e( 'Connection test', 'wp-connect' ); ?></h3>
			<?php $this->render_connection_test(); ?>
		</div>
		<?php
	}

	private function render_app_password_tool( $mcp_url ) {
		if ( ! empty( $_GET['wpc_new_app_password'] ) ) { // phpcs:ignore WordPress.Security.NonceVerification.Recommended
			$password = get_transient( 'wpc_shown_app_password_' . get_current_user_id() );
			delete_transient( 'wpc_shown_app_password_' . get_current_user_id() );
			if ( $password ) {
				$auth = base64_encode( wp_get_current_user()->user_login . ':' . $password );
				?>
				<div class="wpc-callout"><?php esc_html_e( "Copy this now. It won't be shown again.", 'wp-connect' ); ?></div>
				<div class="wpc-code">claude mcp add --transport http wp-connect <?php echo esc_html( $mcp_url ); ?> --header "Authorization: Basic <?php echo esc_html( $auth ); ?>"</div>
				<p class="wpc-muted"><?php esc_html_e( 'Raw header:', 'wp-connect' ); ?> <code>Authorization: Basic <?php echo esc_html( $auth ); ?></code></p>
				<?php
			}
		}
		?>
		<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
			<input type="hidden" name="action" value="wpc_action">
			<input type="hidden" name="do" value="create_app_password">
			<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>">
			<?php wp_nonce_field( 'wpc_admin' ); ?>
			<button type="submit" class="wpc-btn"><?php esc_html_e( 'Create application password', 'wp-connect' ); ?></button>
		</form>
		<?php
	}

	private function render_connection_test() {
		?>
		<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
			<input type="hidden" name="action" value="wpc_action">
			<input type="hidden" name="do" value="connection_test">
			<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>#test">
			<?php wp_nonce_field( 'wpc_admin' ); ?>
			<button type="submit" class="wpc-btn is-ghost"><?php esc_html_e( 'Run test', 'wp-connect' ); ?></button>
		</form>
		<?php
		$results = get_transient( 'wpc_test_results_' . get_current_user_id() );
		if ( $results ) {
			echo '<ul class="wpc-checks">';
			foreach ( $results as $r ) {
				printf( '<li class="%1$s"><b>%2$s</b>%3$s</li>', $r['ok'] ? 'is-ok' : 'is-bad', esc_html( $r['title'] ), esc_html( $r['detail'] ) );
			}
			echo '</ul>';
		}
	}

	/* ------------------------------------------------------------------ */
	/* Abilities                                                            */
	/* ------------------------------------------------------------------ */

	private function tab_abilities() {
		$pending = WPC_Abilities::pending_rows();
		if ( ! empty( $pending ) ) {
			$this->render_pending_abilities( $pending );
		}
		?>
		<section class="wpc-section">
			<div class="wpc-section-head wpc-section-head--row">
				<div>
					<h2><?php esc_html_e( 'Abilities', 'wp-connect' ); ?></h2>
					<p><?php esc_html_e( 'Each ability is one thing Claude can do on your site. Ratings come from real use: whether it worked, whether the page checked out afterwards, and your thumbs up or down on the Activity tab.', 'wp-connect' ); ?></p>
				</div>
				<input type="search" class="wpc-search" data-filter-input placeholder="<?php esc_attr_e( 'Search abilities', 'wp-connect' ); ?>">
			</div>
			<div class="wpc-chips">
				<button type="button" class="wpc-chip is-active" data-filter="all"><?php esc_html_e( 'All', 'wp-connect' ); ?></button>
				<?php foreach ( WPC_Abilities::$categories as $key => $cat ) : ?>
					<button type="button" class="wpc-chip" data-filter="<?php echo esc_attr( $key ); ?>"><?php echo esc_html( $cat['label'] ); ?></button>
				<?php endforeach; ?>
			</div>
			<div class="wpc-abilities">
				<?php foreach ( WPC_Abilities::all() as $name => $ability ) : ?>
					<?php $this->render_ability_card( $name, $ability ); ?>
				<?php endforeach; ?>
			</div>
			<div class="wpc-card wpc-tipbox">
				<p class="wpc-inline"><?php esc_html_e( 'Want a new ability? Ask Claude in chat, e.g. "Write an ability that lists my scheduled posts." It writes the code, and it shows up at the top of this page for you to approve.', 'wp-connect' ); ?></p>
			</div>
		</section>
		<?php
	}

	private function render_pending_abilities( $pending ) {
		?>
		<section class="wpc-section" id="pending">
			<h2><?php esc_html_e( 'Waiting for review', 'wp-connect' ); ?></h2>
			<p><?php esc_html_e( 'Claude wrote these. Nothing runs until you approve it. Read the code, or ask Claude in chat to explain it.', 'wp-connect' ); ?></p>
			<?php foreach ( $pending as $row ) : ?>
				<?php $current = WPC_Abilities::get( $row->name ); ?>
				<div class="wpc-card wpc-review">
					<div class="wpc-review-head">
						<div>
							<span class="wpc-badge"><?php echo 1 === (int) $row->version ? esc_html__( 'New ability', 'wp-connect' ) : esc_html( sprintf( __( 'New version %d', 'wp-connect' ), $row->version ) ); ?></span>
							<h3><?php echo esc_html( $row->label ); ?></h3>
							<code><?php echo esc_html( $row->name ); ?></code>
						</div>
						<div class="wpc-review-flags">
							<?php if ( $row->writes ) : ?><span class="wpc-badge is-writes"><?php esc_html_e( 'Changes the site', 'wp-connect' ); ?></span><?php endif; ?>
							<?php if ( $row->risky ) : ?><span class="wpc-badge is-risky"><?php esc_html_e( 'Risky', 'wp-connect' ); ?></span><?php endif; ?>
						</div>
					</div>
					<p><?php echo esc_html( $row->description ); ?></p>
					<?php if ( $row->change_note ) : ?><p class="wpc-muted"><?php esc_html_e( 'What changed:', 'wp-connect' ); ?> <?php echo esc_html( $row->change_note ); ?></p><?php endif; ?>
					<details>
						<summary><?php esc_html_e( 'Code', 'wp-connect' ); ?></summary>
						<pre class="wpc-code"><?php echo esc_html( $row->code ); ?></pre>
					</details>
					<?php if ( $current && isset( $current['_version'] ) ) : ?>
						<?php $live = WPC_Abilities::custom_row( null ); ?>
						<details>
							<summary><?php esc_html_e( 'Current live version, for comparison', 'wp-connect' ); ?></summary>
							<pre class="wpc-code"><?php echo esc_html( get_post_meta( 0, '', true ) ); ?></pre>
						</details>
					<?php endif; ?>
					<div class="wpc-actions">
						<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
							<input type="hidden" name="action" value="wpc_action">
							<input type="hidden" name="do" value="ability_reject">
							<input type="hidden" name="id" value="<?php echo esc_attr( $row->id ); ?>">
							<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>#pending">
							<?php wp_nonce_field( 'wpc_admin' ); ?>
							<button type="submit" class="wpc-btn is-ghost"><?php esc_html_e( 'Reject', 'wp-connect' ); ?></button>
						</form>
						<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" data-confirm="<?php esc_attr_e( 'Approve this code? It will run on your site whenever Claude uses this ability.', 'wp-connect' ); ?>">
							<input type="hidden" name="action" value="wpc_action">
							<input type="hidden" name="do" value="ability_approve">
							<input type="hidden" name="id" value="<?php echo esc_attr( $row->id ); ?>">
							<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>#pending">
							<?php wp_nonce_field( 'wpc_admin' ); ?>
							<button type="submit" class="wpc-btn"><?php esc_html_e( 'Approve & go live', 'wp-connect' ); ?></button>
						</form>
					</div>
				</div>
			<?php endforeach; ?>
		</section>
		<?php
	}

	private function render_ability_card( $name, $ability ) {
		$rating   = WPC_Abilities::rating( $name );
		$usable   = WPC_Abilities::is_usable( $name );
		$disabled = WPC_Abilities::is_disabled( $name );
		$tuning   = WPC_Abilities::tuning( $name );
		$lessons  = WPC_Abilities::lessons( $name );

		$ring_class = 'is-new';
		if ( null !== $rating['score'] ) {
			$ring_class = $rating['score'] >= 75 ? 'is-good' : ( $rating['score'] >= 50 ? 'is-mid' : 'is-bad' );
		}
		$circumference = 2 * M_PI * 16;
		$offset        = null === $rating['score'] ? $circumference : $circumference * ( 1 - $rating['score'] / 100 );
		?>
		<div class="wpc-ability <?php echo $usable ? '' : 'is-dim'; ?>" id="ability-<?php echo esc_attr( $name ); ?>" data-cat="<?php echo esc_attr( $ability['category'] ); ?>" data-search="<?php echo esc_attr( strtolower( $name . ' ' . $ability['label'] ) ); ?>">
			<div class="wpc-ability-top">
				<div class="wpc-ability-icon"><span class="dashicons <?php echo esc_attr( WPC_Abilities::$categories[ $ability['category'] ]['icon'] ); ?>"></span></div>
				<div class="wpc-ability-title">
					<strong><?php echo esc_html( $ability['label'] ); ?></strong>
					<code><?php echo esc_html( $name ); ?><?php echo isset( $ability['_version'] ) ? esc_html( ' · v' . $ability['_version'] ) : ''; ?></code>
				</div>
				<?php if ( empty( $ability['locked'] ) ) : ?>
					<label class="wpc-switch">
						<input type="checkbox" data-toggle="<?php echo esc_attr( $name ); ?>" <?php checked( ! $disabled ); ?>>
						<span></span>
					</label>
				<?php else : ?>
					<span class="wpc-muted"><?php esc_html_e( 'Always on', 'wp-connect' ); ?></span>
				<?php endif; ?>
			</div>
			<p class="wpc-ability-desc"><?php echo esc_html( $ability['description'] ); ?></p>
			<div class="wpc-ability-score">
				<div class="wpc-ring <?php echo esc_attr( $ring_class ); ?>" style="width:40px;height:40px;">
					<svg width="40" height="40"><circle class="wpc-ring-bg" cx="20" cy="20" r="16"></circle><circle class="wpc-ring-fg" cx="20" cy="20" r="16" style="stroke-dasharray:<?php echo esc_attr( $circumference ); ?>;stroke-dashoffset:<?php echo esc_attr( $offset ); ?>"></circle></svg>
					<span><?php echo null === $rating['score'] ? '' : esc_html( $rating['score'] ); ?></span>
				</div>
				<div>
					<strong><?php echo null === $rating['score'] ? esc_html__( 'New', 'wp-connect' ) : esc_html( $rating['label'] ); ?></strong>
					<span><?php echo $rating['runs'] > 0 ? esc_html( sprintf( __( '%1$d runs · %2$d%% worked', 'wp-connect' ), $rating['runs'], $rating['success_rate'] ) ) : esc_html__( 'Not used yet', 'wp-connect' ); ?></span>
				</div>
			</div>
			<div class="wpc-badges">
				<?php if ( ! empty( $ability['writes'] ) ) : ?><span class="wpc-badge is-writes"><?php esc_html_e( 'Changes the site', 'wp-connect' ); ?></span><?php endif; ?>
				<?php if ( ! empty( $ability['risky'] ) ) : ?><span class="wpc-badge is-risky"><?php esc_html_e( 'Risky', 'wp-connect' ); ?></span><?php endif; ?>
				<?php if ( 'custom' === $ability['category'] ) : ?><span class="wpc-badge is-custom"><?php esc_html_e( 'Written by Claude', 'wp-connect' ); ?></span><?php endif; ?>
				<?php if ( 'full_access' === $ability['category'] ) : ?><span class="wpc-badge"><?php esc_html_e( 'Full Access mode only', 'wp-connect' ); ?></span><?php endif; ?>
				<?php if ( $lessons ) : ?><span class="wpc-badge is-lesson"><?php echo esc_html( sprintf( __( '%d lessons', 'wp-connect' ), count( $lessons ) ) ); ?></span><?php endif; ?>
				<?php if ( '' !== trim( (string) $tuning['notes'] ) ) : ?><span class="wpc-badge is-tuned"><?php esc_html_e( 'Fine-tuned', 'wp-connect' ); ?></span><?php endif; ?>
			</div>
			<details class="wpc-tune">
				<summary><?php esc_html_e( 'Fine-tune', 'wp-connect' ); ?></summary>
				<?php if ( $rating['last_error'] ) : ?><div class="wpc-callout is-warn"><?php echo esc_html( $rating['last_error'] ); ?></div><?php endif; ?>
				<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
					<input type="hidden" name="action" value="wpc_action">
					<input type="hidden" name="do" value="save_tuning">
					<input type="hidden" name="name" value="<?php echo esc_attr( $name ); ?>">
					<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>#ability-<?php echo esc_attr( $name ); ?>">
					<?php wp_nonce_field( 'wpc_admin' ); ?>
					<label class="wpc-label"><?php esc_html_e( 'Your instructions for Claude', 'wp-connect' ); ?></label>
					<textarea name="notes" rows="2" placeholder="<?php esc_attr_e( 'e.g. Always use our brand red #E11D48 for buttons. Never touch the homepage.', 'wp-connect' ); ?>"><?php echo esc_textarea( $tuning['notes'] ); ?></textarea>
					<label class="wpc-label"><?php esc_html_e( 'In AI Agent mode, ask me before running it', 'wp-connect' ); ?></label>
					<select name="needs_approval">
						<option value="" <?php selected( null, $tuning['needs_approval'] ); ?>><?php esc_html_e( 'Default (ask / don\'t ask)', 'wp-connect' ); ?></option>
						<option value="1" <?php selected( true, $tuning['needs_approval'] ); ?>><?php esc_html_e( 'Always ask me', 'wp-connect' ); ?></option>
						<option value="0" <?php selected( false, $tuning['needs_approval'] ); ?>><?php esc_html_e( 'Never ask', 'wp-connect' ); ?></option>
					</select>
					<div class="wpc-actions"><button type="submit" class="wpc-btn is-small"><?php esc_html_e( 'Save', 'wp-connect' ); ?></button></div>
				</form>
				<?php if ( $lessons ) : ?>
					<p class="wpc-label"><?php esc_html_e( 'Lessons Claude has learned', 'wp-connect' ); ?></p>
					<ul class="wpc-lessons-mini">
						<?php foreach ( $lessons as $lesson ) : ?><li><?php echo esc_html( $lesson->lesson ); ?></li><?php endforeach; ?>
					</ul>
					<a class="wpc-link" href="<?php echo esc_url( admin_url( 'admin.php?page=' . self::PAGE . '&tab=lessons#topic-' . $name ) ); ?>"><?php esc_html_e( 'Edit lessons', 'wp-connect' ); ?></a>
				<?php endif; ?>
				<?php if ( 'custom' === $ability['category'] ) : ?>
					<p class="wpc-label"><?php esc_html_e( 'Versions', 'wp-connect' ); ?></p>
					<ul class="wpc-versions">
						<?php foreach ( WPC_Abilities::custom_versions( $name ) as $v ) : ?>
							<li>
								<span>v<?php echo esc_html( $v->version ); ?></span>
								<?php if ( 'active' === $v->status ) : ?><span class="wpc-badge is-on"><?php esc_html_e( 'Live', 'wp-connect' ); ?></span><?php else : ?>
									<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
										<input type="hidden" name="action" value="wpc_action">
										<input type="hidden" name="do" value="ability_restore">
										<input type="hidden" name="id" value="<?php echo esc_attr( $v->id ); ?>">
										<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>">
										<?php wp_nonce_field( 'wpc_admin' ); ?>
										<button type="submit" class="wpc-btn is-small is-ghost"><?php esc_html_e( 'Roll back to this', 'wp-connect' ); ?></button>
									</form>
								<?php endif; ?>
							</li>
						<?php endforeach; ?>
					</ul>
					<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" data-confirm="<?php esc_attr_e( 'Delete this ability?', 'wp-connect' ); ?>">
						<input type="hidden" name="action" value="wpc_action">
						<input type="hidden" name="do" value="ability_delete">
						<input type="hidden" name="name" value="<?php echo esc_attr( $name ); ?>">
						<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>">
						<?php wp_nonce_field( 'wpc_admin' ); ?>
						<button type="submit" class="wpc-btn is-danger is-small"><?php esc_html_e( 'Delete ability', 'wp-connect' ); ?></button>
					</form>
				<?php endif; ?>
				<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" data-confirm="<?php esc_attr_e( 'Reset this rating?', 'wp-connect' ); ?>">
					<input type="hidden" name="action" value="wpc_action">
					<input type="hidden" name="do" value="reset_rating">
					<input type="hidden" name="name" value="<?php echo esc_attr( $name ); ?>">
					<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>">
					<?php wp_nonce_field( 'wpc_admin' ); ?>
					<button type="submit" class="wpc-btn is-small is-ghost"><?php esc_html_e( 'Reset rating', 'wp-connect' ); ?></button>
				</form>
			</details>
		</div>
		<?php
	}

	/* ------------------------------------------------------------------ */
	/* Skills                                                               */
	/* ------------------------------------------------------------------ */

	private function tab_skills() {
		?>
		<section class="wpc-section">
			<h2><?php esc_html_e( 'Skills', 'wp-connect' ); ?></h2>
			<p><?php esc_html_e( 'Abilities are single things Claude can do. Skills are whole jobs: a saved, step-by-step plan that tells Claude which abilities to use, in what order, and what to report. Run one by asking Claude in chat, from Claude\'s prompt menu, or here with AI Agent mode.', 'wp-connect' ); ?></p>
			<?php foreach ( WPC_Skills::all_slugs() as $slug ) : ?>
				<?php $this->render_skill_card( $slug ); ?>
			<?php endforeach; ?>
			<details class="wpc-card wpc-new-skill">
				<summary><?php esc_html_e( 'Create a skill', 'wp-connect' ); ?> <span class="wpc-muted"><?php esc_html_e( 'or ask Claude: "Turn what you just did into a skill."', 'wp-connect' ); ?></span></summary>
				<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
					<input type="hidden" name="action" value="wpc_action">
					<input type="hidden" name="do" value="skill_save">
					<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>">
					<?php wp_nonce_field( 'wpc_admin' ); ?>
					<label class="wpc-label"><?php esc_html_e( 'Name', 'wp-connect' ); ?></label>
					<input type="text" name="skill_slug" required>
					<label class="wpc-label"><?php esc_html_e( 'What it does', 'wp-connect' ); ?></label>
					<input type="text" name="description" required>
					<label class="wpc-label"><?php esc_html_e( 'Steps for Claude', 'wp-connect' ); ?></label>
					<textarea name="instructions" rows="6" required></textarea>
					<div class="wpc-actions"><button type="submit" class="wpc-btn"><?php esc_html_e( 'Save skill', 'wp-connect' ); ?></button></div>
				</form>
			</details>
		</section>
		<?php
	}

	private function render_skill_card( $slug ) {
		$meta   = WPC_Skills::meta( $slug );
		if ( ! $meta ) {
			return;
		}
		$fix_mode = WPC_Skills::fix_mode( $slug );
		$health   = WPC_Skills::health( $slug );
		$report   = WPC_Skills::last_report( $slug );
		$agent_on = 'agent' === WPC_Plugin::instance()->mode();
		?>
		<div class="wpc-card wpc-skill">
			<div class="wpc-skill-head">
				<div class="wpc-skill-icon"><span class="dashicons <?php echo esc_attr( $meta['icon'] ); ?>"></span></div>
				<div class="wpc-skill-title">
					<h3><?php echo esc_html( $meta['title'] ); ?></h3>
					<code><?php echo esc_html( $slug ); ?></code>
					<?php if ( ! empty( $meta['is_builtin'] ) ) : ?>
						<?php if ( WPC_Skills::is_overridden( $slug ) ) : ?><span class="wpc-badge">Edited</span><?php endif; ?>
					<?php else : ?>
						<span class="wpc-badge is-custom"><?php echo 'claude' === $meta['author'] ? esc_html__( 'Written by Claude', 'wp-connect' ) : esc_html__( 'Your skill', 'wp-connect' ); ?></span>
					<?php endif; ?>
				</div>
				<div class="wpc-skill-health">
					<?php if ( null !== $health ) : ?>
						<strong><?php echo esc_html( $health ); ?>/100</strong> <span class="wpc-muted"><?php esc_html_e( 'Skill health - average rating of the abilities it uses', 'wp-connect' ); ?></span>
					<?php endif; ?>
				</div>
			</div>
			<p><?php echo esc_html( $meta['description'] ); ?></p>
			<p><strong><?php esc_html_e( 'Abilities it uses', 'wp-connect' ); ?>:</strong>
				<?php foreach ( (array) $meta['abilities'] as $ability_name ) : ?>
					<?php $on = WPC_Abilities::is_usable( $ability_name ); ?>
					<a class="wpc-badge <?php echo $on ? 'is-on' : ''; ?>" href="<?php echo esc_url( admin_url( 'admin.php?page=' . self::PAGE . '&tab=abilities&ability=' . $ability_name ) ); ?>"><?php echo esc_html( $ability_name ); ?><?php echo $on ? '' : esc_html__( ' (off)', 'wp-connect' ); ?></a>
				<?php endforeach; ?>
			</p>
			<div class="wpc-skill-run">
				<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
					<input type="hidden" name="action" value="wpc_action">
					<input type="hidden" name="do" value="skill_fix_mode">
					<input type="hidden" name="skill" value="<?php echo esc_attr( $slug ); ?>">
					<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>">
					<?php wp_nonce_field( 'wpc_admin' ); ?>
					<label class="wpc-label"><?php esc_html_e( 'How much can it change?', 'wp-connect' ); ?></label>
					<div class="wpc-row">
						<select name="fix_mode">
							<?php foreach ( WPC_Skills::FIX_MODES as $k => $label ) : ?>
								<option value="<?php echo esc_attr( $k ); ?>" <?php selected( $fix_mode, $k ); ?>><?php echo esc_html( $label ); ?></option>
							<?php endforeach; ?>
						</select>
						<button type="submit" class="wpc-btn is-small is-ghost"><?php esc_html_e( 'Save', 'wp-connect' ); ?></button>
					</div>
				</form>
				<div>
					<label class="wpc-label"><?php esc_html_e( 'Run it in Claude chat', 'wp-connect' ); ?></label>
					<div class="wpc-copy"><code><?php echo esc_html( sprintf( __( 'Run the %s skill on my site.', 'wp-connect' ), $slug ) ); ?></code><button type="button" class="wpc-btn is-small is-ghost" data-copy="<?php echo esc_attr( sprintf( __( 'Run the %s skill on my site.', 'wp-connect' ), $slug ) ); ?>"><?php esc_html_e( 'Copy', 'wp-connect' ); ?></button></div>
				</div>
				<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
					<input type="hidden" name="action" value="wpc_action">
					<input type="hidden" name="do" value="skill_run">
					<input type="hidden" name="skill" value="<?php echo esc_attr( $slug ); ?>">
					<input type="hidden" name="back" value="<?php echo esc_attr( admin_url( 'admin.php?page=' . self::PAGE . '&tab=agent' ) ); ?>">
					<?php wp_nonce_field( 'wpc_admin' ); ?>
					<label class="wpc-label"><?php esc_html_e( 'Or let the AI Agent run it', 'wp-connect' ); ?></label>
					<div class="wpc-row">
						<select name="recurrence" <?php disabled( ! $agent_on ); ?>>
							<option value="once"><?php esc_html_e( 'Once', 'wp-connect' ); ?></option>
							<option value="weekly"><?php esc_html_e( 'Every week', 'wp-connect' ); ?></option>
							<option value="daily"><?php esc_html_e( 'Every day', 'wp-connect' ); ?></option>
						</select>
						<button type="submit" class="wpc-btn is-small" <?php disabled( ! $agent_on ); ?>><?php esc_html_e( 'Run now', 'wp-connect' ); ?></button>
					</div>
				</form>
			</div>
			<?php if ( $report && $report['skill'] === $slug ) : ?>
				<details class="wpc-report" open>
					<summary><?php echo esc_html( sprintf( __( 'Last report · %s ago', 'wp-connect' ), human_time_diff( strtotime( $report['created'] ) ) ) ); ?>
						<?php if ( null !== $report['score_before'] && null !== $report['score_after'] ) : ?>
							<span class="wpc-delta"><?php echo esc_html( sprintf( 'Speed %1$d -> %2$d', $report['score_before'], $report['score_after'] ) ); ?></span>
						<?php endif; ?>
					</summary>
					<p><?php echo esc_html( $report['summary'] ); ?></p>
					<div class="wpc-report-grid">
						<?php foreach ( $report['sections'] as $section ) : ?>
							<div class="wpc-report-sec is-<?php echo esc_attr( $section['status'] ); ?>">
								<strong><?php echo esc_html( $section['title'] ); ?></strong>
								<ul><?php foreach ( (array) $section['items'] as $item ) : ?><li><?php echo esc_html( $item ); ?></li><?php endforeach; ?></ul>
							</div>
						<?php endforeach; ?>
					</div>
				</details>
			<?php endif; ?>
			<details>
				<summary><?php esc_html_e( 'Edit instructions', 'wp-connect' ); ?></summary>
				<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
					<input type="hidden" name="action" value="wpc_action">
					<input type="hidden" name="do" value="skill_edit_instructions">
					<input type="hidden" name="skill" value="<?php echo esc_attr( $slug ); ?>">
					<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>">
					<?php wp_nonce_field( 'wpc_admin' ); ?>
					<textarea name="instructions" rows="10" class="wpc-mono"><?php echo esc_textarea( WPC_Skills::raw_instructions( $slug ) ); ?></textarea>
					<p class="wpc-muted"><?php esc_html_e( 'Claude reads exactly this when it runs the skill. {fix_mode} is replaced with the setting above.', 'wp-connect' ); ?></p>
					<div class="wpc-actions wpc-actions--left">
						<button type="submit" class="wpc-btn is-small"><?php esc_html_e( 'Save', 'wp-connect' ); ?></button>
					</div>
				</form>
				<?php if ( ! empty( $meta['is_builtin'] ) && WPC_Skills::is_overridden( $slug ) ) : ?>
					<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
						<input type="hidden" name="action" value="wpc_action">
						<input type="hidden" name="do" value="skill_reset_instructions">
						<input type="hidden" name="skill" value="<?php echo esc_attr( $slug ); ?>">
						<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>">
						<?php wp_nonce_field( 'wpc_admin' ); ?>
						<button type="submit" class="wpc-btn is-small is-ghost"><?php esc_html_e( 'Reset to original', 'wp-connect' ); ?></button>
					</form>
				<?php endif; ?>
				<?php if ( empty( $meta['is_builtin'] ) ) : ?>
					<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" data-confirm="<?php esc_attr_e( 'Delete this skill?', 'wp-connect' ); ?>">
						<input type="hidden" name="action" value="wpc_action">
						<input type="hidden" name="do" value="skill_delete">
						<input type="hidden" name="skill" value="<?php echo esc_attr( $slug ); ?>">
						<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>">
						<?php wp_nonce_field( 'wpc_admin' ); ?>
						<button type="submit" class="wpc-btn is-small is-danger"><?php esc_html_e( 'Delete skill', 'wp-connect' ); ?></button>
					</form>
				<?php endif; ?>
			</details>
		</div>
		<?php
	}

	/* ------------------------------------------------------------------ */
	/* Activity                                                             */
	/* ------------------------------------------------------------------ */

	private function recent_runs( $limit, $offset = 0 ) {
		global $wpdb;
		$table = WPC_Plugin::instance()->table( 'runs' );
		return $wpdb->get_results( $wpdb->prepare( "SELECT * FROM {$table} ORDER BY id DESC LIMIT %d OFFSET %d", $limit, $offset ) ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
	}

	private function tab_activity() {
		$page   = isset( $_GET['wpc_page'] ) ? max( 1, (int) $_GET['wpc_page'] ) : 1; // phpcs:ignore WordPress.Security.NonceVerification.Recommended
		$runs   = $this->recent_runs( 30, ( $page - 1 ) * 30 );
		?>
		<section class="wpc-section">
			<h2><?php esc_html_e( 'Activity', 'wp-connect' ); ?></h2>
			<p><?php esc_html_e( 'Everything Claude did on your site. Thumbs up or down tells WP-Connect whether a result was what you wanted; it feeds the ability\'s rating. Undo puts things back the way they were.', 'wp-connect' ); ?></p>
			<div class="wpc-card">
				<?php $this->render_run_list( $runs, true ); ?>
			</div>
			<div class="wpc-pager">
				<?php if ( $page > 1 ) : ?><a href="<?php echo esc_url( add_query_arg( 'wpc_page', $page - 1 ) ); ?>">&larr; <?php esc_html_e( 'Newer', 'wp-connect' ); ?></a><?php endif; ?>
				<?php if ( count( $runs ) === 30 ) : ?><a href="<?php echo esc_url( add_query_arg( 'wpc_page', $page + 1 ) ); ?>"><?php esc_html_e( 'Older', 'wp-connect' ); ?> &rarr;</a><?php endif; ?>
			</div>
		</section>
		<?php
	}

	private function render_run_list( $runs, $full ) {
		if ( empty( $runs ) ) {
			echo '<p class="wpc-empty">' . esc_html__( 'Nothing yet.', 'wp-connect' ) . '</p>';
			return;
		}
		echo '<ul class="wpc-runs">';
		foreach ( $runs as $run ) {
			$ability     = WPC_Abilities::get( $run->ability );
			$label       = $ability ? $ability['label'] : $run->ability;
			$status_class = $run->success ? ( null === $run->verified ? 'is-ok' : '' ) : 'is-fail';
			$status_text = $run->success ? ( 1 === (int) $run->verified ? __( 'Worked · checked', 'wp-connect' ) : __( 'Worked', 'wp-connect' ) ) : __( 'Failed', 'wp-connect' );
			$source_text = 'agent' === $run->source ? __( 'AI Agent', 'wp-connect' ) : __( 'Claude chat', 'wp-connect' );
			?>
			<li class="wpc-run <?php echo esc_attr( $status_class ); ?>">
				<span class="wpc-run-dot"></span>
				<div class="wpc-run-main">
					<b><?php echo esc_html( $label ); ?></b>
					<span><?php echo esc_html( $status_text . ' · ' . $source_text . ' · ' . human_time_diff( strtotime( $run->created ) ) . ' ago' ); ?></span>
					<?php if ( $run->error ) : ?><em><?php echo esc_html( $run->error ); ?></em><?php endif; ?>
				</div>
				<?php if ( $full ) : ?>
					<div class="wpc-run-actions">
						<button type="button" class="wpc-thumb <?php echo 1 === (int) $run->feedback ? 'is-on' : ''; ?>" data-run="<?php echo esc_attr( $run->id ); ?>" data-value="1" title="<?php esc_attr_e( 'Good result', 'wp-connect' ); ?>">👍</button>
						<button type="button" class="wpc-thumb <?php echo -1 === (int) $run->feedback ? 'is-on' : ''; ?>" data-run="<?php echo esc_attr( $run->id ); ?>" data-value="-1" title="<?php esc_attr_e( 'Wrong result', 'wp-connect' ); ?>">👎</button>
						<?php
						global $wpdb;
						$has_backup = (bool) $wpdb->get_var( $wpdb->prepare( 'SELECT COUNT(*) FROM ' . WPC_Plugin::instance()->table( 'backups' ) . ' WHERE run_id = %d AND undone = 0', $run->id ) ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
						if ( $has_backup ) :
							?>
							<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" data-confirm="<?php esc_attr_e( 'Undo this change?', 'wp-connect' ); ?>">
								<input type="hidden" name="action" value="wpc_action">
								<input type="hidden" name="do" value="undo_run">
								<input type="hidden" name="run_id" value="<?php echo esc_attr( $run->id ); ?>">
								<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>">
								<?php wp_nonce_field( 'wpc_admin' ); ?>
								<button type="submit" class="wpc-btn is-small is-ghost"><?php esc_html_e( 'Undo', 'wp-connect' ); ?></button>
							</form>
						<?php endif; ?>
					</div>
					<details class="wpc-run-details">
						<summary><?php esc_html_e( 'Details', 'wp-connect' ); ?></summary>
						<p><strong>Input:</strong></p>
						<pre class="wpc-code"><?php echo esc_html( wp_json_encode( json_decode( $run->input, true ), JSON_PRETTY_PRINT ) ); ?></pre>
						<p><strong>Result:</strong></p>
						<pre class="wpc-code"><?php echo esc_html( wp_json_encode( json_decode( $run->output, true ), JSON_PRETTY_PRINT ) ); ?></pre>
						<p class="wpc-muted">Run #<?php echo esc_html( $run->id ); ?> · <?php echo esc_html( $run->duration_ms ); ?> ms</p>
					</details>
				<?php endif; ?>
			</li>
			<?php
		}
		echo '</ul>';
	}

	/* ------------------------------------------------------------------ */
	/* AI Agent                                                             */
	/* ------------------------------------------------------------------ */

	private function tab_agent() {
		$mode = WPC_Plugin::instance()->mode();
		if ( 'agent' !== $mode ) {
			?>
			<div class="wpc-card wpc-banner">
				<p class="wpc-inline"><?php esc_html_e( 'AI Agent mode is off. In this mode the plugin calls Claude itself with your Anthropic API key, so jobs run without a chat (and on a schedule). API usage is billed by Anthropic to your key.', 'wp-connect' ); ?></p>
				<?php if ( '' === WPC_Plugin::instance()->api_key() ) : ?>
					<a class="wpc-btn" href="<?php echo esc_url( admin_url( 'admin.php?page=' . self::PAGE . '&tab=settings' ) ); ?>"><?php esc_html_e( 'Add API key', 'wp-connect' ); ?></a>
				<?php else : ?>
					<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
						<input type="hidden" name="action" value="wpc_action">
						<input type="hidden" name="do" value="set_mode">
						<input type="hidden" name="mode" value="agent">
						<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>">
						<?php wp_nonce_field( 'wpc_admin' ); ?>
						<button type="submit" class="wpc-btn"><?php esc_html_e( 'Turn on AI Agent mode', 'wp-connect' ); ?></button>
					</form>
				<?php endif; ?>
			</div>
			<?php
		}

		global $wpdb;
		$waiting = $wpdb->get_results( "SELECT * FROM " . WPC_Plugin::instance()->table( 'tasks' ) . " WHERE status = 'needs_approval' ORDER BY id DESC" ); // phpcs:ignore WordPress.DB.PreparedSQL.InterpolatedNotPrepared
		foreach ( (array) $waiting as $task ) {
			$this->render_approval_card( $task );
		}
		?>
		<div class="wpc-card wpc-composer <?php echo 'agent' === $mode ? '' : 'is-dim'; ?>">
			<h3><?php esc_html_e( 'Give your agent a job', 'wp-connect' ); ?></h3>
			<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
				<input type="hidden" name="action" value="wpc_action">
				<input type="hidden" name="do" value="agent_create">
				<input type="hidden" name="back" value="<?php echo esc_attr( admin_url( 'admin.php?page=' . self::PAGE . '&tab=agent' ) ); ?>">
				<?php wp_nonce_field( 'wpc_admin' ); ?>
				<textarea name="prompt" rows="3" placeholder="<?php esc_attr_e( 'e.g. Check my site, fix anything safe, and tell me what you changed.', 'wp-connect' ); ?>" <?php disabled( 'agent' !== $mode ); ?>></textarea>
				<div class="wpc-chips">
					<button type="button" class="wpc-chip" data-fill="<?php esc_attr_e( 'Run a full site check and safe fixes.', 'wp-connect' ); ?>"><?php esc_html_e( 'Site check & safe fixes', 'wp-connect' ); ?></button>
					<button type="button" class="wpc-chip" data-fill="<?php esc_attr_e( 'Find and fix missing image alt text.', 'wp-connect' ); ?>"><?php esc_html_e( 'Fix missing alt text', 'wp-connect' ); ?></button>
					<button type="button" class="wpc-chip" data-fill="<?php esc_attr_e( 'Check SEO titles and descriptions and improve weak ones.', 'wp-connect' ); ?>"><?php esc_html_e( 'Improve SEO descriptions', 'wp-connect' ); ?></button>
				</div>
				<div class="wpc-composer-foot">
					<label><?php esc_html_e( 'Repeat', 'wp-connect' ); ?>
						<select name="recurrence" <?php disabled( 'agent' !== $mode ); ?>>
							<option value="once"><?php esc_html_e( 'Just once', 'wp-connect' ); ?></option>
							<option value="daily"><?php esc_html_e( 'Every day', 'wp-connect' ); ?></option>
							<option value="weekly"><?php esc_html_e( 'Every week', 'wp-connect' ); ?></option>
						</select>
					</label>
					<button type="submit" class="wpc-btn" <?php disabled( 'agent' !== $mode ); ?>><?php esc_html_e( 'Run job', 'wp-connect' ); ?></button>
				</div>
			</form>
		</div>

		<div class="wpc-agent">
			<div class="wpc-card wpc-jobs">
				<h3><?php esc_html_e( 'Jobs', 'wp-connect' ); ?></h3>
				<?php $this->render_jobs_list(); ?>
			</div>
			<?php $this->render_job_detail(); ?>
		</div>
		<?php
	}

	private function render_approval_card( $task ) {
		$pending = json_decode( $task->pending, true );
		?>
		<div class="wpc-card wpc-approval">
			<h3><?php esc_html_e( "Your agent needs your OK", 'wp-connect' ); ?></h3>
			<p><?php echo esc_html( $task->prompt ); ?></p>
			<?php foreach ( (array) $pending['waiting'] as $call ) : ?>
				<div class="wpc-approval-item">
					<strong><?php echo esc_html( $call['name'] ); ?></strong>
					<pre class="wpc-code"><?php echo esc_html( wp_json_encode( $call['input'], JSON_PRETTY_PRINT ) ); ?></pre>
				</div>
			<?php endforeach; ?>
			<div class="wpc-actions">
				<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
					<input type="hidden" name="action" value="wpc_action">
					<input type="hidden" name="do" value="agent_resolve">
					<input type="hidden" name="task" value="<?php echo esc_attr( $task->id ); ?>">
					<input type="hidden" name="approve" value="0">
					<input type="hidden" name="back" value="<?php echo esc_attr( admin_url( 'admin.php?page=' . self::PAGE . '&tab=agent' ) ); ?>">
					<?php wp_nonce_field( 'wpc_admin' ); ?>
					<button type="submit" class="wpc-btn is-ghost"><?php esc_html_e( 'Decline', 'wp-connect' ); ?></button>
				</form>
				<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
					<input type="hidden" name="action" value="wpc_action">
					<input type="hidden" name="do" value="agent_resolve">
					<input type="hidden" name="task" value="<?php echo esc_attr( $task->id ); ?>">
					<input type="hidden" name="approve" value="1">
					<input type="hidden" name="back" value="<?php echo esc_attr( admin_url( 'admin.php?page=' . self::PAGE . '&tab=agent' ) ); ?>">
					<?php wp_nonce_field( 'wpc_admin' ); ?>
					<button type="submit" class="wpc-btn"><?php esc_html_e( 'Approve', 'wp-connect' ); ?></button>
				</form>
			</div>
		</div>
		<?php
	}

	private function render_jobs_list() {
		$tasks = WPC_Agent::instance()->tasks( 30 );
		if ( empty( $tasks ) ) {
			echo '<p class="wpc-empty">' . esc_html__( 'No jobs yet.', 'wp-connect' ) . '</p>';
			return;
		}
		$open_id = isset( $_GET['task'] ) ? (int) $_GET['task'] : ( $tasks[0]->id ?? 0 ); // phpcs:ignore WordPress.Security.NonceVerification.Recommended
		echo '<ul>';
		foreach ( $tasks as $task ) {
			printf(
				'<li class="%1$s"><a href="%2$s"><span class="wpc-status is-%3$s">%4$s</span><b>%5$s</b><small>%6$s ago%7$s</small></a></li>',
				(int) $task->id === $open_id ? 'is-open' : '',
				esc_url( add_query_arg( 'task', $task->id ) ),
				esc_attr( $task->status ),
				esc_html( WPC_Agent::instance()->status_label( $task->status ) ),
				esc_html( wp_trim_words( $task->prompt, 10 ) ),
				esc_html( human_time_diff( strtotime( $task->created ) ) ),
				'once' !== $task->recurrence ? esc_html( ' · ' . $task->recurrence ) : ''
			);
		}
		echo '</ul>';
	}

	private function render_job_detail() {
		$tasks = WPC_Agent::instance()->tasks( 30 );
		$id    = isset( $_GET['task'] ) ? (int) $_GET['task'] : ( $tasks[0]->id ?? 0 ); // phpcs:ignore WordPress.Security.NonceVerification.Recommended
		$task  = $id ? WPC_Agent::instance()->get_task( $id ) : null;
		if ( ! $task ) {
			echo '<div class="wpc-card"><p class="wpc-empty">' . esc_html__( 'No job selected.', 'wp-connect' ) . '</p></div>';
			return;
		}

		$live = in_array( $task->status, array( 'queued', 'running' ), true );
		?>
		<div class="wpc-card wpc-job" <?php echo $live ? 'data-live="1" data-task="' . esc_attr( $task->id ) . '"' : ''; ?>>
			<div class="wpc-card-head">
				<span class="wpc-status is-<?php echo esc_attr( $task->status ); ?>" data-status><?php echo esc_html( WPC_Agent::instance()->status_label( $task->status ) ); ?></span>
				<span class="wpc-muted"><span data-steps><?php echo esc_html( $task->steps ); ?></span> <?php esc_html_e( 'steps', 'wp-connect' ); ?> <?php echo $live ? '<span class="wpc-spin"></span>' : ''; ?></span>
			</div>
			<p><?php echo esc_html( $task->prompt ); ?></p>
			<div class="wpc-result" data-result><?php echo wp_kses_post( wpautop( esc_html( $task->result ) ) ); ?></div>
			<details class="wpc-report" open>
				<summary><?php esc_html_e( 'Step-by-step log', 'wp-connect' ); ?></summary>
				<ul class="wpc-log" data-log>
					<?php foreach ( (array) json_decode( $task->log, true ) as $entry ) : ?>
						<li class="is-<?php echo esc_attr( $entry['type'] ); ?>"><time><?php echo esc_html( gmdate( 'H:i', strtotime( $entry['t'] ) ) ); ?></time><span><?php echo esc_html( $entry['text'] ); ?></span></li>
					<?php endforeach; ?>
				</ul>
			</details>
			<div class="wpc-actions">
				<?php if ( in_array( $task->status, array( 'queued', 'running', 'needs_approval' ), true ) ) : ?>
					<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" data-confirm="<?php esc_attr_e( 'Stop this job?', 'wp-connect' ); ?>">
						<input type="hidden" name="action" value="wpc_action">
						<input type="hidden" name="do" value="agent_cancel">
						<input type="hidden" name="task" value="<?php echo esc_attr( $task->id ); ?>">
						<input type="hidden" name="back" value="<?php echo esc_attr( admin_url( 'admin.php?page=' . self::PAGE . '&tab=agent' ) ); ?>">
						<?php wp_nonce_field( 'wpc_admin' ); ?>
						<button type="submit" class="wpc-btn is-ghost"><?php esc_html_e( 'Stop job', 'wp-connect' ); ?></button>
					</form>
				<?php elseif ( 'scheduled' === $task->status ) : ?>
					<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" data-confirm="<?php esc_attr_e( 'Cancel this schedule?', 'wp-connect' ); ?>">
						<input type="hidden" name="action" value="wpc_action">
						<input type="hidden" name="do" value="agent_cancel">
						<input type="hidden" name="task" value="<?php echo esc_attr( $task->id ); ?>">
						<input type="hidden" name="back" value="<?php echo esc_attr( admin_url( 'admin.php?page=' . self::PAGE . '&tab=agent' ) ); ?>">
						<?php wp_nonce_field( 'wpc_admin' ); ?>
						<button type="submit" class="wpc-btn is-ghost"><?php esc_html_e( 'Cancel schedule', 'wp-connect' ); ?></button>
					</form>
				<?php endif; ?>
			</div>
		</div>
		<?php
	}

	/* ------------------------------------------------------------------ */
	/* Lessons                                                              */
	/* ------------------------------------------------------------------ */

	private function tab_lessons() {
		$topics = array( 'general' => __( 'General', 'wp-connect' ), 'site_care' => __( 'Site care', 'wp-connect' ) );
		foreach ( WPC_Abilities::all() as $name => $ability ) {
			$topics[ $name ] = $ability['label'];
		}
		?>
		<section class="wpc-section">
			<h2><?php esc_html_e( 'Lessons', 'wp-connect' ); ?></h2>
			<p><?php esc_html_e( "Lessons are how abilities get better on your site. Claude saves one when it figures out why something failed, and each lesson is added to that ability's instructions from then on. You can add your own, edit, or delete them.", 'wp-connect' ); ?></p>
			<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" class="wpc-lesson-add">
				<input type="hidden" name="action" value="wpc_action">
				<input type="hidden" name="do" value="lesson_add">
				<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>">
				<?php wp_nonce_field( 'wpc_admin' ); ?>
				<select name="topic">
					<?php foreach ( $topics as $key => $label ) : ?><option value="<?php echo esc_attr( $key ); ?>"><?php echo esc_html( $label ); ?></option><?php endforeach; ?>
				</select>
				<input type="text" name="lesson" maxlength="300" placeholder="<?php esc_attr_e( 'A short, specific lesson', 'wp-connect' ); ?>" required>
				<button type="submit" class="wpc-btn"><?php esc_html_e( 'Add lesson', 'wp-connect' ); ?></button>
			</form>

			<?php foreach ( $topics as $key => $label ) : ?>
				<?php $lessons = WPC_Abilities::lessons( $key ); ?>
				<?php if ( empty( $lessons ) ) { continue; } ?>
				<div class="wpc-card" id="topic-<?php echo esc_attr( $key ); ?>">
					<h3><?php echo esc_html( $label ); ?></h3>
					<ul class="wpc-lessons">
						<?php foreach ( $lessons as $lesson ) : ?>
							<li>
								<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" class="wpc-lesson-edit">
									<input type="hidden" name="action" value="wpc_action">
									<input type="hidden" name="do" value="lesson_update">
									<input type="hidden" name="id" value="<?php echo esc_attr( $lesson->id ); ?>">
									<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>#topic-<?php echo esc_attr( $key ); ?>">
									<?php wp_nonce_field( 'wpc_admin' ); ?>
									<input type="text" name="lesson" maxlength="300" value="<?php echo esc_attr( $lesson->lesson ); ?>">
									<span class="wpc-badge"><?php echo 'owner' === $lesson->source ? esc_html__( 'You', 'wp-connect' ) : esc_html__( 'Claude', 'wp-connect' ); ?></span>
									<button type="submit" class="wpc-icon-btn" title="<?php esc_attr_e( 'Save', 'wp-connect' ); ?>">&#10003;</button>
								</form>
								<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" data-confirm="<?php esc_attr_e( 'Delete this lesson?', 'wp-connect' ); ?>">
									<input type="hidden" name="action" value="wpc_action">
									<input type="hidden" name="do" value="lesson_delete">
									<input type="hidden" name="id" value="<?php echo esc_attr( $lesson->id ); ?>">
									<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>#topic-<?php echo esc_attr( $key ); ?>">
									<?php wp_nonce_field( 'wpc_admin' ); ?>
									<button type="submit" class="wpc-icon-btn" title="<?php esc_attr_e( 'Delete', 'wp-connect' ); ?>">&times;</button>
								</form>
							</li>
						<?php endforeach; ?>
					</ul>
				</div>
			<?php endforeach; ?>
		</section>
		<?php
	}

	/* ------------------------------------------------------------------ */
	/* Settings                                                             */
	/* ------------------------------------------------------------------ */

	private function tab_settings() {
		$plugin = WPC_Plugin::instance();
		?>
		<div class="wpc-card">
			<h3><?php esc_html_e( 'AI Agent (Anthropic API)', 'wp-connect' ); ?></h3>
			<p class="wpc-muted"><?php esc_html_e( "Only needed for AI Agent mode. Get a key at console.anthropic.com. It's stored encrypted and never shown again.", 'wp-connect' ); ?></p>
			<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
				<input type="hidden" name="action" value="wpc_action">
				<input type="hidden" name="do" value="save_settings">
				<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>">
				<?php wp_nonce_field( 'wpc_admin' ); ?>
				<label class="wpc-label"><?php esc_html_e( 'API key', 'wp-connect' ); ?></label>
				<input type="password" name="api_key" placeholder="<?php echo $plugin->api_key_hint() ? esc_attr( $plugin->api_key_hint() . ' (saved)' ) : ''; ?>">
				<label class="wpc-label"><?php esc_html_e( 'Model', 'wp-connect' ); ?></label>
				<select name="model">
					<?php foreach ( WPC_Agent::$models as $key => $label ) : ?>
						<option value="<?php echo esc_attr( $key ); ?>" <?php selected( $plugin->get_setting( 'model' ), $key ); ?>><?php echo esc_html( $label ); ?></option>
					<?php endforeach; ?>
				</select>
				<label class="wpc-label"><?php esc_html_e( 'Max steps per job', 'wp-connect' ); ?></label>
				<input type="number" name="agent_max_steps" min="3" max="100" value="<?php echo esc_attr( $plugin->get_setting( 'agent_max_steps', 25 ) ); ?>">
				<label class="wpc-check">
					<input type="checkbox" name="email_on_done" value="1" <?php checked( $plugin->get_setting( 'email_on_done', true ) ); ?>>
					<span><?php esc_html_e( 'Email me when a job finishes or needs my OK', 'wp-connect' ); ?></span>
				</label>
				<div class="wpc-actions wpc-actions--left"><button type="submit" class="wpc-btn"><?php esc_html_e( 'Save settings', 'wp-connect' ); ?></button></div>
			</form>
		</div>

		<div class="wpc-card">
			<h3><?php esc_html_e( 'Plugin vulnerability checks', 'wp-connect' ); ?></h3>
			<p class="wpc-muted"><?php esc_html_e( 'Optional. A free WPScan API token (wpscan.com, 25 checks a day) lets the plugin security check look up known vulnerabilities. Without it, it still checks for removed, abandoned and outdated plugins.', 'wp-connect' ); ?></p>
			<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
				<input type="hidden" name="action" value="wpc_action">
				<input type="hidden" name="do" value="save_wpscan">
				<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>">
				<?php wp_nonce_field( 'wpc_admin' ); ?>
				<label class="wpc-label"><?php esc_html_e( 'WPScan token', 'wp-connect' ); ?></label>
				<input type="text" name="wpscan_token" placeholder="<?php echo $plugin->get_setting( 'wpscan_token' ) ? esc_attr__( 'saved - type "remove" to delete', 'wp-connect' ) : ''; ?>">
				<div class="wpc-actions wpc-actions--left"><button type="submit" class="wpc-btn is-small"><?php esc_html_e( 'Save', 'wp-connect' ); ?></button></div>
			</form>
		</div>

		<div class="wpc-card">
			<h3><?php esc_html_e( 'Safety', 'wp-connect' ); ?></h3>
			<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
				<input type="hidden" name="action" value="wpc_action">
				<input type="hidden" name="do" value="save_uninstall">
				<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>">
				<?php wp_nonce_field( 'wpc_admin' ); ?>
				<label class="wpc-check">
					<input type="checkbox" name="delete_on_uninstall" value="1" <?php checked( $plugin->get_setting( 'delete_on_uninstall' ) ); ?>>
					<span><?php esc_html_e( 'Delete all WP-Connect data when the plugin is deleted', 'wp-connect' ); ?></span>
				</label>
				<div class="wpc-actions wpc-actions--left"><button type="submit" class="wpc-btn is-small"><?php esc_html_e( 'Save', 'wp-connect' ); ?></button></div>
			</form>
		</div>

		<div class="wpc-card">
			<h3><?php esc_html_e( 'Saved key', 'wp-connect' ); ?></h3>
			<div class="wpc-actions wpc-actions--left">
				<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>">
					<input type="hidden" name="action" value="wpc_action">
					<input type="hidden" name="do" value="test_key">
					<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>">
					<?php wp_nonce_field( 'wpc_admin' ); ?>
					<button type="submit" class="wpc-btn is-ghost"><?php esc_html_e( 'Test key', 'wp-connect' ); ?></button>
				</form>
				<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" data-confirm="<?php esc_attr_e( 'Remove the saved API key?', 'wp-connect' ); ?>">
					<input type="hidden" name="action" value="wpc_action">
					<input type="hidden" name="do" value="remove_key">
					<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>">
					<?php wp_nonce_field( 'wpc_admin' ); ?>
					<button type="submit" class="wpc-btn is-danger"><?php esc_html_e( 'Remove key', 'wp-connect' ); ?></button>
				</form>
			</div>
			<h3><?php esc_html_e( 'Reset', 'wp-connect' ); ?></h3>
			<div class="wpc-actions wpc-actions--left">
				<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" data-confirm="<?php esc_attr_e( 'Reset every ability rating?', 'wp-connect' ); ?>">
					<input type="hidden" name="action" value="wpc_action">
					<input type="hidden" name="do" value="reset_all_ratings">
					<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>">
					<?php wp_nonce_field( 'wpc_admin' ); ?>
					<button type="submit" class="wpc-btn is-ghost"><?php esc_html_e( 'Reset all ratings', 'wp-connect' ); ?></button>
				</form>
				<form method="post" action="<?php echo esc_url( admin_url( 'admin-post.php' ) ); ?>" data-confirm="<?php esc_attr_e( 'Disconnect every connected app?', 'wp-connect' ); ?>">
					<input type="hidden" name="action" value="wpc_action">
					<input type="hidden" name="do" value="disconnect_all">
					<input type="hidden" name="back" value="<?php echo esc_attr( $this->back_url() ); ?>">
					<?php wp_nonce_field( 'wpc_admin' ); ?>
					<button type="submit" class="wpc-btn is-ghost"><?php esc_html_e( 'Disconnect all apps', 'wp-connect' ); ?></button>
				</form>
			</div>
		</div>
		<?php
	}

	/* ------------------------------------------------------------------ */
	/* admin-post handler                                                   */
	/* ------------------------------------------------------------------ */

	public function handle_post() {
		if ( ! current_user_can( 'manage_options' ) ) {
			wp_die( esc_html__( 'You are not allowed to do this.', 'wp-connect' ) );
		}
		check_admin_referer( 'wpc_admin' );

		$do   = isset( $_POST['do'] ) ? sanitize_key( $_POST['do'] ) : '';
		$back = isset( $_POST['back'] ) ? esc_url_raw( wp_unslash( $_POST['back'] ) ) : admin_url( 'admin.php?page=' . self::PAGE );

		$method = 'do_' . $do;
		if ( method_exists( $this, $method ) ) {
			$this->$method();
		}

		wp_safe_redirect( $back );
		exit;
	}

	private function do_set_mode() {
		$mode = isset( $_POST['mode'] ) ? sanitize_key( $_POST['mode'] ) : 'abilities';
		if ( ! in_array( $mode, array( 'full', 'abilities', 'agent' ), true ) ) {
			return;
		}
		WPC_Plugin::instance()->update_settings( array( 'mode' => $mode ) );
		$this->notice( sprintf( __( '%s mode is on. Reconnect or refresh tools in Claude to see the change.', 'wp-connect' ), WPC_Plugin::instance()->mode_label( $mode ) ) );
	}

	private function do_create_app_password() {
		if ( ! class_exists( 'WP_Application_Passwords' ) ) {
			$this->notice( __( 'Application passwords are not available on this site.', 'wp-connect' ), 'warn' );
			return;
		}
		$name   = 'WP-Connect (Claude) ' . gmdate( 'Y-m-d' );
		$result = WP_Application_Passwords::create_new_application_password( get_current_user_id(), array( 'name' => $name ) );
		if ( is_wp_error( $result ) ) {
			$this->notice( $result->get_error_message(), 'warn' );
			return;
		}
		set_transient( 'wpc_shown_app_password_' . get_current_user_id(), $result[0], 5 * MINUTE_IN_SECONDS );
		add_filter(
			'wp_redirect',
			function ( $location ) {
				return add_query_arg( 'wpc_new_app_password', '1', $location ) . '#app-password';
			}
		);
	}

	private function do_connection_test() {
		$results = array();

		$mcp_url = WPC_OAuth::instance()->mcp_url();
		$token   = wp_generate_password( 32, false );
		set_transient( 'wpc_selftest_' . $token, 1, 2 * MINUTE_IN_SECONDS );
		$response = wp_remote_post(
			$mcp_url,
			array(
				'timeout' => 20,
				'headers' => array( 'Content-Type' => 'application/json' ),
				'body'    => wp_json_encode( array( 'jsonrpc' => '2.0', 'id' => 1, 'method' => 'ping' ) ),
			)
		);
		$code = is_wp_error( $response ) ? 0 : wp_remote_retrieve_response_code( $response );
		if ( 401 === $code ) {
			$results[] = array( 'ok' => true, 'title' => __( 'MCP endpoint reachable', 'wp-connect' ), 'detail' => ' - ' . __( 'correctly requires sign-in.', 'wp-connect' ) );
		} elseif ( 200 === $code ) {
			$results[] = array( 'ok' => false, 'title' => __( 'MCP endpoint did not require authentication', 'wp-connect' ), 'detail' => '' );
		} else {
			$results[] = array( 'ok' => false, 'title' => __( 'Could not reach the MCP endpoint', 'wp-connect' ), 'detail' => ' - ' . __( 'A security plugin may be blocking the REST API.', 'wp-connect' ) );
		}

		$discovery = wp_remote_get( home_url( '/.well-known/oauth-protected-resource' ), array( 'timeout' => 10 ) );
		$results[] = array(
			'ok'     => ! is_wp_error( $discovery ) && 200 === wp_remote_retrieve_response_code( $discovery ),
			'title'  => __( 'Login discovery', 'wp-connect' ),
			'detail' => '',
		);

		$results[] = array(
			'ok'     => is_ssl() || 0 === strpos( home_url(), 'https://' ),
			'title'  => __( 'HTTPS', 'wp-connect' ),
			'detail' => ' - ' . __( 'claude.ai only connects to https:// sites.', 'wp-connect' ),
		);

		set_transient( 'wpc_test_results_' . get_current_user_id(), $results, 60 );
	}

	private function do_ability_reject() {
		WPC_Abilities::reject( (int) $_POST['id'] );
		$this->notice( __( 'Rejected.', 'wp-connect' ) );
	}

	private function do_ability_approve() {
		WPC_Abilities::approve( (int) $_POST['id'] );
		$this->notice( __( 'Approved and live.', 'wp-connect' ) );
	}

	private function do_ability_restore() {
		WPC_Abilities::restore_version( (int) $_POST['id'] );
		$this->notice( __( 'Restored.', 'wp-connect' ) );
	}

	private function do_ability_delete() {
		WPC_Abilities::delete_custom( sanitize_text_field( wp_unslash( $_POST['name'] ) ) );
		$this->notice( __( 'Deleted.', 'wp-connect' ) );
	}

	private function do_save_tuning() {
		WPC_Abilities::save_tuning(
			sanitize_text_field( wp_unslash( $_POST['name'] ) ),
			isset( $_POST['notes'] ) ? wp_unslash( $_POST['notes'] ) : '',
			isset( $_POST['needs_approval'] ) && '' !== $_POST['needs_approval'] ? ( '1' === $_POST['needs_approval'] ) : null
		);
		$this->notice( __( 'Saved.', 'wp-connect' ) );
	}

	private function do_reset_rating() {
		WPC_Abilities::reset_rating( sanitize_text_field( wp_unslash( $_POST['name'] ) ) );
		$this->notice( __( 'Rating reset.', 'wp-connect' ) );
	}

	private function do_reset_all_ratings() {
		foreach ( WPC_Abilities::all() as $name => $ability ) {
			WPC_Abilities::reset_rating( $name );
		}
		$this->notice( __( 'All ratings reset.', 'wp-connect' ) );
	}

	private function do_undo_run() {
		$ok = WPC_Backups::undo_run( (int) $_POST['run_id'] );
		$this->notice( $ok ? __( 'Undone.', 'wp-connect' ) : __( 'Nothing to undo.', 'wp-connect' ) );
	}

	private function do_lesson_add() {
		WPC_Abilities::save_lesson( sanitize_text_field( wp_unslash( $_POST['topic'] ) ), wp_unslash( $_POST['lesson'] ), 'owner' );
		$this->notice( __( 'Lesson added.', 'wp-connect' ) );
	}

	private function do_lesson_update() {
		WPC_Abilities::update_lesson( (int) $_POST['id'], wp_unslash( $_POST['lesson'] ) );
	}

	private function do_lesson_delete() {
		WPC_Abilities::delete_lesson( (int) $_POST['id'] );
	}

	private function do_skill_save() {
		WPC_Skills::save_custom( sanitize_title( wp_unslash( $_POST['skill_slug'] ) ), sanitize_text_field( wp_unslash( $_POST['skill_slug'] ) ), wp_unslash( $_POST['description'] ), wp_unslash( $_POST['instructions'] ), 'owner' );
		$this->notice( __( 'Skill saved.', 'wp-connect' ) );
	}

	private function do_skill_fix_mode() {
		WPC_Skills::set_fix_mode( sanitize_text_field( wp_unslash( $_POST['skill'] ) ), sanitize_key( $_POST['fix_mode'] ) );
	}

	private function do_skill_edit_instructions() {
		WPC_Skills::override_instructions( sanitize_text_field( wp_unslash( $_POST['skill'] ) ), wp_unslash( $_POST['instructions'] ) );
		$this->notice( __( 'Saved.', 'wp-connect' ) );
	}

	private function do_skill_reset_instructions() {
		WPC_Skills::reset_instructions( sanitize_text_field( wp_unslash( $_POST['skill'] ) ) );
	}

	private function do_skill_delete() {
		WPC_Skills::delete_custom( sanitize_text_field( wp_unslash( $_POST['skill'] ) ) );
	}

	private function do_skill_run() {
		$slug       = sanitize_text_field( wp_unslash( $_POST['skill'] ) );
		$recurrence = sanitize_key( $_POST['recurrence'] );
		WPC_Agent::instance()->create(
			sprintf( 'Run the "%1$s" skill on this site: call wpc_skill_get with skill "%1$s" and follow its steps.', $slug ),
			$recurrence
		);
	}

	private function do_save_settings() {
		$plugin = WPC_Plugin::instance();
		$plugin->update_settings(
			array(
				'model'           => sanitize_text_field( wp_unslash( $_POST['model'] ) ),
				'agent_max_steps' => max( 3, min( 100, (int) $_POST['agent_max_steps'] ) ),
				'email_on_done'   => ! empty( $_POST['email_on_done'] ),
			)
		);
		if ( ! empty( $_POST['api_key'] ) ) {
			$plugin->set_api_key( wp_unslash( $_POST['api_key'] ) );
			$test = WPC_Agent::instance()->test_key( $plugin->api_key() );
			if ( is_wp_error( $test ) ) {
				$this->notice( __( 'Settings saved, but: ', 'wp-connect' ) . $test->get_error_message(), 'warn' );
				return;
			}
			$this->notice( __( 'Settings saved. API key works.', 'wp-connect' ) );
			return;
		}
		$this->notice( __( 'Settings saved.', 'wp-connect' ) );
	}

	private function do_save_wpscan() {
		$token = isset( $_POST['wpscan_token'] ) ? trim( wp_unslash( $_POST['wpscan_token'] ) ) : '';
		if ( 'remove' === strtolower( $token ) ) {
			$token = '';
		} elseif ( '' === $token ) {
			return;
		}
		WPC_Plugin::instance()->update_settings( array( 'wpscan_token' => $token ) );
		$this->notice( __( 'Saved.', 'wp-connect' ) );
	}

	private function do_save_uninstall() {
		WPC_Plugin::instance()->update_settings( array( 'delete_on_uninstall' => ! empty( $_POST['delete_on_uninstall'] ) ) );
		$this->notice( __( 'Saved.', 'wp-connect' ) );
	}

	private function do_test_key() {
		$result = WPC_Agent::instance()->test_key( WPC_Plugin::instance()->api_key() );
		$this->notice( is_wp_error( $result ) ? $result->get_error_message() : __( 'The key works.', 'wp-connect' ), is_wp_error( $result ) ? 'warn' : 'ok' );
	}

	private function do_remove_key() {
		WPC_Plugin::instance()->set_api_key( '' );
		$this->notice( __( 'API key removed.', 'wp-connect' ) );
	}

	private function do_disconnect_all() {
		WPC_OAuth::instance()->disconnect_all();
		$this->notice( __( 'All apps disconnected.', 'wp-connect' ) );
	}

	private function do_agent_create() {
		$prompt     = isset( $_POST['prompt'] ) ? trim( wp_unslash( $_POST['prompt'] ) ) : '';
		$recurrence = sanitize_key( $_POST['recurrence'] );
		if ( '' === $prompt ) {
			return;
		}
		WPC_Agent::instance()->create( $prompt, $recurrence );
	}

	private function do_agent_resolve() {
		WPC_Agent::instance()->resolve( (int) $_POST['task'], ! empty( $_POST['approve'] ) && '1' === $_POST['approve'] );
	}

	private function do_agent_cancel() {
		WPC_Agent::instance()->cancel( (int) $_POST['task'] );
	}

	/* ------------------------------------------------------------------ */
	/* AJAX                                                                 */
	/* ------------------------------------------------------------------ */

	private function verify_ajax() {
		check_ajax_referer( 'wpc_ajax' );
		if ( ! current_user_can( 'manage_options' ) ) {
			wp_send_json_error( 'forbidden', 403 );
		}
	}

	public function ajax_toggle() {
		$this->verify_ajax();
		$ok = WPC_Abilities::toggle( sanitize_text_field( wp_unslash( $_POST['name'] ) ), ! empty( $_POST['on'] ) );
		$ok ? wp_send_json_success() : wp_send_json_error();
	}

	public function ajax_feedback() {
		$this->verify_ajax();
		$run_id = (int) $_POST['run'];
		$value  = (int) $_POST['value'];
		if ( 0 === $value ) {
			global $wpdb;
			$wpdb->update( WPC_Plugin::instance()->table( 'runs' ), array( 'feedback' => null ), array( 'id' => $run_id ) );
			wp_send_json_success();
		}
		$rating = WPC_Abilities::record_feedback( $run_id, 1 === $value );
		null === $rating ? wp_send_json_error() : wp_send_json_success( $rating );
	}

	public function ajax_poll() {
		$this->verify_ajax();
		$task = WPC_Agent::instance()->poll( (int) $_POST['task'] );
		if ( ! $task ) {
			wp_send_json_error();
		}

		$log_html = '';
		foreach ( (array) json_decode( $task->log, true ) as $entry ) {
			$log_html .= sprintf( '<li class="is-%1$s"><time>%2$s</time><span>%3$s</span></li>', esc_attr( $entry['type'] ), esc_html( gmdate( 'H:i', strtotime( $entry['t'] ) ) ), esc_html( $entry['text'] ) );
		}

		wp_send_json_success(
			array(
				'status' => $task->status,
				'label'  => WPC_Agent::instance()->status_label( $task->status ),
				'steps'  => (int) $task->steps,
				'log'    => $log_html,
				'result' => wpautop( esc_html( $task->result ) ),
			)
		);
	}
}
