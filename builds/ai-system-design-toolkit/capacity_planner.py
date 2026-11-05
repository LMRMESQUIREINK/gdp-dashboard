"""Real implementation of the capacity-planning math from "AI System
Design: A Practical Guide to Production AI" (Piyush Kashyap) Section 3 --
read in full, every worked number independently recomputed by hand before
this was written (see /notes/ai-system-design-guide-analysis.md).

Deliberately kept to exactly the formulas the source states, not extended
with anything it doesn't cover: daily request volume, average and peak
requests per second, Little's Law concurrency, daily/monthly token
consumption, and a monthly cost estimate from per-million-token pricing.
This is a sizing calculator for an AI application's OWN backend -- not a
trading risk tool like this project's prop-firm-sizing family, which is
the gap this build fills.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Workload:
    """The assumptions a capacity estimate is built from -- kept together
    so a plan always states exactly what it assumed, per the source
    article's own repeated caution that these numbers are "estimates, not
    fixed capacity requirements."""

    users: int
    requests_per_user_per_day: float
    working_hours_per_day: float
    working_days_per_month: int
    peak_multiplier: float
    avg_input_tokens_per_request: float
    avg_output_tokens_per_request: float
    price_per_million_input_tokens: float
    price_per_million_output_tokens: float

    def __post_init__(self):
        for name in (
            "users",
            "requests_per_user_per_day",
            "working_hours_per_day",
            "working_days_per_month",
            "peak_multiplier",
            "avg_input_tokens_per_request",
            "avg_output_tokens_per_request",
            "price_per_million_input_tokens",
            "price_per_million_output_tokens",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative")
        if self.users == 0 or self.requests_per_user_per_day == 0:
            raise ValueError("a workload with zero users or zero requests has no capacity to plan")
        if self.working_hours_per_day <= 0:
            raise ValueError("working_hours_per_day must be positive")


@dataclass(frozen=True)
class CapacityPlan:
    daily_requests: float
    avg_requests_per_second: float
    peak_requests_per_second: float
    daily_input_tokens: float
    daily_output_tokens: float
    daily_total_tokens: float
    monthly_input_tokens: float
    monthly_output_tokens: float
    monthly_total_tokens: float
    monthly_input_cost: float
    monthly_output_cost: float
    monthly_total_cost: float

    def concurrency(self, avg_seconds_in_system: float) -> float:
        """Little's Law: L = lambda * W, applied to THIS plan's average
        requests-per-second against a caller-supplied average time a
        request spends in the system. Deliberately not folded into the
        plan itself -- unlike every other field here, "time in system" is
        not a workload assumption, it's a measured property of the
        running application, so it can't be known at planning time."""
        if avg_seconds_in_system < 0:
            raise ValueError("avg_seconds_in_system cannot be negative")
        return self.avg_requests_per_second * avg_seconds_in_system


def plan_capacity(workload: Workload) -> CapacityPlan:
    daily_requests = workload.users * workload.requests_per_user_per_day
    working_seconds_per_day = workload.working_hours_per_day * 60 * 60
    avg_rps = daily_requests / working_seconds_per_day
    peak_rps = avg_rps * workload.peak_multiplier

    daily_input_tokens = daily_requests * workload.avg_input_tokens_per_request
    daily_output_tokens = daily_requests * workload.avg_output_tokens_per_request
    daily_total_tokens = daily_input_tokens + daily_output_tokens

    monthly_input_tokens = daily_input_tokens * workload.working_days_per_month
    monthly_output_tokens = daily_output_tokens * workload.working_days_per_month
    monthly_total_tokens = monthly_input_tokens + monthly_output_tokens

    monthly_input_cost = (monthly_input_tokens / 1_000_000) * workload.price_per_million_input_tokens
    monthly_output_cost = (monthly_output_tokens / 1_000_000) * workload.price_per_million_output_tokens
    monthly_total_cost = monthly_input_cost + monthly_output_cost

    return CapacityPlan(
        daily_requests=daily_requests,
        avg_requests_per_second=avg_rps,
        peak_requests_per_second=peak_rps,
        daily_input_tokens=daily_input_tokens,
        daily_output_tokens=daily_output_tokens,
        daily_total_tokens=daily_total_tokens,
        monthly_input_tokens=monthly_input_tokens,
        monthly_output_tokens=monthly_output_tokens,
        monthly_total_tokens=monthly_total_tokens,
        monthly_input_cost=monthly_input_cost,
        monthly_output_cost=monthly_output_cost,
        monthly_total_cost=monthly_total_cost,
    )


