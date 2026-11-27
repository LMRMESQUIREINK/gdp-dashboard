"""Imports payment_processor.py -- the one real edge this scenario's
OKF bundle documents."""
from payment_processor import charge


def complete_checkout(amount_cents: int) -> dict:
    return charge(amount_cents)
