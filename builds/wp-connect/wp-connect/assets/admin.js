/* global WPC */
( function () {
	'use strict';

	document.addEventListener( 'DOMContentLoaded', function () {
		wireConfirms();
		wireCopy();
		wireToggles();
		wireFilter();
		wireThumbs();
		wireFillChips();
		wireLivePoll();
	} );

	/* ---------------------------------------------------------- confirms */

	function wireConfirms() {
		document.querySelectorAll( '[data-confirm]' ).forEach( function ( form ) {
			form.addEventListener( 'submit', function ( e ) {
				if ( ! window.confirm( form.getAttribute( 'data-confirm' ) ) ) {
					e.preventDefault();
				}
			} );
		} );
	}

	/* -------------------------------------------------------------- copy */

	function wireCopy() {
		document.querySelectorAll( '[data-copy]' ).forEach( function ( btn ) {
			btn.addEventListener( 'click', function () {
				var text = btn.getAttribute( 'data-copy' );
				var done = function () {
					var original = btn.textContent;
					btn.textContent = 'Copied';
					setTimeout( function () {
						btn.textContent = original;
					}, 1500 );
				};

				if ( navigator.clipboard && navigator.clipboard.writeText ) {
					navigator.clipboard.writeText( text ).then( done, done );
					return;
				}

				var tmp = document.createElement( 'textarea' );
				tmp.value = text;
				tmp.style.position = 'fixed';
				tmp.style.opacity = '0';
				document.body.appendChild( tmp );
				tmp.select();
				try {
					document.execCommand( 'copy' );
				} catch ( err ) {
					/* clipboard unavailable; nothing more to do */
				}
				document.body.removeChild( tmp );
				done();
			} );
		} );
	}

	/* --------------------------------------------------------- toggles */

	function wireToggles() {
		document.querySelectorAll( '[data-toggle]' ).forEach( function ( input ) {
			input.addEventListener( 'change', function () {
				var name = input.getAttribute( 'data-toggle' );
				var on = input.checked;

				var body = new URLSearchParams();
				body.set( 'action', 'wpc_toggle' );
				body.set( '_wpnonce', WPC.nonce );
				body.set( 'name', name );
				body.set( 'on', on ? '1' : '0' );

				fetch( WPC.ajax, { method: 'POST', credentials: 'same-origin', body: body } )
					.then( function ( r ) {
						return r.json();
					} )
					.then( function ( json ) {
						if ( ! json || ! json.success ) {
							input.checked = ! on;
						}
					} )
					.catch( function () {
						input.checked = ! on;
					} );
			} );
		} );
	}

	/* ------------------------------------------------------------ filter */

	function wireFilter() {
		var chips = document.querySelectorAll( '[data-filter]' );
		var search = document.querySelector( '[data-filter-input]' );
		var cards = document.querySelectorAll( '.wpc-ability' );

		if ( ! chips.length && ! search ) {
			return;
		}

		var activeCat = 'all';

		function apply() {
			var term = search ? search.value.trim().toLowerCase() : '';
			cards.forEach( function ( card ) {
				var cat = card.getAttribute( 'data-cat' );
				var hay = card.getAttribute( 'data-search' ) || '';
				var catOk = 'all' === activeCat || cat === activeCat;
				var termOk = '' === term || hay.indexOf( term ) !== -1;
				card.style.display = catOk && termOk ? '' : 'none';
			} );
		}

		chips.forEach( function ( chip ) {
			chip.addEventListener( 'click', function () {
				chips.forEach( function ( c ) {
					c.classList.remove( 'is-active' );
				} );
				chip.classList.add( 'is-active' );
				activeCat = chip.getAttribute( 'data-filter' );
				apply();
			} );
		} );

		if ( search ) {
			search.addEventListener( 'input', apply );
		}
	}

	/* ------------------------------------------------------------- thumbs */

	function wireThumbs() {
		document.querySelectorAll( '.wpc-thumb' ).forEach( function ( btn ) {
			btn.addEventListener( 'click', function () {
				var runId = btn.getAttribute( 'data-run' );
				var value = btn.getAttribute( 'data-value' );
				var group = document.querySelectorAll( '.wpc-thumb[data-run="' + runId + '"]' );
				var wasOn = btn.classList.contains( 'is-on' );
				var newValue = wasOn ? '0' : value;

				var body = new URLSearchParams();
				body.set( 'action', 'wpc_feedback' );
				body.set( '_wpnonce', WPC.nonce );
				body.set( 'run', runId );
				body.set( 'value', newValue );

				fetch( WPC.ajax, { method: 'POST', credentials: 'same-origin', body: body } )
					.then( function ( r ) {
						return r.json();
					} )
					.then( function ( json ) {
						if ( json && json.success ) {
							group.forEach( function ( b ) {
								b.classList.remove( 'is-on' );
							} );
							if ( '0' !== newValue ) {
								btn.classList.add( 'is-on' );
							}
						}
					} );
			} );
		} );
	}

	/* -------------------------------------------------------- fill chips */

	function wireFillChips() {
		document.querySelectorAll( '[data-fill]' ).forEach( function ( chip ) {
			chip.addEventListener( 'click', function () {
				var form = chip.closest( 'form' );
				if ( ! form ) {
					return;
				}
				var textarea = form.querySelector( 'textarea' );
				if ( textarea ) {
					textarea.value = chip.getAttribute( 'data-fill' );
					textarea.focus();
				}
			} );
		} );
	}

	/* --------------------------------------------------------- live poll */

	function wireLivePoll() {
		var job = document.querySelector( '.wpc-job[data-live="1"]' );
		if ( ! job ) {
			return;
		}

		var taskId = job.getAttribute( 'data-task' );
		var statusEl = job.querySelector( '[data-status]' );
		var stepsEl = job.querySelector( '[data-steps]' );
		var logEl = job.querySelector( '[data-log]' );
		var resultEl = job.querySelector( '[data-result]' );

		var tries = 0;
		var maxTries = 150; /* ~5 minutes at 2s */

		var timer = setInterval( poll, 2000 );

		function poll() {
			tries++;
			if ( tries > maxTries ) {
				clearInterval( timer );
				return;
			}

			var body = new URLSearchParams();
			body.set( 'action', 'wpc_poll' );
			body.set( '_wpnonce', WPC.nonce );
			body.set( 'task', taskId );

			fetch( WPC.ajax, { method: 'POST', credentials: 'same-origin', body: body } )
				.then( function ( r ) {
					return r.json();
				} )
				.then( function ( json ) {
					if ( ! json || ! json.success ) {
						return;
					}
					var data = json.data;

					if ( statusEl ) {
						statusEl.textContent = data.label;
						statusEl.className = 'wpc-status is-' + data.status;
					}
					if ( stepsEl ) {
						stepsEl.textContent = data.steps;
					}
					if ( logEl ) {
						logEl.innerHTML = data.log;
					}
					if ( resultEl ) {
						resultEl.innerHTML = data.result;
					}

					if ( 'queued' !== data.status && 'running' !== data.status ) {
						clearInterval( timer );
						if ( 'needs_approval' === data.status ) {
							window.location.reload();
						}
					}
				} )
				.catch( function () {
					/* a missed poll just tries again next tick */
				} );
		}
	}
} )();
