"""Select on validation, commit that choice, then run the fixed protected test once."""

import argparse, subprocess
from pathlib import Path
from fractions import Fraction
from common import ROOT, rows, save, load, table, digest
from model import GRID, name, gates, predict, metrics


def validation(out):
    pairs = rows(ROOT / "results/pairs.csv")
    g = gates(pairs)
    predictions = predict(pairs, "validation", GRID)
    scores = metrics(predictions)
    table(out / "validation_predictions.csv", predictions)
    table(out / "validation_metrics.csv", scores)
    macros = {
        r["model"]: Fraction(r["mape"]) for r in scores if r["company"] == "MACRO"
    }
    chosen = {
        f: min([0, 1, 4, 16], key=lambda a: (macros[name(f, a)], a))
        for f in ["fiscal", "calendar"]
    }
    winner = min(GRID, key=lambda x: (macros[name(*x)], GRID.index(x)))
    selection = dict(
        selected_alpha=chosen,
        overall_validation_winner=name(*winner),
        selection_loss="equal-company macro MAPE",
        validation_sha256={
            n: digest(out / n)
            for n in ["validation_predictions.csv", "validation_metrics.csv"]
        },
        source_pairs_sha256=digest(ROOT / "results/pairs.csv"),
        freeze_sha256=digest(ROOT / "PLAN_FREEZE.json"),
        gates=g,
    )
    save(out / "selection.json", selection)
    print("VALIDATION_SELECTION", chosen, name(*winner))


def test(out, replay=False):
    s = load("results/selection.json")
    for n, h in s["validation_sha256"].items():
        assert digest(ROOT / "results" / n) == h
    assert (
        digest(ROOT / "PLAN_FREEZE.json") == s["freeze_sha256"]
        and digest(ROOT / "results/pairs.csv") == s["source_pairs_sha256"]
    )
    if not replay:
        for n in [
            "selection.json",
            "validation_predictions.csv",
            "validation_metrics.csv",
        ]:
            assert (
                subprocess.check_output(["git", "show", "HEAD:results/" + n], cwd=ROOT)
                == (ROOT / "results" / n).read_bytes()
            ), "commit selection before test"
        assert not (
            out / "test_predictions.csv"
        ).exists(), "protected test already exists; use separate replay directory"
    p = rows(ROOT / "results/pairs.csv")
    gates(p)
    models = [("zero", 0), ("global", 0)] + [
        (f, s["selected_alpha"][f]) for f in ["fiscal", "calendar"]
    ]
    predictions = predict(p, "test", models)
    scores = metrics(predictions)
    table(out / "test_predictions.csv", predictions)
    table(out / "test_metrics.csv", scores)
    by = {(r["model"], r["pair_id"]): r for r in predictions}
    diff = []
    fm = name("fiscal", s["selected_alpha"]["fiscal"])
    cm = name("calendar", s["selected_alpha"]["calendar"])
    for r in predictions:
        if r["model"] == fm:
            diff.append(
                dict(
                    pair_id=r["pair_id"],
                    company=r["company"],
                    year=r["end"][:4],
                    fiscal_ape=r["ape"],
                    calendar_ape=by[cm, r["pair_id"]]["ape"],
                    difference=str(
                        Fraction(r["ape"]) - Fraction(by[cm, r["pair_id"]]["ape"])
                    ),
                )
            )
    table(out / "paired_losses.csv", diff)

    def macro(rs):
        companies = sorted({r["company"] for r in rs})
        return str(
            sum(
                (
                    sum(
                        (Fraction(x["difference"]) for x in rs if x["company"] == c),
                        Fraction(),
                    )
                    / sum(x["company"] == c for x in rs)
                    for c in companies
                ),
                Fraction(),
            )
            / len(companies)
        )

    sensitivity = []
    for field in ["company", "year"]:
        for value in sorted({r[field] for r in diff}):
            for mode in ["only", "omit"]:
                rs = [r for r in diff if (r[field] == value) == (mode == "only")]
                sensitivity.append(
                    dict(
                        field=field,
                        value=value,
                        mode=mode,
                        n=len(rs),
                        macro_ape_difference=macro(rs),
                    )
                )
    table(out / "sensitivity.csv", sensitivity)
    save(
        out / "summary.json",
        dict(
            gates=s["gates"],
            selected_alpha=s["selected_alpha"],
            overall_validation_winner=s["overall_validation_winner"],
            test_pairs=len(diff),
            test_predictions=len(predictions),
            test_macro={r["model"]: r for r in scores if r["company"] == "MACRO"},
            macro_definition="Equal-company means; macro RMSE is square root of macro MSE.",
            limitations="Conditional current-source filing-day reconstruction; three convenience companies, 13 test pairs, no immutable point-in-time, causal or investment claim. Two calendar years do not support calibrated interval/significance claims.",
        ),
    )
    print(
        "PROTECTED_TEST_COMPLETE", len(diff), "pairs", len(predictions), "predictions"
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("phase", choices=["validation", "test"])
    p.add_argument("--out", type=Path, default=ROOT / "results")
    p.add_argument("--replay", action="store_true")
    a = p.parse_args()
    validation(a.out) if a.phase == "validation" else test(a.out, a.replay)
