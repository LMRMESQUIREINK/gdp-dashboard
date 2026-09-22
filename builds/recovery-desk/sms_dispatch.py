"""
Recovery Desk — SMS dispatch.

Sends the morning decision text via Twilio. Same fail-fast pattern as
data_pipeline.py: a placeholder credential fails locally and
immediately, not as a confusing remote 401 after a wasted round trip.
No live Twilio account in this sandbox — send_decision_text() is a
real, complete implementation but untested live; print_decision_text()
is what every test/demo in this build actually exercises.
"""

import os

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "YOUR_TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "YOUR_TWILIO_AUTH_TOKEN")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "YOUR_TWILIO_FROM_NUMBER")

DISCLAIMER = (
    "Recovery Desk is not a medical device and doesn't diagnose or "
    "treat anything. Reply STOP to cancel."
)


def _require_config(value: str, env_var: str, placeholder: str) -> None:
    if not value or value == placeholder:
        raise RuntimeError(
            f"{env_var} is not set. Set it before running, e.g.:\n"
            f"  bash/macOS/Linux : export {env_var}=\"your_value_here\"\n"
            f"  Windows PowerShell: setx {env_var} \"your_value_here\"\n"
            f"(then restart your terminal so the new value is picked up)"
        )


def format_message(decision_text: str, reason: str, is_anomaly: bool) -> str:
    """The actual text a subscriber receives — decision, one-line why,
    and the disclaimer, every single time (not just on anomaly days)."""
    body = f"{decision_text} {reason}"
    if is_anomaly:
        # Anomaly messages already read as a caution; no need to also
        # look like a normal training tip underneath it.
        return f"{body}\n\n{DISCLAIMER}"
    return f"{body}\n\n{DISCLAIMER}"


def send_decision_text(to_number: str, decision_text: str, reason: str, is_anomaly: bool) -> dict:
    """Send the formatted message via Twilio. Requires a live account —
    fails fast locally if the credentials are still placeholders."""
    _require_config(TWILIO_ACCOUNT_SID, "TWILIO_ACCOUNT_SID", "YOUR_TWILIO_ACCOUNT_SID")
    _require_config(TWILIO_AUTH_TOKEN, "TWILIO_AUTH_TOKEN", "YOUR_TWILIO_AUTH_TOKEN")
    _require_config(TWILIO_FROM_NUMBER, "TWILIO_FROM_NUMBER", "YOUR_TWILIO_FROM_NUMBER")

    from twilio.rest import Client  # imported here so this module loads without twilio installed until actually sending

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=format_message(decision_text, reason, is_anomaly),
        from_=TWILIO_FROM_NUMBER,
        to=to_number,
    )
    return {"sid": message.sid, "status": message.status}


def print_decision_text(decision_text: str, reason: str, is_anomaly: bool) -> str:
    """What every test/demo in this build actually uses instead of a
    live send — the exact message body a real subscriber would get."""
    formatted = format_message(decision_text, reason, is_anomaly)
    print(f"\nRecovery Desk — morning text\n{'─' * 40}\n{formatted}\n{'─' * 40}")
    return formatted
