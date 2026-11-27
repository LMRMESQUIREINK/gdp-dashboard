"""Tests for sti.py. The central scenario (set up once in setUp) is
deliberately constructed so the three leaks the module docstring names
are each independently provable on the SAME documents and the SAME
caller — not three different hand-picked examples, one shared fixture.

Scenario: a caller in the "finance" group searches for "quarterly revenue
report". Two "engineering"-only documents score higher (they contain all
three query terms) than the one "finance"-authorized document (which
contains only one). With top_k=2, a naive post-filter search truncates to
the two unauthorized engineering documents BEFORE applying the ACL filter
— so after filtering, the finance caller's authorized, genuinely relevant
document is dropped entirely, even though it's the only document they
could ever see.
"""
from __future__ import annotations

import unittest

from sti import Document, SecurityTrimmedIndex, naive_post_filter_search


class TestScenario(unittest.TestCase):
    def setUp(self):
        self.index = SecurityTrimmedIndex()
        self.index.add(Document(
            id="eng-1", text="quarterly revenue report for the engineering org",
            allowed_group_ids=frozenset({"engineering"}),
            facets={"department": "engineering"},
        ))
        self.index.add(Document(
            id="eng-2", text="quarterly revenue report draft notes",
            allowed_group_ids=frozenset({"engineering"}),
            facets={"department": "engineering"},
        ))
        self.index.add(Document(
            id="fin-1", text="revenue summary for finance leadership",
            allowed_group_ids=frozenset({"finance"}),
            facets={"department": "finance"},
        ))
        self.finance_caller = {"finance"}
        self.engineering_caller = {"engineering"}
        self.query = "quarterly revenue report"

    # --- Correct behavior, STI ---

    def test_correct_search_returns_only_authorized_match(self):
        resp = self.index.search(self.query, self.finance_caller, top_k=2)
        self.assertEqual([r.doc_id for r in resp.results], ["fin-1"])

    def test_correct_total_count_reflects_only_authorized_subset(self):
        resp = self.index.search(self.query, self.finance_caller, top_k=2)
        self.assertEqual(resp.total_count, 1)

    def test_correct_facet_counts_reflect_only_authorized_subset(self):
        resp = self.index.search(self.query, self.finance_caller, top_k=2, facet_fields=("department",))
        self.assertEqual(resp.facet_counts["department"], {"finance": 1})

    def test_engineering_caller_sees_both_engineering_docs(self):
        resp = self.index.search(self.query, self.engineering_caller, top_k=2)
        self.assertEqual({r.doc_id for r in resp.results}, {"eng-1", "eng-2"})
        self.assertEqual(resp.total_count, 2)

    # --- The three leaks, same scenario, naive_post_filter_search ---

    def test_leak_1_total_count_includes_unauthorized_documents(self):
        correct = self.index.search(self.query, self.finance_caller, top_k=2)
        naive = naive_post_filter_search(self.index, self.query, self.finance_caller, top_k=2)
        self.assertEqual(correct.total_count, 1)
        self.assertEqual(naive.total_count, 3)  # leaks all 3 matches, 2 the caller can't see

    def test_leak_2_facet_counts_include_unauthorized_buckets(self):
        correct = self.index.search(self.query, self.finance_caller, top_k=2, facet_fields=("department",))
        naive = naive_post_filter_search(self.index, self.query, self.finance_caller, top_k=2,
                                          facet_fields=("department",))
        self.assertEqual(correct.facet_counts["department"], {"finance": 1})
        self.assertEqual(naive.facet_counts["department"], {"engineering": 2, "finance": 1})

    def test_leak_3_pagination_drops_the_authorized_match_entirely(self):
        """The sharpest leak: not an over-count, a real missing result.
        The finance caller's only visible, relevant document never reaches
        them at all under the naive approach."""
        correct = self.index.search(self.query, self.finance_caller, top_k=2)
        naive = naive_post_filter_search(self.index, self.query, self.finance_caller, top_k=2)
        self.assertEqual([r.doc_id for r in correct.results], ["fin-1"])
        self.assertEqual(naive.results, ())  # dropped, not merely ranked lower

    def test_leak_3_does_not_occur_with_a_large_enough_top_k(self):
        """Confirms leak 3 is specifically a truncation-order bug, not a
        permanent property of the naive function — with top_k large
        enough to cover the whole unfiltered corpus, the authorized
        document survives the later ACL filter (though the count/facet
        leaks from the other two tests still apply)."""
        naive = naive_post_filter_search(self.index, self.query, self.finance_caller, top_k=10)
        self.assertEqual([r.doc_id for r in naive.results], ["fin-1"])


class TestMultiGroupMembership(unittest.TestCase):
    def test_caller_in_multiple_groups_sees_union_of_access(self):
        index = SecurityTrimmedIndex()
        index.add(Document(id="a", text="budget forecast", allowed_group_ids=frozenset({"finance"})))
        index.add(Document(id="b", text="budget forecast", allowed_group_ids=frozenset({"legal"})))
        index.add(Document(id="c", text="budget forecast", allowed_group_ids=frozenset({"hr"})))
        resp = index.search("budget forecast", {"finance", "legal"}, top_k=10)
        self.assertEqual({r.doc_id for r in resp.results}, {"a", "b"})
        self.assertNotIn("c", {r.doc_id for r in resp.results})

    def test_caller_with_no_matching_group_sees_nothing(self):
        index = SecurityTrimmedIndex()
        index.add(Document(id="a", text="budget forecast", allowed_group_ids=frozenset({"finance"})))
        resp = index.search("budget forecast", {"marketing"}, top_k=10)
        self.assertEqual(resp.results, ())
        self.assertEqual(resp.total_count, 0)


class TestNoMatchesAndEmptyIndex(unittest.TestCase):
    def test_no_query_term_matches_anything(self):
        index = SecurityTrimmedIndex()
        index.add(Document(id="a", text="unrelated content entirely", allowed_group_ids=frozenset({"finance"})))
        resp = index.search("budget forecast", {"finance"}, top_k=10)
        self.assertEqual(resp.results, ())
        self.assertEqual(resp.total_count, 0)

    def test_empty_index(self):
        index = SecurityTrimmedIndex()
        resp = index.search("anything", {"finance"}, top_k=10)
        self.assertEqual(resp.results, ())
        self.assertEqual(resp.total_count, 0)
        self.assertEqual(resp.facet_counts, {})


if __name__ == "__main__":
    unittest.main()
