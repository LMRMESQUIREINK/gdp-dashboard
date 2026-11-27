import json
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from provisional_gate import Claim, Leaf, combine, get_path, load_leaf_tree, publish_check

HERE = os.path.dirname(os.path.abspath(__file__))
REAL_EVAL = os.path.join(HERE, "fixtures", "transportive_eval.json")
REAL_CLAIMS = os.path.join(HERE, "fixtures", "transportive_claims.json")


def load_real_eval_tree():
    with open(REAL_EVAL, "r", encoding="utf-8") as f:
        return load_leaf_tree(json.load(f))


class TestLeafAndCombine(unittest.TestCase):
    def test_combine_both_confirmed_stays_confirmed(self):
        a, b = Leaf(3, False), Leaf(4, False)
        result = combine(a, b, fn=lambda x, y: x + y)
        self.assertEqual(result.value, 7)
        self.assertFalse(result.provisional)

    def test_combine_one_provisional_poisons_result(self):
        a, b = Leaf(3, False), Leaf(4, True)
        result = combine(a, b, fn=lambda x, y: x + y)
        self.assertEqual(result.value, 7)
        self.assertTrue(result.provisional)

    def test_combine_requires_at_least_one_leaf(self):
        with self.assertRaises(ValueError):
            combine(fn=lambda: 0)

    def test_combine_three_leaves_any_provisional_poisons(self):
        leaves = [Leaf(1, False), Leaf(2, False), Leaf(3, True)]
        result = combine(*leaves, fn=lambda *xs: sum(xs))
        self.assertTrue(result.provisional)


class TestLoadLeafTree(unittest.TestCase):
    def test_plain_dict_passes_through(self):
        tree = load_leaf_tree({"a": 1, "b": "text"})
        self.assertEqual(tree, {"a": 1, "b": "text"})

    def test_leaf_shape_becomes_leaf_object(self):
        tree = load_leaf_tree({"a": {"v": 5, "provisional": True}})
        self.assertIsInstance(tree["a"], Leaf)
        self.assertEqual(tree["a"].value, 5)
        self.assertTrue(tree["a"].provisional)

    def test_nested_leaves_recurse(self):
        tree = load_leaf_tree({"outer": {"inner": {"v": 1, "provisional": False}}})
        self.assertIsInstance(tree["outer"]["inner"], Leaf)

    def test_list_of_leaves(self):
        tree = load_leaf_tree([{"v": 1, "provisional": True}, {"v": 2, "provisional": False}])
        self.assertIsInstance(tree[0], Leaf)
        self.assertFalse(tree[1].provisional)

    def test_dict_that_happens_to_have_v_and_provisional_as_non_bool_not_treated_as_leaf(self):
        # provisional must be a real bool, not just any truthy value, to count as a leaf shape
        tree = load_leaf_tree({"v": 1, "provisional": "yes"})
        self.assertNotIsInstance(tree, Leaf)


class TestGetPath(unittest.TestCase):
    def test_real_headline_number_a4_opus_pass(self):
        tree = load_real_eval_tree()
        leaf = get_path(tree, "arms.A4.opus.pass")
        # the article's own headline claim: "the full machine passed 33 of 36 tickets with Opus"
        self.assertEqual(leaf.value, 33)
        self.assertTrue(leaf.provisional)

    def test_real_headline_number_a4_opus_n(self):
        tree = load_real_eval_tree()
        leaf = get_path(tree, "arms.A4.opus.n")
        self.assertEqual(leaf.value, 36)
        self.assertTrue(leaf.provisional)

    def test_real_a1_opus_baseline(self):
        tree = load_real_eval_tree()
        leaf = get_path(tree, "arms.A1.opus.pass")
        # the article's other headline claim: "17 for Opus with a plain prompt"
        self.assertEqual(leaf.value, 17)
        self.assertTrue(leaf.provisional)

    def test_missing_path_names_the_failing_segment(self):
        tree = load_real_eval_tree()
        with self.assertRaises(KeyError) as ctx:
            get_path(tree, "arms.A4.nonexistent_coder.pass")
        self.assertIn("nonexistent_coder", str(ctx.exception))

    def test_path_that_resolves_to_non_leaf_raises(self):
        tree = load_real_eval_tree()
        with self.assertRaises(KeyError):
            get_path(tree, "arms.A4")  # a dict of coders, not a leaf


class TestPublishCheckAgainstRealData(unittest.TestCase):
    """Reproduces the actual finding: every number in transportive-ai's
    real results/eval.json is provisional (the repo's own README says
    so), but the companion article presents dozens of them with zero
    disclosure, and discloses exactly one unrelated thing (the #19812
    severity caveat) at the very end."""

    def setUp(self):
        self.tree = load_real_eval_tree()

    def test_undisclosed_headline_claim_is_flagged(self):
        claim = Claim(
            "headline-33-of-36",
            "the full machine passed 33 of 36 tickets with Opus",
            get_path(self.tree, "arms.A4.opus.pass"),
        )
        violations = publish_check([claim], disclosed=set())
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0].claim_id, "headline-33-of-36")

    def test_same_claim_passes_once_actually_disclosed(self):
        claim = Claim(
            "headline-33-of-36",
            "the full machine passed 33 of 36 tickets with Opus",
            get_path(self.tree, "arms.A4.opus.pass"),
        )
        violations = publish_check([claim], disclosed={"headline-33-of-36"})
        self.assertEqual(violations, [])

    def test_confirmed_claim_never_needs_disclosure(self):
        # a Leaf built directly from confirmed inputs (not loaded from the
        # provisional real file) should never be flagged, disclosed or not
        confirmed = Leaf(1067371, False)
        claim = Claim("dataset-row-count", "1,067,371 lines from a UK shop", confirmed)
        self.assertEqual(publish_check([claim], disclosed=set()), [])
        self.assertEqual(publish_check([claim], disclosed={"dataset-row-count"}), [])

    def test_the_articles_full_set_of_headline_claims_mostly_undisclosed(self):
        # Reproduce the article's own reporting: six real headline numbers,
        # pulled from the actual provisional eval.json, with the article's
        # own real disclosure set (only the severity note, which isn't even
        # one of these numeric claims) -- so all six should be flagged.
        claims = [
            Claim("a4-opus-pass", "33 of 36 with the full machine, Opus", get_path(self.tree, "arms.A4.opus.pass")),
            Claim("a4-qwen-pass", "30 of 36 with the full machine, Qwen", get_path(self.tree, "arms.A4.qwen.pass")),
            Claim("a1-opus-pass", "17 of 36 with a plain prompt, Opus", get_path(self.tree, "arms.A1.opus.pass")),
            Claim("a1-qwen-pass", "12 of 36 with a plain prompt, Qwen", get_path(self.tree, "arms.A1.qwen.pass")),
            Claim("a1-opus-gw", "a 45% green-but-wrong rate for the plain Opus arm", get_path(self.tree, "arms.A1.opus.gw")),
            Claim("a4-opus-gw", "a 0% green-but-wrong rate for the full machine, Opus", get_path(self.tree, "arms.A4.opus.gw")),
        ]
        # the article's actual disclosure, carried over verbatim, covers a
        # different topic entirely (issue severity), so it discloses none
        # of these six numeric claims
        real_disclosure = {"issue-19812-severity"}
        violations = publish_check(claims, disclosed=real_disclosure)
        self.assertEqual(len(violations), 6)
        self.assertEqual({v.claim_id for v in violations}, {c.claim_id for c in claims})


if __name__ == "__main__":
    unittest.main(verbosity=2)
