"""Tests for experience_library.py -- including the real "attack" that
reproduces the gap found in google-research/harness2's actual design
(ExperienceLibrary.retain() trusts its caller completely, same as the
real Library.retain()) and proves OrderedStream closes it structurally.

Run with: python3 test_experience_library.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from experience_library import ExperienceLibrary, OrderedStream, OutOfOrderError  # noqa: E402

passed = 0
failed = 0


def check(cond, name, detail=""):
    global passed, failed
    if cond:
        passed += 1
        print("ok   - " + name)
    else:
        failed += 1
        print("FAIL - " + name + (f" ({detail})" if detail else ""))


# --- Basic add/retain round trip, matching the real Library's contract ---
lib = ExperienceLibrary(domain="debugging")
lib.add("task-a", "harness-a", "why-a", lesson="lesson-a")
lib.add("task-b", "harness-b", "why-b", lesson="lesson-b")
lib.add("task-c", "harness-c", "why-c")
check(len(lib.all_entries()) == 3, "three added entries are all present")
check(lib.entries["task-c"].lesson is None, "a task with no lesson stores None, matching the real has_experience() gate's optional lesson field")

lib.retain(["task-a", "task-b"])
check(set(lib.entries) == {"task-a", "task-b"}, "retain() keeps exactly the listed task ids and drops the rest, matching the real Library.retain()'s contract")

ctx = lib.context_for(["task-b", "task-a"])
check([e.task_id for e in ctx] == ["task-b", "task-a"], "context_for() returns entries in the ORDER the caller asked for, not insertion order", [e.task_id for e in ctx])

# --- THE real gap, reproduced: retain() trusts an arbitrary list, so a --
# caller that (by mistake) includes a LATER task's id leaks it. ----------
lib2 = ExperienceLibrary(domain="debugging")
lib2.add("task-1", "h1", "w1", lesson="lesson from task 1")
lib2.add("task-2", "h2", "w2", lesson="lesson from task 2 -- should not be visible to task 1")
lib2.add("task-3", "h3", "w3", lesson="lesson from task 3")
# A caller processing task-1 SHOULD retain(["​"]) (nothing before it), but
# passes the wrong slice (includes task-3, which runs after task-1) --
# exactly the kind of off-by-one the real schedule.py's own
# `task_ids[: i - 1]` could get wrong at a different, hypothetical call site.
lib2.retain(["task-1", "task-3"])  # WRONG: task-3 hasn't "happened yet" relative to task-1
leaked = lib2.context_for(["task-1", "task-3"])
check(any(e.task_id == "task-3" for e in leaked), "reproduced: a naive ExperienceLibrary.retain() call CAN leak a future task's entry if the caller's slice is wrong -- the real design's real gap, not a strawman", [e.task_id for e in leaked])

# --- OrderedStream closes the gap structurally --------------------------
lib3 = ExperienceLibrary(domain="debugging")
stream = OrderedStream(lib3, task_order=["task-1", "task-2", "task-3", "task-4"])

seen_at_each_step = {}


def process(task_id, prior_entries):
    seen_at_each_step[task_id] = [e.task_id for e in prior_entries]
    return {"harness_summary": f"harness-for-{task_id}", "why": f"why-{task_id}", "lesson": f"lesson-from-{task_id}"}


stream.run("task-1", process)
stream.run("task-2", process)
stream.run("task-3", process)
stream.run("task-4", process)

check(seen_at_each_step["task-1"] == [], "task-1 (the first task in the stream) sees no prior entries")
check(seen_at_each_step["task-2"] == ["task-1"], "task-2 sees only task-1's entry")
check(seen_at_each_step["task-3"] == ["task-1", "task-2"], "task-3 sees task-1 and task-2, in order, but never task-4 (which hasn't run yet)")
check(seen_at_each_step["task-4"] == ["task-1", "task-2", "task-3"], "task-4 sees everything strictly before it")
check(stream.done, "the stream reports done after its last declared task")

# --- OrderedStream refuses out-of-order processing -----------------------
stream2 = OrderedStream(ExperienceLibrary(domain="d2"), task_order=["a", "b", "c"])
try:
    stream2.run("b", process)  # skipping "a"
    check(False, "running a non-next task raises OutOfOrderError", "no exception")
except OutOfOrderError as e:
    check("expected" in str(e) and "'a'" in str(e), "OutOfOrderError names the actually-expected next task", str(e))

stream3 = OrderedStream(ExperienceLibrary(domain="d3"), task_order=["a", "b"])
stream3.run("a", process)
stream3.run("b", process)
try:
    stream3.run("a", process)  # already exhausted
    check(False, "running past the end of an exhausted stream raises", "no exception")
except OutOfOrderError:
    check(True, "an exhausted stream refuses a further run() call rather than silently reprocessing")

# --- A process_fn returning None (no transferable lesson) records nothing,
# matching the real Library.add()'s has_experience() gate ------------------
stream4 = OrderedStream(ExperienceLibrary(domain="d4"), task_order=["x", "y"])
stream4.run("x", lambda tid, prior: None)
stream4.run("y", lambda tid, prior: {"harness_summary": "h", "why": "w"})
check("x" not in stream4.library.entries, "a task whose process_fn returns None records nothing in the library")
check("y" in stream4.library.entries, "a task whose process_fn returns a real result IS recorded")

# --- Duplicate task ids in task_order are rejected at construction, not
# discovered later mid-stream ---------------------------------------------
try:
    OrderedStream(ExperienceLibrary(domain="d5"), task_order=["a", "b", "a"])
    check(False, "a task_order with a duplicate id raises at construction", "no exception")
except ValueError:
    check(True, "a duplicate task id in task_order is rejected immediately, not discovered mid-stream")

print(f"\n{passed} passed, {failed} failed.")
if failed:
    sys.exit(1)
