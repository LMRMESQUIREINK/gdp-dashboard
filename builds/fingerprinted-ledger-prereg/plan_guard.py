"""A restricted-plan-language checker plus a price-then-approve gate.

Independently reimplemented (not copied) from reading the real notebook behind
FareedKhan-dev/dynamic-workflow-agents: a lead model writes a short Python
"plan" that a runtime then executes with real workers. Before any worker is
started, the plan is (1) checked against an AST whitelist so it can only call
a few given names and methods, never arbitrary Python, then (2) rehearsed
against a free stand-in to get a cost estimate, then (3) run through a policy
that auto-approves a cheap plan, refuses an unaffordable one, and holds
anything in between for a human. This module covers (1) and (3) — the
generalizable, model-free halves; (2) needs a real stand-in model to rehearse
against and is not reproduced here.

Known limitation, inherited from the real source rather than introduced here:
a loop bound of exactly one million passes the oversized-literal check (it is
not "larger than" the limit), so the static whitelist alone cannot refuse the
real source's own worst-case runaway example. The real system catches that
case only at dry-run time, via a separate runtime worker-count cap this
module does not reimplement -- see test_plan_guard.py's own test naming this
directly, and the real source's text, which says of this exact example:
"runaway passes the rules: True."
"""
import ast
import builtins as _builtins_module

MAX_INT_LITERAL = 1_000_000  # no plan needs a bound bigger than this -- but this check alone does NOT
# catch a loop bound of exactly one million (not "larger than"), the real source's own hostile example;
# that one is caught only by a separate runtime worker-count backstop this module does not implement

# a safe subset of syntax: no Import, While, Try, With, Global, Lambda-body side effects, etc.
# Pass is added deliberately on top of the real source's own whitelist, found missing while testing
# this module (an empty for-loop body, e.g. "for _ in range(n): pass", is otherwise harmless and the
# real notebook's own ALLOWED_NODES set omits it) -- a one-line, backward-compatible widening, not a
# silent fix of code this project does not own.
ALLOWED_NODE_TYPES = {getattr(ast, n) for n in (
    "Module Expr Assign AugAssign For If Break Continue Return FunctionDef Lambda ListComp DictComp "
    "SetComp GeneratorExp comprehension Call keyword Name Attribute Subscript Slice Constant List Tuple "
    "Dict Set BoolOp BinOp UnaryOp Compare IfExp JoinedStr FormattedValue arguments arg Starred Load Store "
    "And Or Add Sub Mult Div FloorDiv Mod Not USub UAdd Eq NotEq Lt LtE Gt GtE In NotIn Is IsNot Pass"
).split()}

WHY_NOT_ALLOWED = {
    ast.While: "use a for loop over range(n) instead, so the loop states its own bound",
    ast.Import: "a plan has nothing to import",
    ast.ImportFrom: "a plan has nothing to import",
    ast.Try: "a plan must not hide errors",
    ast.With: "a plan has no resources to open",
    ast.Global: "a plan has no module scope to reach into",
    ast.ClassDef: "a plan defines no classes",
}

DEFAULT_METHODS = {"append", "extend", "get", "items", "keys", "values", "update", "add", "setdefault",
                    "pop", "sort", "split", "strip", "lower", "upper", "join", "startswith", "endswith",
                    "count", "index", "replace"}

DEFAULT_BUILTINS = {"len", "range", "enumerate", "zip", "sorted", "min", "max", "sum", "any", "all",
                     "list", "dict", "set", "tuple", "str", "int", "float", "round", "abs"}


class PlanRejected(ValueError):
    """A plan program failed the whitelist check."""


