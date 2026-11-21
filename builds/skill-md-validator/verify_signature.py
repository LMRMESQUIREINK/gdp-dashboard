"""Verify NVIDIA's `skill.oms.sig` bundles found in `NVIDIA/auto-ontology`'s
`skills/*/` directories -- a signed, content-addressed manifest of a skill's
own files, built by the same `model_signing` scheme Sigstore's model-transparency
project uses for ML model provenance, repurposed here for Claude Agent Skill
bundles. Full source analysis: `/notes/nvidia-auto-ontology-analysis.md`.

Unlike every other check in this build (and in `skill_md_validator.py`,
deliberately dependency-free), this one needs real X.509/ECDSA parsing, which
has no stdlib equivalent -- it imports `cryptography`, stated plainly here as
a real, justified new dependency rather than silently added.

What this verifies, and what it deliberately does NOT:

- It recomputes a sha256 digest for every file the signed in-toto statement
  names, and reports exactly which match, which drifted, and which are
  missing -- the core "did the files change after signing" integrity check.
- It cryptographically verifies the DSSE envelope's signature against the
  leaf certificate's embedded public key (ECDSA over the DSSE
  pre-authentication encoding, per the DSSE spec), confirming the signed
  statement is internally self-consistent -- the private key paired with
  that leaf cert really did produce this signature over this exact payload.
- It does NOT validate the certificate chain against any public root of
  trust. These bundles' leaf certs chain to "NVIDIA Agent Capabilities CA",
  a private NVIDIA-operated CA, not Sigstore's public Fulcio root -- there
  is no public root to chain to from outside NVIDIA. This script reports
  the chain's subject/issuer/validity metadata for a human to read, never
  as a trust decision.
- It does NOT check Rekor (Sigstore's public transparency log) for an entry,
  because these bundles' own `tlogEntries` list is empty in every skill this
  project checked (`nvidia-ontology-setup`, `nvidia-ontology-query`,
  `nvidia-ontology-management`) -- a real, consistent, checkable property of
  this signing scheme worth surfacing as its own finding, not a bug in this
  verifier: these signatures are not independently, publicly auditable via a
  transparency log the way a standard keyless Sigstore signature would be;
  the audit trail depends entirely on trusting NVIDIA's own private CA.
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.hashes import SHA256, SHA384, SHA512

_HASH_BY_CURVE_BITS = {256: SHA256, 384: SHA384, 521: SHA512}

DSSE_PAYLOAD_TYPE = "application/vnd.in-toto+json"


@dataclass
class ResourceCheck:
    name: str
    algorithm: str
    expected_digest: str
    actual_digest: str | None
    status: str  # "match" | "mismatch" | "missing"


@dataclass
class CertInfo:
    index: int
    subject: str
    issuer: str
    not_valid_before: str
    not_valid_after: str


@dataclass
class VerificationResult:
    skill_dir: Path
    sig_path: Path
    statement_subject_name: str | None
    predicate_type: str | None
    resources: list[ResourceCheck] = field(default_factory=list)
    certs: list[CertInfo] = field(default_factory=list)
    dsse_signature_valid: bool | None = None
    dsse_signature_error: str | None = None
    tlog_entries: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        if self.errors:
            return False
        if self.dsse_signature_valid is False:
            return False
        return all(r.status == "match" for r in self.resources)


def _b64decode(s: str) -> bytes:
    return base64.b64decode(s)


def _dsse_pae(payload_type: str, payload: bytes) -> bytes:
    """DSSE pre-authentication encoding, per the DSSE spec:
    PAE(type, body) = "DSSEv1" + SP + LEN(type) + SP + type + SP + LEN(body) + SP + body
    with LEN() being the decimal length and all fields space-separated, no
    trailing delimiter."""
    type_bytes = payload_type.encode("utf-8")
    parts = [
        b"DSSEv1",
        str(len(type_bytes)).encode("ascii"),
        type_bytes,
        str(len(payload)).encode("ascii"),
        payload,
    ]
    return b" ".join(parts)


def verify_skill_signature(skill_dir: str | Path) -> VerificationResult:
    skill_dir = Path(skill_dir)
    sig_path = skill_dir / "skill.oms.sig"
    result = VerificationResult(
        skill_dir=skill_dir,
        sig_path=sig_path,
        statement_subject_name=None,
        predicate_type=None,
    )

    if not sig_path.is_file():
        result.errors.append(f"no skill.oms.sig found at {sig_path}")
        return result

    bundle = json.loads(sig_path.read_text())

    verification_material = bundle.get("verificationMaterial", {})
    tlog_entries = verification_material.get("tlogEntries", [])
    result.tlog_entries = len(tlog_entries)

    certs_der = (
        verification_material.get("x509CertificateChain", {}).get("certificates", [])
    )
    cert_objs = []
    for i, entry in enumerate(certs_der):
        raw = _b64decode(entry["rawBytes"])
        cert = x509.load_der_x509_certificate(raw)
        cert_objs.append(cert)
        result.certs.append(
            CertInfo(
                index=i,
                subject=cert.subject.rfc4514_string(),
                issuer=cert.issuer.rfc4514_string(),
                not_valid_before=cert.not_valid_before_utc.isoformat(),
                not_valid_after=cert.not_valid_after_utc.isoformat(),
            )
        )

    envelope = bundle.get("dsseEnvelope", {})
    payload_type = envelope.get("payloadType", "")
    payload_b64 = envelope.get("payload", "")
    payload_bytes = _b64decode(payload_b64)
    statement = json.loads(payload_bytes)

    result.predicate_type = statement.get("predicateType")
    subjects = statement.get("subject", [])
    if subjects:
        result.statement_subject_name = subjects[0].get("name")

    resources = statement.get("predicate", {}).get("resources", [])
    for res in resources:
        name = res["name"]
        algorithm = res.get("algorithm", "sha256")
        expected_digest = res["digest"]
        file_path = skill_dir / name
        if not file_path.is_file():
            result.resources.append(
                ResourceCheck(name, algorithm, expected_digest, None, "missing")
            )
            continue
        actual_digest = _hash_file(file_path, algorithm)
        status = "match" if actual_digest == expected_digest else "mismatch"
        result.resources.append(
            ResourceCheck(name, algorithm, expected_digest, actual_digest, status)
        )

    sigs = envelope.get("signatures", [])
    if not sigs:
        result.dsse_signature_error = "no signatures present in dsseEnvelope"
    elif not cert_objs:
        result.dsse_signature_error = "no certificates present to verify against"
    else:
        leaf_cert = cert_objs[0]
        public_key = leaf_cert.public_key()
        if not isinstance(public_key, ec.EllipticCurvePublicKey):
            result.dsse_signature_error = (
                f"leaf certificate public key is {type(public_key).__name__}, "
                "not an EC key -- verification not implemented for this key type"
            )
        else:
            hash_cls = _HASH_BY_CURVE_BITS.get(public_key.curve.key_size)
            if hash_cls is None:
                result.dsse_signature_error = (
                    f"no known ECDSA hash pairing for curve {public_key.curve.name} "
                    f"({public_key.curve.key_size}-bit)"
                )
            else:
                pae = _dsse_pae(payload_type, payload_bytes)
                sig_bytes = _b64decode(sigs[0]["sig"])
                try:
                    public_key.verify(sig_bytes, pae, ec.ECDSA(hash_cls()))
                    result.dsse_signature_valid = True
                except InvalidSignature:
                    result.dsse_signature_valid = False
                    result.dsse_signature_error = "signature does not verify against leaf certificate's public key"

    return result


def _hash_file(path: Path, algorithm: str) -> str:
    if algorithm != "sha256":
        raise ValueError(f"unsupported digest algorithm: {algorithm}")
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def format_report(result: VerificationResult) -> str:
    lines = [f"Skill: {result.skill_dir.name}"]
    if result.errors:
        for e in result.errors:
            lines.append(f"  ERROR: {e}")
        return "\n".join(lines)

    lines.append(f"  Predicate type: {result.predicate_type}")
    lines.append(f"  Statement subject: {result.statement_subject_name}")
    lines.append(f"  Transparency-log entries: {result.tlog_entries}")
    if result.dsse_signature_valid is True:
        lines.append("  DSSE signature: VALID (matches leaf cert's public key)")
    elif result.dsse_signature_valid is False:
        lines.append(f"  DSSE signature: INVALID -- {result.dsse_signature_error}")
    else:
        lines.append(f"  DSSE signature: not checked -- {result.dsse_signature_error}")

    for cert in result.certs:
        lines.append(f"  Cert[{cert.index}]: subject={cert.subject}")
        lines.append(f"              issuer={cert.issuer}")
        lines.append(
            f"              valid {cert.not_valid_before} .. {cert.not_valid_after}"
        )

    for res in result.resources:
        marker = {"match": "OK", "mismatch": "MISMATCH", "missing": "MISSING"}[res.status]
        lines.append(f"  [{marker}] {res.name}")

    lines.append(f"  Overall: {'PASS' if result.ok else 'FAIL'}")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    print(format_report(verify_skill_signature(target)))