def format_report(workload: Workload, plan: CapacityPlan) -> str:
    lines = [
        "Capacity plan",
        "=============",
        f"Assumptions: {workload.users:,} users x {workload.requests_per_user_per_day:g} req/day, "
        f"{workload.working_hours_per_day:g}h/day, {workload.working_days_per_month} working days/month, "
        f"{workload.peak_multiplier:g}x peak multiplier",
        "",
        f"Daily requests:        {plan.daily_requests:,.0f}",
        f"Avg requests/sec:      {plan.avg_requests_per_second:.4f}",
        f"Peak requests/sec:     {plan.peak_requests_per_second:.4f}",
        "",
        f"Daily input tokens:    {plan.daily_input_tokens:,.0f}",
        f"Daily output tokens:   {plan.daily_output_tokens:,.0f}",
        f"Daily total tokens:    {plan.daily_total_tokens:,.0f}",
        "",
        f"Monthly input tokens:  {plan.monthly_input_tokens:,.0f}",
        f"Monthly output tokens: {plan.monthly_output_tokens:,.0f}",
        f"Monthly total tokens:  {plan.monthly_total_tokens:,.0f}",
        "",
        f"Monthly input cost:    ${plan.monthly_input_cost:,.2f}",
        f"Monthly output cost:   ${plan.monthly_output_cost:,.2f}",
        f"Monthly total cost:    ${plan.monthly_total_cost:,.2f}",
    ]
    return "\n".join(lines)


def _build_arg_parser():
    import argparse

    parser = argparse.ArgumentParser(description="Size an AI application's backend from workload assumptions.")
    parser.add_argument("--users", type=int, required=True)
    parser.add_argument("--requests-per-user-per-day", type=float, required=True)
    parser.add_argument("--working-hours-per-day", type=float, default=8.0)
    parser.add_argument("--working-days-per-month", type=int, default=22)
    parser.add_argument("--peak-multiplier", type=float, default=8.0)
    parser.add_argument("--avg-input-tokens", type=float, required=True)
    parser.add_argument("--avg-output-tokens", type=float, required=True)
    parser.add_argument("--price-per-million-input", type=float, required=True)
    parser.add_argument("--price-per-million-output", type=float, required=True)
    parser.add_argument("--concurrency-avg-seconds", type=float, default=None, help="if set, also report Little's Law concurrency for this avg time-in-system")
    return parser


def main(argv=None):
    args = _build_arg_parser().parse_args(argv)
    try:
        workload = Workload(
            users=args.users,
            requests_per_user_per_day=args.requests_per_user_per_day,
            working_hours_per_day=args.working_hours_per_day,
            working_days_per_month=args.working_days_per_month,
            peak_multiplier=args.peak_multiplier,
            avg_input_tokens_per_request=args.avg_input_tokens,
            avg_output_tokens_per_request=args.avg_output_tokens,
            price_per_million_input_tokens=args.price_per_million_input,
            price_per_million_output_tokens=args.price_per_million_output,
        )
    except ValueError as e:
        print(f"Invalid workload: {e}")
        return 1
    plan = plan_capacity(workload)
    print(format_report(workload, plan))
    if args.concurrency_avg_seconds is not None:
        print(f"\nLittle's Law concurrency (avg {args.concurrency_avg_seconds:g}s in system): "
              f"{plan.concurrency(args.concurrency_avg_seconds):.2f} requests in flight on average")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
