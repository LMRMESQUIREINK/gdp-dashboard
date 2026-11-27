"""The Verified Identity Agent Bridge (VIAB) and its named companion,
Delegated Boundary OAuth (DBO) — from "The Verified Identity Agent
Bridge" (Natarajan Selvaraj), one of five articles in the PDF bundle
analyzed in /notes/okf-rag-agentic-bundle-analysis.md. That round's named
"within a week" next move — built in the immediate follow-up round,
extending this build rather than starting a new one (checked /builds/
first: this is a verified-identity primitive, the same governance domain
`governed_call`/`approval_store.py` already live in).

The article's real scenario: a downstream low-code agent platform (its
own worked example is Microsoft Copilot Studio) cannot validate a
user-audience OAuth token directly. VIAB resolves this by having a
bridge do the work instead: verify the human via a delegated OAuth
Authorization Code + PKCE flow against the enterprise IdP, resolve
canonical identity from the IdP's own source of truth (the article's own
example: Microsoft Graph `/me`), and assert that verified identity
downstream as explicit per-request CONTEXT — never forwarding the user's
own access token.

DBO is the article's own named companion pattern, for the opposite case:
when the downstream service CAN validate a token directly (it has access
to the IdP's signing keys), the bridge mints and forwards a token scoped
to that specific downstream audience instead of a context dict. The two
patterns are deliberately kept as separate mechanisms below — VIAB never
produces a token at all; DBO never produces a bare context dict — rather
than one function branching on a flag, so a caller can't accidentally end
up on the wrong side of "did a token leave this boundary."

No live enterprise IdP exists in this sandbox to test against (same
standing restriction as every build here needing a live external
service), so `SimulatedIdP` below stands in for one — implementing just
the two steps VIAB actually depends on (issuing a PKCE-bound
authorization code, and resolving a verified subject from its own
directory on exchange), not a full OAuth server.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from typing import Optional


# --- PKCE -------------------------------------------------------------

def generate_pkce_pair() -> tuple[str, str]:
    """Returns (code_verifier, code_challenge) using the real PKCE
    S256 method: the challenge is the base64url-encoded SHA-256 of the
    verifier, with padding stripped."""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    challenge = _pkce_challenge(verifier)
    return verifier, challenge


def _pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


class PKCEMismatch(ValueError):
    pass


class AuthorizationCodeError(ValueError):
    pass


@dataclass
class _IssuedCode:
    code_challenge: str
    subject_id: str
    expires_at: float
    used: bool = False


class SimulatedIdP:
    """A stand-in for a real enterprise IdP (e.g. Microsoft Entra ID).
    Implements only what VIAB/DBO actually depend on: a user directory
    (the IdP's own source of truth for identity, matching the article's
    Graph `/me` step) and PKCE-bound authorization-code issuance and
    exchange — not a general-purpose OAuth server."""

    def __init__(self) -> None:
        self._directory: dict[str, dict] = {}
        self._codes: dict[str, _IssuedCode] = {}

    def register_user(self, subject_id: str, display_name: str) -> None:
        self._directory[subject_id] = {"display_name": display_name}

    def issue_authorization_code(self, subject_id: str, code_challenge: str, *, ttl: float = 300.0) -> str:
        if subject_id not in self._directory:
            raise AuthorizationCodeError(f"unknown subject: {subject_id}")
        code = secrets.token_urlsafe(16)
        self._codes[code] = _IssuedCode(code_challenge=code_challenge, subject_id=subject_id,
                                         expires_at=time.time() + ttl)
        return code

    def exchange_code(self, code: str, code_verifier: str) -> dict:
        """The token-exchange step. Raises on reuse, expiry, or a PKCE
        verifier that doesn't match the challenge the code was issued
        with — the real defense PKCE exists to provide: a stolen
        authorization code is useless without the verifier that only the
        original requester holds."""
        issued = self._codes.get(code)
        if issued is None:
            raise AuthorizationCodeError(f"unknown authorization code: {code}")
        if issued.used:
            raise AuthorizationCodeError(f"authorization code already used: {code}")
        if time.time() > issued.expires_at:
            raise AuthorizationCodeError(f"authorization code expired: {code}")
        if _pkce_challenge(code_verifier) != issued.code_challenge:
            raise PKCEMismatch("code_verifier does not match the code_challenge this code was issued with")
        issued.used = True
        profile = self._directory[issued.subject_id]
        return {"subject_id": issued.subject_id, **profile}


# --- VIAB ---------------------------------------------------------------

@dataclass(frozen=True)
class VerifiedIdentity:
    subject_id: str
    display_name: str
    verified_at: float
    verified_by: str  # which IdP resolved this identity, e.g. "entra-id"


class IdentityBridge:
    """VIAB: verifies a human via delegated OAuth Authorization Code +
    PKCE, resolves their canonical identity from the IdP's own directory,
    and asserts it downstream as an explicit context dict — never a
    token of any kind. Use this when the downstream surface cannot
    validate a user-audience token directly (the article's own example:
    a low-code agent platform)."""

    def __init__(self, idp: SimulatedIdP, idp_name: str = "entra-id"):
        self.idp = idp
        self.idp_name = idp_name

    def verify(self, authorization_code: str, code_verifier: str) -> VerifiedIdentity:
        profile = self.idp.exchange_code(authorization_code, code_verifier)
        return VerifiedIdentity(
            subject_id=profile["subject_id"],
            display_name=profile["display_name"],
            verified_at=time.time(),
            verified_by=self.idp_name,
        )

    def assert_downstream(self, identity: VerifiedIdentity) -> dict:
        """The per-request identity context handed to the downstream
        surface. The one invariant this function exists to guarantee:
        the real user's access token never appears anywhere in this
        dict — test_identity_bridge.py checks this directly against the
        returned keys, not just by reading this function's body."""
        return {
            "subject_id": identity.subject_id,
            "display_name": identity.display_name,
            "verified_by": identity.verified_by,
            "verified_at": identity.verified_at,
        }


