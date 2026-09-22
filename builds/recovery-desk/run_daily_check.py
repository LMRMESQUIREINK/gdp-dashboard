"""
Recovery Desk — CLI entry point.

Usage:
    python run_daily_check.py --demo train_hard
    python run_daily_check.py --demo back_off
    python run_daily_check.py --demo eat_more
    python run_daily_check.py --demo sleep_earlier
    python run_daily_check.py --demo anomaly

    python run_daily_check.py --provider oura --to +15551234567
    python run_daily_check.py --provider whoop --to +15551234567

--demo runs the full fetch->decide->format pipeline against a
synthetic reading, prints the exact message body a subscriber would
get, and never touches Twilio. --provider is the real path (Oura or
Whoop, live send) — requires OURA_API_TOKEN/WHOOP_API_TOKEN and the
three TWILIO_* env vars; both fail fast locally if left as
placeholders, same pattern as every other build in this project.
"""

import argparse

from data_pipeline import fetch_oura_reading, fetch_whoop_reading, synthetic_reading
from decision_engine import decide
from sms_dispatch import print_decision_text, send_decision_text


def run(reading, to_number: str = None, live_send: bool = False) -> None:
    result = decide(reading)
    if live_send:
        response = send_decision_text(to_number, result.text, result.reason, result.is_anomaly)
        print(f"Sent — Twilio SID {response['sid']}, status {response['status']}")
    else:
        print_decision_text(result.text, result.reason, result.is_anomaly)
    print(f"\nDecision: {result.decision.value}" + (" (ANOMALY)" if result.is_anomaly else ""))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recovery Desk — daily decision text.")
    parser.add_argument("--demo", choices=["train_hard", "back_off", "eat_more", "sleep_earlier", "anomaly"],
                         help="Run against a synthetic reading and print the message (no Twilio).")
    parser.add_argument("--provider", choices=["oura", "whoop"], help="Fetch a real reading and send live.")
    parser.add_argument("--to", help="Destination phone number, required with --provider.")
    args = parser.parse_args()

    if args.demo:
        run(synthetic_reading(args.demo))
    elif args.provider:
        if not args.to:
            parser.error("--provider needs --to")
        reading = fetch_oura_reading() if args.provider == "oura" else fetch_whoop_reading()
        run(reading, to_number=args.to, live_send=True)
    else:
        parser.error("Specify --demo SCENARIO or --provider oura/whoop --to NUMBER")
