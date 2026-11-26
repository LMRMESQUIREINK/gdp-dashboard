"""Flags a bundle of source PDFs whose creation dates span suspiciously far
apart, or whose own forward-looking forecasts have already lapsed relative to
a given 'as of' date.

Built from a real finding: a 3-PDF Cloudera/Microsoft bundle uploaded together
with no accompanying note turned out to span three different vintages (a 2019
edge/IoT ebook forecasting "30 billion connected devices by 2020", a 2022
ebook, and a brand-new 2026 survey report) -- confirmed directly from each
PDF's own CreationDate metadata, not guessed from content.
"""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PdfRecord:
    name: str
    creation_date: date


@dataclass(frozen=True)
class VintageFinding:
    kind: str  # "spread" | "lapsed_forecast"
    detail: str


def check_spread(pdfs: list[PdfRecord], max_spread_days: int = 730) -> list[VintageFinding]:
    """Flags when the oldest and newest PDF in a bundle are more than
    max_spread_days apart (default: 2 years)."""
    if len(pdfs) < 2:
        return []
    oldest = min(pdfs, key=lambda p: p.creation_date)
    newest = max(pdfs, key=lambda p: p.creation_date)
    spread = (newest.creation_date - oldest.creation_date).days
    if spread > max_spread_days:
        return [
            VintageFinding(
                "spread",
                f"{oldest.name} ({oldest.creation_date.isoformat()}) and "
                f"{newest.name} ({newest.creation_date.isoformat()}) are "
                f"{spread} days apart ({spread / 365.25:.1f} years), over the "
                f"{max_spread_days / 365.25:.1f}-year threshold.",
            )
        ]
    return []


def check_lapsed_forecasts(
    pdfs_with_forecast_years: list[tuple[PdfRecord, int]], as_of: date
) -> list[VintageFinding]:
    """Flags any PDF that states a forward-looking forecast for a year
    already in the past relative to as_of."""
    findings = []
    for pdf, forecast_year in pdfs_with_forecast_years:
        if forecast_year < as_of.year:
            findings.append(
                VintageFinding(
                    "lapsed_forecast",
                    f"{pdf.name} (created {pdf.creation_date.isoformat()}) states "
                    f"a forward-looking forecast for {forecast_year}, which is "
                    f"{as_of.year - forecast_year} year(s) in the past as of "
                    f"{as_of.isoformat()}.",
                )
            )
    return findings
