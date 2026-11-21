"""
A verbatim-content-reuse detector plus a source-disclosure check, built
from a real, manually-performed investigation this round: a Medium
article/repo ("Building the Entire RAG Ecosystem," Fareed Khan) presents
a RAG-techniques walkthrough in first person throughout ("My Table of
Contents...," every diagram captioned "Created by Fareed Khan"), while
its own repository's LICENSE file reads "Copyright (c) 2025 LangChain"
and its commit history is titled "MIT LangChain" -- and its code,
checked directly against the real public `langchain-ai/rag-from-scratch`
repository, turns out to share verbatim, character-for-character
identical cells (the Step-Back Prompting few-shot examples: "Could the
members of The Police perform lawful arrests?" / "Jan Sindel's was born
in what country?", confirmed present in both repos byte-for-byte).

Despite the correctly-preserved MIT copyright line (a legally proper
minimum), the article's own prose never names the original source
anywhere -- every "LangChain" mention in the README/article is about
*using* the LangChain library, never about the walkthrough's own
content being substantially LangChain's pre-existing teaching material.

This module generalizes the by-hand check performed this round: given a
candidate text/code corpus and one or more reference corpora, find
verbatim (n-gram-fingerprint) overlap, and separately check whether any
given disclosure text (the candidate's own README/article prose) names
the reference source specifically -- not just mentions a tool or brand
name that happens to also be the reference's author, which is exactly
the false-disclosure trap a naive substring check on "LangChain" alone
would fall into here.
"""
from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass, field


def normalize(text: str) -> str:
    """Lowercase and collapse whitespace, so formatting differences
    (newlines, extra spaces) don't hide a real verbatim match."""
    return re.sub(r"\s+", " ", text.strip().lower())


def ngram_fingerprints(text: str, n: int = 8) -> set[str]:
    """Sliding-window word n-grams of the normalized text. A real
    verbatim-reuse signal, not just a shared short phrase -- n=8 words
    is long enough that two independent authors landing on the same
    8-word sequence by coincidence is implausible."""
    words = normalize(text).split()
    if len(words) < n:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i : i + n]) for i in range(len(words) - n + 1)}


@dataclass
class ReuseMatch:
    reference_name: str
    shared_ngrams: int
    candidate_ngrams: int
    overlap_ratio: float  # shared / candidate_ngrams
    sample_matches: list[str] = field(default_factory=list)


def find_reuse(
    candidate_text: str, references: dict[str, str], n: int = 8, max_samples: int = 3
) -> list[ReuseMatch]:
    """Check a candidate text against one or more named reference texts
    for verbatim n-gram overlap. Returns one ReuseMatch per reference
    that shares at least one n-gram, sorted by overlap ratio descending."""
    candidate_grams = ngram_fingerprints(candidate_text, n)
    if not candidate_grams:
        return []

    matches = []
    for name, ref_text in references.items():
        ref_grams = ngram_fingerprints(ref_text, n)
        shared = candidate_grams & ref_grams
        if not shared:
            continue
        matches.append(
            ReuseMatch(
                reference_name=name,
                shared_ngrams=len(shared),
                candidate_ngrams=len(candidate_grams),
                overlap_ratio=len(shared) / len(candidate_grams),
                sample_matches=sorted(shared)[:max_samples],
            )
        )
    return sorted(matches, key=lambda m: m.overlap_ratio, reverse=True)


def is_disclosed(disclosure_text: str, source_markers: list[str]) -> bool:
    """A source counts as disclosed only if the disclosure text contains
    one of its specific, identifying markers (e.g. a repo name, an
    author's name, a specific project title) -- never a bare mention of
    a generic tool/brand name the source also happens to share. Pass
    markers specific enough that a tool-usage mention can't trigger a
    false positive (e.g. "rag-from-scratch" or "langchain-ai", not the
    bare word "LangChain", which this project's own check found mentioned
    dozens of times in the article purely as a library being used)."""
    normalized = normalize(disclosure_text)
    return any(normalize(marker) in normalized for marker in source_markers)


@dataclass
class ProvenanceReport:
    reuse: list[ReuseMatch]
    disclosed: dict[str, bool]  # reference_name -> whether it was disclosed

    @property
    def undisclosed_reuse(self) -> list[ReuseMatch]:
        """Reuse found, with no matching disclosure -- the actual
        finding this module exists to surface."""
        return [m for m in self.reuse if not self.disclosed.get(m.reference_name, False)]


def check_provenance(
    candidate_text: str,
    references: dict[str, str],
    disclosure_text: str,
    source_markers: dict[str, list[str]],
    n: int = 8,
) -> ProvenanceReport:
    """The full check: find verbatim reuse against each named reference,
    then check whether the disclosure text actually names that specific
    reference (via its own markers, never a generic brand mention)."""
    reuse = find_reuse(candidate_text, references, n=n)
    disclosed = {
        m.reference_name: is_disclosed(disclosure_text, source_markers.get(m.reference_name, []))
        for m in reuse
    }
    return ProvenanceReport(reuse=reuse, disclosed=disclosed)


def sha256_of_file(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


@dataclass(frozen=True)
class BinaryMatch:
    filename: str
    reference_name: str


def find_binary_reuse(candidate_dir: str, references: dict[str, str]) -> list[BinaryMatch]:
    """Check every file in `candidate_dir` against same-named files in
    each reference directory for byte-identical content (sha256).

    Verbatim text reuse isn't the only signal a real investigation needs
    -- this round's own check found 9 of 11 shared-filename diagram
    images between two real repos were byte-identical, confirmed this
    way (sha256), not by eye. Images carry no words to fingerprint, so
    this is a deliberately separate function from `find_reuse()`, not a
    variant of it."""
    matches = []
    for fname in sorted(os.listdir(candidate_dir)):
        cand_path = os.path.join(candidate_dir, fname)
        if not os.path.isfile(cand_path):
            continue
        cand_hash = sha256_of_file(cand_path)
        for ref_name, ref_dir in references.items():
            ref_path = os.path.join(ref_dir, fname)
            if os.path.isfile(ref_path) and sha256_of_file(ref_path) == cand_hash:
                matches.append(BinaryMatch(filename=fname, reference_name=ref_name))
    return matches
