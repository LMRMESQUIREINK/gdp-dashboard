# Deep analysis: `NVIDIA/auto-ontology`

Source: a bare GitHub repo link, no accompanying text — per this
project's established convention, the bare link is itself the
instruction to run the deep-analysis-and-ship loop. A genuinely new,
substantial, actively-shipping NVIDIA open-source project: Apache 2.0,
1,084 files, 475 Python files, a frontend, an MCP server, Helm charts,
Alembic migrations, and its own `CLAUDE.md`/`AGENTS.md` — measured via
`git clone`/`find`/`wc` before reading anything for meaning.

## What it is

Auto Ontology builds an enterprise semantic layer (an "ontology") from
database metadata automatically, lets human experts certify it, and
exposes it to any agent harness (MCP, CLI, API) so a text-to-SQL agent
can ground its answers in business meaning instead of guessing table
joins from scratch. It generates a Postgres+pgvector ontology from a
source database, answers questions through a tool-calling loop
(`retrieve`/`run_sql`/`submit`), checks `check_answerable` before
committing to an answer it can't actually support, and interoperates
with Apache Ossie (a real, separately-maintained open semantic-model
exchange standard with its own converter for Auto Ontology,
`apache/ossie-converters`).

## Leaderboard claims checked, found unverifiable from this sandbox

The README's top two badges claim "#1 on the BEAVER leaderboard" and
"#2 on the BIRD-Interact leaderboard." Checked directly rather than
repeated as fact: both leaderboard hosts
(`beaverbench.github.io`, `bird-interact.github.io`) returned
`getaddrinfo ENOTFOUND` from this sandbox — the same egress-restriction
class already documented for EODHD/FMP/Hugging Face/arXiv/
agentskills.io/dev.to, now extended to both benchmark sites. Secondary
web sources confirm BEAVER and BIRD-Interact are both real, independently-
run text-to-SQL benchmarks (BEAVER: MIT-led, enterprise data; BIRD-
Interact: GPT-5 scoring only 8.67%-17% on its own harder interactive
tracks), and that the companion `NVIDIA/auto-ontology-eval` repo exists
and runs schema-only-vs-ontology-equipped comparisons against both —
but no secondary source could confirm the specific #1/#2 rank claims,
and this sandbox can't reach the primary leaderboard pages to check
directly. Reported as unverified, not disputed.

## The disclosed internal trust boundary checks out exactly

The README states plainly that FastAPI (port 3001) and the ingestion
service (port 3002) must stay on a private network because "FastAPI
trusts the user identity the frontend forwards in the
`x-auto-ontology-user-id` header... with no authentication of their
own." Read the real code rather than trusted the prose: `auto_ontology/
server/identity.py`'s `resolve_internal_user()` does exactly this —
reads the header, raises 401 only if a caller explicitly required
authentication and the header is empty, with its own docstring stating
"FastAPI must not be publicly reachable because the header is not
independently authenticated here." The `nvidia-ontology-setup` skill's
own developer-workflow instructions repeat the same warning verbatim
when telling a developer to open port 3001 to a Docker container.
Credited as an honestly disclosed, consistently enforced design
decision, not a silently-assumed one.

## The real finding: NVIDIA ships cryptographically signed Claude Agent Skills

The repo's `skills/` directory contains three real, substantial Claude
Agent Skills (`nvidia-ontology-setup`, `nvidia-ontology-query`,
`nvidia-ontology-management`) — the first vendor-shipped (not
third-party) Claude Skills this project has found inside a product's
own repository, as opposed to a standalone skills marketplace
(`coreyhaines31/marketingskills`, `mattpocock/skills`) or community
skill (the Scrapling skills). Each carries a `skill.oms.sig` file: a
real Sigstore-*bundle-format* signature (`application/vnd.dev.sigstore.
bundle.v0.3+json`) wrapping a DSSE envelope whose payload is an in-toto
attestation (`predicateType: https://model_signing/signature/v1.0` —
the same scheme Sigstore's `model-transparency`/`model_signing` project
uses for ML model provenance, repurposed here for skill files) listing
a sha256 digest for every file the skill ships (`SKILL.md`,
`BENCHMARK.md`, `evals/evals.json`, every `references/*.md`,
`assets/runtime-contract.yaml`, `skill-card.md`).

Each skill also carries a `BENCHMARK.md` and `skill-card.md` describing
a real three-tier publication gate: Tier 1 static validation (a tool
called "SkillSpector"), Tier 2 semantic deduplication, and Tier 3 live
agent evaluation — two real agents (Claude Code, Codex) run 10
evaluation tasks each in isolated Kubernetes sandbox pods, scored on
five weighted dimensions (Security, Correctness, Discoverability,
Effectiveness, Efficiency) against a no-skill baseline, with a real
measured uplift table (e.g. Correctness 50.0%→100.0% for Claude Code
with the setup skill). `skill-card.md` follows NVIDIA's standard
model/dataset-card template (license, deployment geography, required
credentials, known risks, ethical considerations) applied to a Claude
Skill instead of a model.

