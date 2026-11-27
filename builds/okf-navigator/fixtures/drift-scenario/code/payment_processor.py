"""A tiny, real, synthetic module used only by test_staleness_value.py
to demonstrate that okf_navigator's stale_after mechanism actually
gates something meaningful -- not a product file."""
def charge(amount_cents: int) -> dict:
    return {"charged": amount_cents}
