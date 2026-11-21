import unittest

from plan_guard import ApprovalPolicy, PlanRejected, check_program, run_checked

NAMES = {"data", "double", "total"}


class TestCheckProgramAcceptsValidPlans(unittest.TestCase):
    def test_a_small_valid_program_passes(self):
        src = "found = []\nfor x in data:\n    found.append(double(x))\nresult = total(found)"
        self.assertEqual(check_program(src, NAMES), [])

    def test_comprehensions_and_conditionals_are_allowed(self):
        src = "picked = [x for x in data if x > 0]\nresult = total(picked) if picked else 0"
        self.assertEqual(check_program(src, NAMES), [])


class TestCheckProgramRejectsBadSyntax(unittest.TestCase):
    def test_a_while_loop_is_rejected_with_a_reason(self):
        problems = check_program("i = 0\nwhile i < 10:\n    i = i + 1\nresult = i", NAMES)
        self.assertTrue(any("While" in p and "range" in p for p in problems))

    def test_an_import_is_rejected(self):
        problems = check_program("import os\nresult = 1", NAMES)
        self.assertTrue(any("Import" in p for p in problems))

    def test_a_try_block_is_rejected(self):
        src = "try:\n    result = double(data)\nexcept Exception:\n    result = None"
        self.assertTrue(any("Try" in p for p in check_program(src, NAMES)))

    def test_an_oversized_integer_literal_is_rejected(self):
        problems = check_program("for i in range(5000000):\n    pass\nresult = i", NAMES)
        self.assertTrue(any("5000000" in p for p in problems))

    def test_not_valid_python_is_rejected(self):
        problems = check_program("result = (", NAMES)
        self.assertTrue(problems and "not valid Python" in problems[0])

    def test_program_over_the_line_limit_is_rejected(self):
        src = "\n".join(f"x{i} = {i}" for i in range(100)) + "\nresult = 1"
        problems = check_program(src, NAMES, max_lines=80)
        self.assertTrue(problems and "lines" in problems[0])


class TestCheckProgramRejectsBadMethodsAndNames(unittest.TestCase):
    def test_a_disallowed_method_call_is_rejected(self):
        problems = check_program("result = data.__class__", NAMES)
        self.assertTrue(any("__class__" in p for p in problems))

    def test_an_arbitrary_method_not_on_the_whitelist_is_rejected(self):
        problems = check_program("data.eval()\nresult = 1", NAMES)
        self.assertTrue(any("'.eval'" in p for p in problems))

    def test_an_undefined_name_is_rejected(self):
        problems = check_program("result = mystery_function(data)", NAMES)
        self.assertTrue(any("mystery_function" in p for p in problems))

    def test_reassigning_a_plan_language_name_is_rejected(self):
        problems = check_program("data = []\nresult = data", NAMES)
        self.assertTrue(any("'data'" in p and "cannot be reassigned" in p for p in problems))

    def test_an_underscore_prefixed_name_is_rejected(self):
        problems = check_program("_secret = 1\nresult = _secret", NAMES)
        self.assertTrue(any("_secret" in p for p in problems))

    def test_a_lone_underscore_is_allowed(self):
        src = "found = []\nfor _ in range(3):\n    found.append(1)\nresult = total(found)"
        self.assertEqual(check_program(src, NAMES), [])

    def test_an_empty_loop_body_is_allowed(self):
        # ast.Pass was found missing from the real source's own whitelist while writing this test;
        # added deliberately here (see the comment on ALLOWED_NODE_TYPES)
        src = "for _ in range(3):\n    pass\nresult = 1"
        self.assertEqual(check_program(src, NAMES), [])

    def test_missing_result_assignment_is_rejected(self):
        problems = check_program("found = double(data)", NAMES)
        self.assertTrue(any("never assigns" in p for p in problems))


class TestRunChecked(unittest.TestCase):
    def test_a_valid_program_actually_runs_and_returns_result(self):
        env = {"data": [1, 2, 3], "double": lambda x: x * 2, "total": sum}
        src = "found = [double(x) for x in data]\nresult = total(found)"
        self.assertEqual(run_checked(src, env, NAMES), 12)

    def test_a_rejected_program_never_executes(self):
        ran = []
        env = {"data": [1], "double": lambda x: ran.append(x) or x, "total": sum}
        with self.assertRaises(PlanRejected):
            run_checked("import os\nresult = double(data[0])", env, NAMES)
        self.assertEqual(ran, [], "a rejected program must never reach exec()")

    def test_the_runaway_style_loop_from_the_source_passes_this_static_check(self):
        # the real source's own text about this exact example: "runaway passes the rules: True" --
        # a bare loop bound of one million is not "larger than" the limit, so the static whitelist
        # alone cannot catch it; the real system relies on a separate runtime worker-count backstop
        # (its MAX_AGENTS_PER_RUN cap) that this module deliberately does not reimplement, since its
        # own scope is the static checker and the approval gate, not the runtime. Documented here as
        # a real, honest limitation rather than silently assumed closed.
        env = {"data": [], "double": lambda x: x, "total": sum, "agent": lambda *a, **k: None}
        src = "for i in range(1000000):\n    agent('look again')\nresult = []"
        self.assertEqual(check_program(src, NAMES | {"agent"}), [])


class TestApprovalPolicy(unittest.TestCase):
    def setUp(self):
        self.policy = ApprovalPolicy(max_credits=40.0, max_share=1 / 3)

    def test_a_cheap_plan_is_approved_automatically(self):
        decision, reason = self.policy.decide({"credits": 10.1}, budget=150)
        self.assertEqual(decision, "approved")
        self.assertIn("under the automatic limit", reason)

    def test_a_plan_over_the_whole_budget_is_refused(self):
        decision, reason = self.policy.decide({"credits": 200.0}, budget=150)
        self.assertEqual(decision, "refused")
        self.assertIn("more than the whole budget", reason)

    def test_a_plan_between_the_limit_and_the_budget_is_held_with_no_person(self):
        decision, reason = self.policy.decide({"credits": 50.0}, budget=150)
        self.assertEqual(decision, "held")
        self.assertIn("a person must approve", reason)

    def test_a_person_can_approve_a_held_plan(self):
        decision, reason = self.policy.decide({"credits": 50.0}, budget=150, person=lambda est: True)
        self.assertEqual(decision, "approved")
        self.assertIn("approved it", reason)

    def test_a_person_can_refuse_a_held_plan(self):
        decision, reason = self.policy.decide({"credits": 50.0}, budget=150, person=lambda est: False)
        self.assertEqual(decision, "refused")
        self.assertIn("refused it", reason)

    def test_a_failed_estimate_is_refused_without_reading_the_budget(self):
        decision, reason = self.policy.decide(None, budget=150)
        self.assertEqual(decision, "refused")
        self.assertIn("failed its check", reason)

    def test_the_automatic_limit_scales_with_the_budget_share(self):
        # a small budget's third can be below max_credits
        decision, _ = self.policy.decide({"credits": 20.0}, budget=45)   # limit = min(40, 15) = 15
        self.assertEqual(decision, "held")
        decision, _ = self.policy.decide({"credits": 10.0}, budget=45)
        self.assertEqual(decision, "approved")


if __name__ == "__main__":
    unittest.main()