# --- DBO ------------------------------------------------------------------

class DelegatedBoundaryTokenError(ValueError):
    pass


class DelegatedBoundaryToken:
    """DBO: the article's own named companion pattern, for when the
    downstream service CAN validate a token directly (it has access to
    the IdP's signing material). Mints a token scoped to one specific
    downstream audience and forwards THAT, never the user's own raw
    token — distinct from VIAB, which forwards no token at all.

    Implemented here as a minimal HMAC-signed claim set rather than a
    full JWT library: this sandbox has no live IdP whose real JWKS
    signing keys could be fetched, so the signing key below stands in for
    a key both sides of a real deployment would hold (the IdP's signing
    secret, or a shared verification key derived from it)."""

    def __init__(self, signing_key: bytes, issuer: str = "viab-bridge-demo"):
        self.signing_key = signing_key
        self.issuer = issuer

    def mint(self, identity: VerifiedIdentity, audience: str, *, ttl: float = 300.0) -> str:
        claims = {
            "sub": identity.subject_id,
            "aud": audience,
            "iss": self.issuer,
            "verified_by": identity.verified_by,
            "exp": time.time() + ttl,
        }
        payload = json.dumps(claims, sort_keys=True, separators=(",", ":")).encode("utf-8")
        signature = hmac.new(self.signing_key, payload, hashlib.sha256).hexdigest()
        return base64.urlsafe_b64encode(payload).decode("ascii") + "." + signature

    def validate(self, token: str, expected_audience: str) -> dict:
        """Raises on a malformed token, a bad signature, the wrong
        audience, or expiry. A downstream service calling this is
        exactly what makes DBO different from VIAB: it's validating a
        real, bearer-style credential, not simply trusting an
        already-asserted context dict."""
        try:
            payload_b64, signature = token.rsplit(".", 1)
            payload = base64.urlsafe_b64decode(payload_b64.encode("ascii"))
        except ValueError as exc:  # bad split, bad base64, or odd-length input
            raise DelegatedBoundaryTokenError(f"malformed token: {exc}") from exc
        expected_signature = hmac.new(self.signing_key, payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            raise DelegatedBoundaryTokenError("invalid token signature")
        claims = json.loads(payload)
        if claims["aud"] != expected_audience:
            raise DelegatedBoundaryTokenError(
                f"token audience {claims['aud']!r} does not match expected audience {expected_audience!r}"
            )
        if time.time() > claims["exp"]:
            raise DelegatedBoundaryTokenError("token has expired")
        return claims
