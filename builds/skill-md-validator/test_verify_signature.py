"""Tests for verify_signature.py, run against the three real, unmodified
`skill.oms.sig` bundles NVIDIA ships in `NVIDIA/auto-ontology`'s
`skills/*/` directories (committed as fixtures under
`tests/fixtures/nvidia-skills/`), plus synthetic tamper cases.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from verify_signature import verify_skill_signature

FIXTURES = Path(__file__).parent / "tests" / "fixtures" / "nvidia-skills"
REAL_SKILLS = ["nvidia-ontology-setup", "nvidia-ontology-query", "nvidia-ontology-management"]


def run(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
        return True
    except AssertionError as e:
        print(f"FAIL  {name}: {e}")
        return False


def test_each_real_skill_signature_verifies():
    for skill in REAL_SKILLS:
        result = verify_skill_signature(FIXTURES / skill)
        assert result.ok, f"{skill} should pass: {result}"
        assert result.dsse_signature_valid is True


def test_each_real_skill_has_no_file_drift():
    for skill in REAL_SKILLS:
        result = verify_skill_signature(FIXTURES / skill)
        statuses = {r.status for r in result.resources}
        assert statuses == {"match"}, f"{skill}: {[r for r in result.resources if r.status != 'match']}"


def test_each_real_skill_has_no_transparency_log_entries():
    # A real, consistent, checkable property of this signing scheme across
    # all three skills -- not a bug in the verifier, a finding about the
    # source: these bundles aren't publicly auditable via Rekor.
    for skill in REAL_SKILLS:
        result = verify_skill_signature(FIXTURES / skill)
        assert result.tlog_entries == 0


def test_each_real_skill_cert_chain_has_three_certs():
    for skill in REAL_SKILLS:
        result = verify_skill_signature(FIXTURES / skill)
        assert len(result.certs) == 3
        assert "NVIDIA Agent Skills Signing" in result.certs[0].subject
        assert "NVIDIA Agent Capabilities ICA" in result.certs[1].subject
        assert "NVIDIA Agent Capabilities CA" in result.certs[2].subject


def test_tampering_with_a_signed_file_is_caught():
    # Copy a real skill, flip one byte in SKILL.md, confirm the digest
    # mismatch is caught -- proves this is a real discriminating check,
    # not something that reports PASS unconditionally.
    with tempfile.TemporaryDirectory() as tmp:
        dst = Path(tmp) / "nvidia-ontology-setup"
        shutil.copytree(FIXTURES / "nvidia-ontology-setup", dst)
        skill_md = dst / "SKILL.md"
        text = skill_md.read_text()
        skill_md.write_text(text + "\n<!-- tampered -->\n")

        result = verify_skill_signature(dst)
        assert not result.ok
        skill_md_check = next(r for r in result.resources if r.name == "SKILL.md")
        assert skill_md_check.status == "mismatch"
        # The DSSE signature itself is still internally valid -- it signed
        # the ORIGINAL digest list, which is exactly why the file-content
        # check is a separate, necessary layer from the signature check.
        assert result.dsse_signature_valid is True


def test_deleting_a_signed_file_is_reported_missing():
    with tempfile.TemporaryDirectory() as tmp:
        dst = Path(tmp) / "nvidia-ontology-setup"
        shutil.copytree(FIXTURES / "nvidia-ontology-setup", dst)
        (dst / "SKILL.md").unlink()

        result = verify_skill_signature(dst)
        assert not result.ok
        skill_md_check = next(r for r in result.resources if r.name == "SKILL.md")
        assert skill_md_check.status == "missing"
        assert skill_md_check.actual_digest is None


def test_tampering_with_the_signature_bundle_itself_is_caught():
    # Flip a byte inside the DSSE envelope's base64 payload (simulating a
    # forged statement) and confirm the ECDSA check -- not just the digest
    # check -- correctly rejects it.
    import base64
    import json

    with tempfile.TemporaryDirectory() as tmp:
        dst = Path(tmp) / "nvidia-ontology-setup"
        shutil.copytree(FIXTURES / "nvidia-ontology-setup", dst)
        sig_path = dst / "skill.oms.sig"
        bundle = json.loads(sig_path.read_text())

        payload_bytes = bytearray(base64.b64decode(bundle["dsseEnvelope"]["payload"]))
        # Flip one bit well inside the payload -- it's JSON text, so this
        # also keeps the file loadable as (different) JSON more often than
        # not, but either outcome is fine: either the payload still parses
        # and the signature fails, or it doesn't parse at all, which the
        # verifier's JSON decode will raise on. We only assert the strict
        # case: a still-parseable but altered payload fails signature
        # verification rather than silently accepted.
        payload_bytes[50] ^= 0x01
        bundle["dsseEnvelope"]["payload"] = base64.b64encode(bytes(payload_bytes)).decode()
        sig_path.write_text(json.dumps(bundle))

        try:
            result = verify_skill_signature(dst)
        except Exception:
            # Payload no longer parses as JSON -- an acceptable, safe
            # failure mode for a forged bundle, not something to paper over.
            return
        assert result.dsse_signature_valid is False


def test_missing_sig_file_reports_a_clean_error_not_a_crash():
    with tempfile.TemporaryDirectory() as tmp:
        dst = Path(tmp) / "no-sig-here"
        dst.mkdir()
        (dst / "SKILL.md").write_text("---\nname: x\n---\nbody")

        result = verify_skill_signature(dst)
        assert not result.ok
        assert result.errors
        assert "no skill.oms.sig" in result.errors[0]


TESTS = [
    test_each_real_skill_signature_verifies,
    test_each_real_skill_has_no_file_drift,
    test_each_real_skill_has_no_transparency_log_entries,
    test_each_real_skill_cert_chain_has_three_certs,
    test_tampering_with_a_signed_file_is_caught,
    test_deleting_a_signed_file_is_reported_missing,
    test_tampering_with_the_signature_bundle_itself_is_caught,
    test_missing_sig_file_reports_a_clean_error_not_a_crash,
]

if __name__ == "__main__":
    results = [run(t.__name__, t) for t in TESTS]
    passed = sum(results)
    total = len(results)
    print(f"\n{passed}/{total} passed")
    if passed != total:
        raise SystemExit(1)
