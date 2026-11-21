# manifest-drift-guard

A dependency-free Python tool that checks whether a committed fingerprint
manifest (`{filename: hash}`) still matches the real files it describes —
built directly from a real finding in this round's `ruthless-gate` audit of
[`FareedKhan-dev/ontology-driven-observability`](https://github.com/FareedKhan-dev/ontology-driven-observability)
(`/builds/ontology-observability-gate/`, finding `deepest-01`).

## The gap this closes

That repository ships `artifacts/run_manifest.json`, which records a
sha256[:16] fingerprint for each of its three ontology files, written by the
notebook's own `file_hash()` and matching exactly what the executed notebook
printed when it last ran. The README's own central reproducibility claim is
that "the run fingerprints itself... a reader can see that the two agree."

Recomputing that same hash directly against the actually-committed files
shows all three have drifted — the files were edited after the run that
produced the manifest, and the edited files were committed alongside the
now-stale fingerprints, with nothing re-checking the manifest against the
files before publishing it. This tool is that missing re-check, applicable
to any project that ships a "this is what we measured" manifest next to the
files it describes — not specific to this one repository.

## Use

```bash
python3 manifest_drift.py <manifest.json> --dir <directory> [--key dotted.path.to.dict] [--strict] [--trunc N]
```

Exits `0` on a clean match, `1` on drift/missing files (or unlisted files
too, with `--strict`) — suitable as a CI gate. `--key` resolves a dotted
path into the JSON file to the `{filename: hash}` dict, for a manifest where
that mapping is nested (as it is in the real repo this was built from,
under `"ontology"`).

## Proven

```bash
python3 test_manifest_drift.py
```

**32/32 assertions pass**, against real files in a real temp directory for
every case (no mocking of `file_hash`): a clean manifest, an edited file
(drift), a deleted file (missing), an untracked file (unlisted, lenient vs.
`--strict`), an empty manifest, a mixed-outcome manifest, and five real CLI
subprocess calls (clean exit 0, drifted exit 1, strict vs. non-strict,
and a malformed `--key`). **One real bug found and fixed while writing
these tests**: a `--key` that didn't resolve inside the manifest JSON
originally crashed with a raw, unhandled `KeyError` traceback instead of a
clean error — fixed with a dedicated `KeyPathError` caught in `main()`,
now a distinct exit code (2) with a one-line message.

**Also run for real against the actual repository this tool was built
from** (not committed here — see `source/measurements.json` in
`/builds/ontology-observability-gate/` for why — but run directly against
a transient local clone during this round):

```
$ python3 manifest_drift.py artifacts/run_manifest.json --dir ontology --key ontology
  0 matched, 3 drifted, 0 missing, 0 unlisted
  DRIFT   competency.rq: manifest says 2cba2f48ff7891c2, file actually hashes to 97453bd4a5b85f10
  DRIFT   ops.ttl: manifest says db895132680a71ea, file actually hashes to 4180b165ed2c0482
  DRIFT   shapes.ttl: manifest says 1a8b5be802a06a9e, file actually hashes to 71c0d741cf16573c
exit code: 1
```

Reproduces the exact real-world finding this tool was built from, exactly —
not a synthetic approximation of it.

## What's not built here

- No recursive/glob file discovery — the manifest's own keys are the file
  list, matching the real repo's own `file_hash(p) for p in ONTO_DIR.glob("*")`
  pattern exactly, rather than inventing a different discovery mechanism.
- No auto-fix / manifest-regeneration mode — this tool reports drift, it
  doesn't decide whether the fix is "re-run and regenerate the manifest" or
  "revert the file edit," which is a project-specific judgment call.