**Built**: extended `/builds/skill-md-validator/` (checked `/builds/`
first — this is exactly the project's existing home for Claude Skill
validation, and cryptographic integrity is a new, clearly separate
concern from the existing frontmatter/structure checks, not a
duplicate) with `verify_signature.py` — a real verifier for this
`skill.oms.sig` format: it recomputes sha256 for every file the signed
statement names and reports match/mismatch/missing, and cryptographically
verifies the DSSE envelope's ECDSA signature against the leaf
certificate's embedded public key, confirming the signed statement is
internally self-consistent. It deliberately does NOT validate the
certificate chain against a public root of trust — these bundles chain
to "NVIDIA Agent Capabilities CA," a private NVIDIA-operated CA, not
Sigstore's public Fulcio root, so there is no public root to check
against from outside NVIDIA; chain metadata (subject/issuer/validity)
is reported for a human to read, never as a trust decision. Needed a
real, justified new dependency — `cryptography`, for X.509/ECDSA
parsing with no stdlib equivalent — stated plainly rather than silently
added, a deliberate departure from this build's otherwise dependency-
free design.

**A real bug found and fixed in this build's own first draft, not in
NVIDIA's signing scheme**: the first version hardcoded SHA-256 for the
ECDSA verification and failed on all three real skills. Before
concluding anything about the source, inspected the actual leaf
certificate's curve directly — it's **secp384r1 (P-384)**, which pairs
with SHA-384, not SHA-256 (confirmed by the DER signature's own length,
104 bytes, consistent with a P-384 signature and inconsistent with
P-256's ~70-72 bytes). Fixed by deriving the hash algorithm from the
public key's curve size (256→SHA-256, 384→SHA-384, 521→SHA-512) instead
of assuming one. After the fix, all three real, unmodified skill
bundles verify cleanly: every file's content matches exactly what was
signed, and the DSSE signature is cryptographically valid against the
leaf cert — a genuine positive finding about NVIDIA's signing scheme,
not assumed from the format alone.

**A second real, consistent finding, not a bug**: all three skills'
`skill.oms.sig` bundles have an empty `tlogEntries` list — no Sigstore
transparency-log (Rekor) entry recorded, confirmed across all three
independently, not a one-off. This is a materially different trust
model than standard public "keyless" Sigstore signing, which logs every
signing event to a public, append-only transparency log for anyone to
audit — these signatures are authentic (the DSSE signature check
proves that) but not independently, publicly auditable the way the
bundle *format* might suggest at a glance. Stated plainly as an
observation about the scheme's actual trust model, not a flaw: NVIDIA's
own private CA hierarchy is a reasonable choice for an internal
signing pipeline that was never meant to log to the public Sigstore
transparency log in the first place.

**A third real finding, a genuine false positive in this project's own
pre-existing tool**, caught by running the unmodified
`skill_md_validator.py` against these three real skills: it flagged
`nvidia-ontology-setup`'s reference to `auto_ontology/server/main.py`
as a broken reference. Read the real line before concluding anything:
"The app factory is `create_app()` in `auto_ontology/server/__main__.py`.
**There is no** `auto_ontology/server/main.py`." — the author is
deliberately stating the path does NOT exist, to head off a reader's
wrong assumption, not pointing at a file that should be there. Same
false-positive class this project has repeatedly documented (Recovery
Desk's "doesn't diagnose or treat," the solo-bot-business-gate's
"guaranteed pass" meta-statement): negated language that a naive
reference-checker reads as a dangling pointer. **Fixed** with a new
`negated-reference` check: if the ~80 characters immediately before a
non-resolving reference contain an explicit negation-of-existence
phrase ("there is no," "there's no," "there are no," "no longer
exists," "does not exist"/"doesn't exist"), the finding downgrades from
a hard `broken-reference` error to a `negated-reference` warning
instead of being silently dropped — the fixture's two genuinely
unresolvable *other* references (real repo-root files this fixture
copy, deliberately only the skill subdirectory, legitimately can't see)
still correctly error, proving the fix is narrow and doesn't quietly
suppress real broken references.

44/44 tests pass across both suites (36 for `skill_md_validator.py`, up
from 35; 8 new for `verify_signature.py`), including the real,
unmodified `skill.oms.sig` bundles and real `SKILL.md` files from all
three skills committed as fixtures
(`tests/fixtures/nvidia-skills/`), a planted file-tampering test and a
planted bundle-tampering test (both correctly caught), and this
project's own 12 real skills re-confirmed clean (zero errors) after
both fixes.

## Deliberately not built

The ontology-generation pipeline and the text-to-SQL answering loop
themselves — both need a live NVIDIA NIM/OpenAI-compatible model
endpoint and a real source database (Wide World Importers, Microsoft's
sample sales DB), the same standing no-live-model-access restriction as
every build in this project needing a real model call. A full Sigstore
trust-chain verification against a public root — these bundles chain to
a private NVIDIA CA, not a public one, so there is no public root this
sandbox (or anyone outside NVIDIA) could verify against; this is a
real, structural reason, not a sandbox limitation to work around.
