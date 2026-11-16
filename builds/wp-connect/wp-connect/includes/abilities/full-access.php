<?php
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

/**
 * Full Access mode's one ability: run arbitrary PHP. Never offered in
 * Abilities or AI Agent mode (see 'modes' / 'agent' below).
 */

WPC_Abilities::register(
	array(
		'name'         => 'run_php',
		'label'        => __( 'Run PHP (Full Access)', 'wp-connect' ),
		'category'     => 'full_access',
		'description'  => __( 'Full Access mode: run PHP code inside WordPress with every WordPress function available. Send code without the <?php tag; use "return" to send a value back (echo output is captured too). Prefer a specific ability when one exists, because those back up and can be undone; this one can\'t be undone automatically. Explain what the code does in purpose, it is shown to the owner.', 'wp-connect' ),
		'writes'       => true,
		'risky'        => true,
		'modes'        => array( 'full' ),
		'agent'        => false,
		'input_schema' => array(
			'type'       => 'object',
			'properties' => array(
				'code'    => array( 'type' => 'string' ),
				'purpose' => array( 'type' => 'string' ),
			),
			'required'   => array( 'code', 'purpose' ),
		),
		'callback'     => function ( $input ) {
			$code = $input['code'];
			if ( 0 === strpos( ltrim( $code ), '<?php' ) ) {
				throw new WPC_Ability_Error( __( 'Code must not include an opening <?php tag.', 'wp-connect' ) );
			}

			$lint_error = WPC_Abilities::lint_code( $code );
			if ( '' !== $lint_error ) {
				throw new WPC_Ability_Error( $lint_error );
			}

			ob_start();
			try {
				// phpcs:ignore Squiz.PHP.Eval.Discouraged
				$fn     = eval( 'return function() { ' . $code . ' };' );
				$return = $fn();
			} catch ( \Throwable $e ) {
				ob_end_clean();
				throw new WPC_Ability_Error( sprintf( 'PHP error: %s (%s:%d)', $e->getMessage(), basename( $e->getFile() ), $e->getLine() ) );
			}
			$output = ob_get_clean();

			return array(
				'purpose' => $input['purpose'],
				'return'  => $return,
				'output'  => $output,
			);
		},
	)
);
