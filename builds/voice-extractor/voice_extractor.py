#!/usr/bin/env python3
"""
CLI for extracting a voice profile from a writing sample, and scoring a
new draft against it.

Usage:
    python3 voice_extractor.py extract sample.txt --save profile.json
    python3 voice_extractor.py score draft.md --profile profile.json
    python3 voice_extractor.py score draft.md --profile profile.json --json
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import sys

from voice_match import score_match
from voice_profile import VoiceProfile, extract_profile


def _read(path: str) -> str:
    return sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()


def _cmd_extract(args: argparse.Namespace) -> int:
    text = _read(args.path)
    profile = extract_profile(text)
    payload = dataclasses.asdict(profile)
    payload["top_sentence_openers"] = list(profile.top_sentence_openers)

    rendered = json.dumps(payload, indent=2)
    if args.save:
        with open(args.save, "w", encoding="utf-8") as handle:
            handle.write(rendered)
        print(f"Saved voice profile to {args.save} ({profile.sentence_count} sentences analyzed)")
    else:
        print(rendered)
    return 0


def _load_profile(path: str) -> VoiceProfile:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    data["top_sentence_openers"] = tuple(tuple(pair) for pair in data["top_sentence_openers"])
    return VoiceProfile(**data)


def _cmd_score(args: argparse.Namespace) -> int:
    draft_text = _read(args.path)
    reference = _load_profile(args.profile)
    result = score_match(draft_text, reference)

    if args.json:
        print(json.dumps(
            {
                "overall_score": result.overall_score,
                "per_metric_score": result.per_metric_score,
                "suggestions": list(result.suggestions),
            },
            indent=2,
        ))
    else:
        print(f"Voice match score: {result.overall_score:.0%}")
        if result.suggestions:
            print("To sound more like the reference voice:")
            for suggestion in result.suggestions:
                print(f"  - {suggestion}")
        else:
            print("No strong mismatches found.")

    if args.min_score is not None and result.overall_score < args.min_score:
        print(f"\nFAIL: {result.overall_score:.0%} is below the {args.min_score:.0%} threshold", file=sys.stderr)
        return 1
    return 0


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    extract_parser = sub.add_parser("extract", help="Extract a voice profile from a writing sample")
    extract_parser.add_argument("path", help="Sample file, or '-' for stdin")
    extract_parser.add_argument("--save", help="Write the profile as JSON to this path")
    extract_parser.set_defaults(func=_cmd_extract)

    score_parser = sub.add_parser("score", help="Score a draft against a saved voice profile")
    score_parser.add_argument("path", help="Draft file, or '-' for stdin")
    score_parser.add_argument("--profile", required=True, help="Path to a saved voice profile JSON file")
    score_parser.add_argument("--json", action="store_true")
    score_parser.add_argument("--min-score", type=float, default=None, help="Exit 1 if the score is below this (0.0-1.0)")
    score_parser.set_defaults(func=_cmd_score)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(_main())