def _rule_syntax(tree, allowed_methods):
    """Only whitelisted syntax, no oversized integer literal, and only whitelisted method calls."""
    called = {id(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    problems = []
    for node in ast.walk(tree):
        line = getattr(node, "lineno", 1)
        if type(node) not in ALLOWED_NODE_TYPES:
            why = WHY_NOT_ALLOWED.get(type(node), "it is not part of the plan language")
            problems.append(f"line {line}: {type(node).__name__} is not allowed: {why}")
        elif isinstance(node, ast.Constant) and type(node.value) is int and abs(node.value) > MAX_INT_LITERAL:
            problems.append(f"line {line}: the number {node.value} is larger than any plan needs")
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("_") or id(node) not in called or node.attr not in allowed_methods:
                problems.append(f"line {line}: '.{node.attr}' is not allowed: a plan may only call "
                                 f"{', '.join(sorted(allowed_methods))} on data")
    return problems


def _rule_names(tree, allowed_names):
    """Only the given names may be read, none starting with an underscore, and the language's own
    names may never be reassigned."""
    bound = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    bound |= {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    bound |= {n.arg for n in ast.walk(tree) if isinstance(n, ast.arg)}
    problems = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            name, stored = node.id, isinstance(node.ctx, ast.Store)
        elif isinstance(node, ast.FunctionDef):
            name, stored = node.name, True
        elif isinstance(node, ast.arg):
            name, stored = node.arg, True
        else:
            continue
        if name.startswith("_") and name != "_":
            problems.append(f"line {node.lineno}: the name '{name}' starts with an underscore, which is not allowed")
        elif stored and name in allowed_names:
            problems.append(f"line {node.lineno}: '{name}' is part of the plan language and cannot be reassigned")
        elif not stored and name not in allowed_names | DEFAULT_BUILTINS | bound:
            problems.append(f"line {node.lineno}: the name '{name}' is not defined: the plan language has no such name")
    return sorted(set(problems), key=lambda s: int(s.split(":")[0][5:]))


def check_program(src, allowed_names, *, allowed_methods=DEFAULT_METHODS, max_lines=80, max_chars=6000,
                   result_var="result"):
    """Every problem with a plan program, by line. An empty list means it may go on to be rehearsed."""
    if len(src) > max_chars or len(src.splitlines()) > max_lines:
        return [f"line 1: the program has {len(src.splitlines())} lines and {len(src)} characters, "
                f"and the limit is {max_lines} and {max_chars}"]
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [f"line {e.lineno}: this is not valid Python ({e.msg})"]
    assigns_result = any(isinstance(n, ast.Name) and n.id == result_var and isinstance(n.ctx, ast.Store)
                          for n in ast.walk(tree))
    problems = _rule_syntax(tree, allowed_methods) + _rule_names(tree, set(allowed_names))
    if not assigns_result:
        problems.append(f"line 1: the program never assigns `{result_var}`")
    return problems


def run_checked(src, env, allowed_names, *, allowed_methods=DEFAULT_METHODS, max_lines=80, max_chars=6000,
                 result_var="result"):
    """Run a plan program only after it passes check_program, with nothing in scope but `env`'s names
    and a small safe set of builtins. Raises PlanRejected before anything executes if it fails."""
    problems = check_program(src, allowed_names, allowed_methods=allowed_methods, max_lines=max_lines,
                              max_chars=max_chars, result_var=result_var)
    if problems:
        raise PlanRejected(" | ".join(problems[:5]))
    scope = dict(env, __builtins__={n: getattr(_builtins_module, n) for n in DEFAULT_BUILTINS})
    exec(compile(src, "<plan>", "exec"), scope)
    return scope.get(result_var)


class ApprovalPolicy:
    """A plan is approved automatically under a limit fixed before any plan was priced, refused if it
    costs more than the whole budget, and otherwise held for a person."""

    def __init__(self, max_credits, max_share):
        self.max_credits, self.max_share = max_credits, max_share

    def decide(self, estimate, budget, person=None):
        if estimate is None:
            return "refused", "the plan failed its check or its rehearsal"
        if estimate["credits"] > budget:
            return "refused", f"estimated {estimate['credits']:.1f} credits is more than the whole budget of {budget:.0f}"
        limit = min(self.max_credits, self.max_share * budget)
        cost = f"estimated {estimate['credits']:.1f} credits"
        if estimate["credits"] <= limit:
            return "approved", f"{cost} is under the automatic limit of {limit:.1f}"
        if person is None:
            return "held", f"{cost} is over the automatic limit of {limit:.1f}, so a person must approve it"
        yes = bool(person(estimate))
        return ("approved" if yes else "refused"), f"a person {'approved' if yes else 'refused'} it after reading the {cost}"
