"""Tests for policy/identity_bridge.py — VIAB and DBO."""
from __future__ import annotations

import time
import unittest

from policy.identity_bridge import (
    AuthorizationCodeError,
    DelegatedBoundaryToken,
    DelegatedBoundaryTokenError,
    IdentityBridge,
    PKCEMismatch,
    SimulatedIdP,
    generate_pkce_pair,
)


def _authenticate(idp: SimulatedIdP, subject_id: str) -> tuple[str, str]:
    """Helper mirroring the real flow: the client generates a PKCE pair,
    the IdP issues a code bound to the challenge, and the client holds
    onto the verifier for the exchange step."""
    verifier, challenge = generate_pkce_pair()
    code = idp.issue_authorization_code(subject_id, challenge)
    return code, verifier


class TestVIABHappyPath(unittest.TestCase):
    def setUp(self):
        self.idp = SimulatedIdP()
        self.idp.register_user("u-1", "Dana Chen")
        self.bridge = IdentityBridge(self.idp, idp_name="entra-id")

    def test_verify_resolves_real_identity_from_idp_directory(self):
        code, verifier = _authenticate(self.idp, "u-1")
        identity = self.bridge.verify(code, verifier)
        self.assertEqual(identity.subject_id, "u-1")
        self.assertEqual(identity.display_name, "Dana Chen")
        self.assertEqual(identity.verified_by, "entra-id")

    def test_assert_downstream_context_never_contains_a_token(self):
        code, verifier = _authenticate(self.idp, "u-1")
        identity = self.bridge.verify(code, verifier)
        context = self.bridge.assert_downstream(identity)
        serialized = str(context).lower()
        for forbidden in ("token", "access_token", "bearer", "authorization_code"):
            self.assertNotIn(forbidden, serialized)
        self.assertEqual(
            set(context.keys()), {"subject_id", "display_name", "verified_by", "verified_at"}
        )

    def test_authorization_code_is_single_use(self):
        code, verifier = _authenticate(self.idp, "u-1")
        self.bridge.verify(code, verifier)
        with self.assertRaises(AuthorizationCodeError):
            self.bridge.verify(code, verifier)

    def test_wrong_pkce_verifier_is_rejected(self):
        code, _real_verifier = _authenticate(self.idp, "u-1")
        wrong_verifier, _unused = generate_pkce_pair()
        with self.assertRaises(PKCEMismatch):
            self.bridge.verify(code, wrong_verifier)

    def test_expired_authorization_code_is_rejected(self):
        verifier, challenge = generate_pkce_pair()
        code = self.idp.issue_authorization_code("u-1", challenge, ttl=-1.0)
        with self.assertRaises(AuthorizationCodeError):
            self.bridge.verify(code, verifier)

    def test_unknown_subject_cannot_be_issued_a_code(self):
        _verifier, challenge = generate_pkce_pair()
        with self.assertRaises(AuthorizationCodeError):
            self.idp.issue_authorization_code("ghost-user", challenge)

    def test_unknown_authorization_code_is_rejected(self):
        _verifier, _challenge = generate_pkce_pair()
        with self.assertRaises(AuthorizationCodeError):
            self.bridge.verify("not-a-real-code", "whatever")


class TestDBO(unittest.TestCase):
    def setUp(self):
        self.idp = SimulatedIdP()
        self.idp.register_user("u-2", "Priya Nair")
        self.bridge = IdentityBridge(self.idp)
        self.signing_key = b"shared-signing-secret-for-test"
        self.dbo = DelegatedBoundaryToken(self.signing_key, issuer="viab-bridge-demo")

    def _verified_identity(self):
        code, verifier = _authenticate(self.idp, "u-2")
        return self.bridge.verify(code, verifier)

    def test_downstream_can_validate_a_correctly_minted_token(self):
        identity = self._verified_identity()
        token = self.dbo.mint(identity, audience="procurement-service")
        claims = self.dbo.validate(token, expected_audience="procurement-service")
        self.assertEqual(claims["sub"], "u-2")
        self.assertEqual(claims["aud"], "procurement-service")
        self.assertEqual(claims["iss"], "viab-bridge-demo")

    def test_token_rejected_for_the_wrong_audience(self):
        identity = self._verified_identity()
        token = self.dbo.mint(identity, audience="procurement-service")
        with self.assertRaises(DelegatedBoundaryTokenError):
            self.dbo.validate(token, expected_audience="travel-service")

    def test_expired_token_is_rejected(self):
        identity = self._verified_identity()
        token = self.dbo.mint(identity, audience="procurement-service", ttl=-1.0)
        with self.assertRaises(DelegatedBoundaryTokenError):
            self.dbo.validate(token, expected_audience="procurement-service")

    def test_tampered_token_signature_is_rejected(self):
        identity = self._verified_identity()
        token = self.dbo.mint(identity, audience="procurement-service")
        payload_b64, signature = token.rsplit(".", 1)
        tampered = payload_b64 + "." + ("0" if signature[0] != "0" else "1") + signature[1:]
        with self.assertRaises(DelegatedBoundaryTokenError):
            self.dbo.validate(tampered, expected_audience="procurement-service")

    def test_a_different_signing_key_cannot_validate_the_token(self):
        """Simulates a downstream service that was never given the real
        shared key -- the token must not validate against it."""
        identity = self._verified_identity()
        token = self.dbo.mint(identity, audience="procurement-service")
        wrong_key_dbo = DelegatedBoundaryToken(b"a-completely-different-key")
        with self.assertRaises(DelegatedBoundaryTokenError):
            wrong_key_dbo.validate(token, expected_audience="procurement-service")

    def test_malformed_token_is_rejected_cleanly(self):
        with self.assertRaises(DelegatedBoundaryTokenError):
            self.dbo.validate("not-a-real-token-at-all", expected_audience="procurement-service")


class TestViabAndDboStayDistinct(unittest.TestCase):
    """The article's own point: these are two separate mechanisms for two
    different downstream capabilities, not one function with a flag.
    Confirmed structurally, not just by reading the two classes."""

    def test_viab_never_produces_a_token_shaped_string(self):
        idp = SimulatedIdP()
        idp.register_user("u-3", "Sam Okafor")
        bridge = IdentityBridge(idp)
        code, verifier = _authenticate(idp, "u-3")
        identity = bridge.verify(code, verifier)
        context = bridge.assert_downstream(identity)
        # A DBO token always contains a "." joining a base64 payload to a
        # hex signature. VIAB's context dict must never produce any
        # string value matching that shape.
        for value in context.values():
            if isinstance(value, str):
                self.assertNotIn(".", value)

    def test_dbo_never_returns_a_bare_context_dict(self):
        idp = SimulatedIdP()
        idp.register_user("u-4", "Omar Haddad")
        bridge = IdentityBridge(idp)
        code, verifier = _authenticate(idp, "u-4")
        identity = bridge.verify(code, verifier)
        dbo = DelegatedBoundaryToken(b"key")
        token = dbo.mint(identity, audience="hr-service")
        self.assertIsInstance(token, str)
        self.assertIn(".", token)


if __name__ == "__main__":
    unittest.main()
