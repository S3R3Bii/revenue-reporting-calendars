"""Qualified saved-cohort fiscal-slot forecasts with explicit abstention."""

from common import ROOT, load, rows, save
from model import fitting, forecast


def answer(request):
    if set(request) != {"scope", "pair_id", "model", "origin"}:
        return dict(status="REJECT", reason="unsupported fields or incomplete request")
    if request["scope"] != "reported_fiscal_slot_forecast":
        return dict(
            status="REJECT",
            reason="unsupported claim; no investment, source-truth or exact future-date certification",
        )
    if request["model"] not in ["zero", "global", "fiscal", "calendar"]:
        return dict(status="REJECT", reason="model outside fixed exercise")
    pairs = rows(ROOT / "results/pairs.csv")
    matches = [
        r
        for r in pairs
        if r["id"] == request["pair_id"] and "2025-01-01" <= r["end"] <= "2026-06-30"
    ]
    if len(matches) != 1:
        return dict(status="ABSTAIN", reason="no unique saved test fiscal slot")
    r = matches[0]
    if request["origin"] != r["origin"]:
        return dict(
            status="ABSTAIN", reason="origin does not match saved availability contract"
        )
    fit = fitting(pairs, r["origin"], "test")
    f = request["model"]
    alpha = load("results/selection.json")["selected_alpha"].get(f, 0)
    if len(fit) < 3:
        return dict(status="ABSTAIN", reason="insufficient available training labels")
    return dict(
        status="QUALIFIED",
        forecast_usd=str(
            forecast(r["prior"], r["fp"], r["calendar_quarter"], fit, f, alpha)
        ),
        prior_usd=r["prior"],
        origin=r["origin"],
        known_fp=r["fp"],
        calendar_quarter=r["calendar_quarter"],
        fit_ids=[v["id"] for v in fit],
        qualification="Conditional current-source filing-day reconstruction and persistent fiscal-slot assumption; not immutable production-vintage or investment evidence.",
    )


def main(out):
    save(
        out / "exercise.json",
        [dict(request=r, response=answer(r)) for r in load("data/requests.json")],
    )


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=ROOT / "results")
    main(p.parse_args().out)
