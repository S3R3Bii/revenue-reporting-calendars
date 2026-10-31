"""Simple available-label growth pooling with explicit company/time boundaries."""

from fractions import Fraction
from collections import Counter, defaultdict
from common import TRAIN, shown

GRID = [("zero", 0), ("global", 0)] + [
    (f, a) for f in ["fiscal", "calendar"] for a in [0, 1, 4, 16]
]


def name(f, a):
    return f if f in ["zero", "global"] else f + "_" + str(a)


def partition(pairs, phase):
    lower, upper = (
        ("2022-01-01", "2023-12-31")
        if phase == "validation"
        else ("2025-01-01", "2026-06-30")
    )
    return [
        r
        for r in pairs
        if lower <= r["end"] <= upper and (phase != "validation" or r["cik"] in TRAIN)
    ]


def fitting(pairs, origin, phase):
    upper = "2021-12-31" if phase == "validation" else "2023-12-31"
    return [
        r
        for r in pairs
        if r["cik"] in TRAIN
        and "2019-01-01" <= r["end"] <= upper
        and r["available"] < origin
    ]


def forecast(prior, fp, calendar, fit, family, alpha):
    assert family in ["zero", "global", "fiscal", "calendar"] and alpha in [0, 1, 4, 16]
    if len(fit) < 3:
        raise ValueError("insufficient available fitting labels")
    global_mean = sum((Fraction(r["growth"]) for r in fit), Fraction()) / len(fit)
    if family == "zero":
        g = Fraction()
    elif family == "global":
        g = global_mean
    else:
        group = [
            Fraction(r["growth"])
            for r in fit
            if (
                r["fp"] == fp
                if family == "fiscal"
                else int(r["calendar_quarter"]) == int(calendar)
            )
        ]
        g = (
            (sum(group, Fraction()) + alpha * global_mean) / (len(group) + alpha)
            if group
            else global_mean
        )
    result = Fraction(prior) * (1 + g)
    assert result > 0
    return result


def gates(pairs):
    counts = {}
    for phase in ["train", "validation", "test"]:
        rs = (
            [
                r
                for r in pairs
                if r["cik"] in TRAIN and "2019-01-01" <= r["end"] <= "2021-12-31"
            ]
            if phase == "train"
            else partition(pairs, phase)
        )
        c = Counter(r["cik"] for r in rs)
        required = TRAIN if phase != "test" else set(r["cik"] for r in pairs)
        assert len(required) == (2 if phase != "test" else 3)
        assert all(c[k] >= 3 for k in required), (phase, c)
        counts[phase] = dict(sorted(c.items()))
    closure = max(r["available"] for r in partition(pairs, "validation"))
    assert all(
        r["origin"] > closure for r in partition(pairs, "test")
    ), "test origin precedes selection closure"
    for phase in ["validation", "test"]:
        assert all(
            len(fitting(pairs, r["origin"], phase)) >= 3
            for r in partition(pairs, phase)
        )
    return dict(counts=counts, validation_closure=closure)


def predict(pairs, phase, models):
    output = []
    for target in partition(pairs, phase):
        fit = fitting(pairs, target["origin"], phase)
        for family, alpha in models:
            p = forecast(
                target["prior"],
                target["fp"],
                target["calendar_quarter"],
                fit,
                family,
                alpha,
            )
            error = p - Fraction(target["actual"])
            output.append(
                dict(
                    phase=phase,
                    model=name(family, alpha),
                    pair_id=target["id"],
                    cik=target["cik"],
                    company=target["company"],
                    end=target["end"],
                    origin=target["origin"],
                    available=target["available"],
                    fp=target["fp"],
                    calendar_quarter=target["calendar_quarter"],
                    prior=target["prior"],
                    actual=target["actual"],
                    forecast=str(p),
                    error=str(error),
                    ape=str(abs(error) / Fraction(target["actual"])),
                    fit_ids=";".join(r["id"] for r in fit),
                    fit_count=len(fit),
                )
            )
    return output


def metrics(predictions):
    groups = defaultdict(list)
    for r in predictions:
        groups[r["model"], r["company"]].append(r)
    out = []
    for (m, c), rs in sorted(groups.items()):
        n = len(rs)
        e = [Fraction(r["error"]) for r in rs]
        mae = sum(map(abs, e), Fraction()) / n
        mse = sum((v * v for v in e), Fraction()) / n
        mape = sum((Fraction(r["ape"]) for r in rs), Fraction()) / n
        out.append(
            dict(
                model=m,
                company=c,
                n=n,
                mae=str(mae),
                mse=str(mse),
                mape=str(mape),
                mae_usd=shown(mae),
                mse_usd_squared=shown(mse),
                rmse_usd=shown(mse, True),
                mape_percent=shown(100 * mape),
            )
        )
    for m in sorted({r["model"] for r in out}):
        rs = [r for r in out if r["model"] == m]
        n = len(rs)
        mae = sum((Fraction(r["mae"]) for r in rs), Fraction()) / n
        mse = sum((Fraction(r["mse"]) for r in rs), Fraction()) / n
        mape = sum((Fraction(r["mape"]) for r in rs), Fraction()) / n
        out.append(
            dict(
                model=m,
                company="MACRO",
                n=sum(r["n"] for r in rs),
                mae=str(mae),
                mse=str(mse),
                mape=str(mape),
                mae_usd=shown(mae),
                mse_usd_squared=shown(mse),
                rmse_usd=shown(mse, True),
                mape_percent=shown(100 * mape),
            )
        )
    return out
