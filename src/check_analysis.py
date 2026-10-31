"""Independent SQLite source selection and rational forecasting reconstruction.

Does not import dataset, model, evaluate or exercise implementation functions.
"""

from pathlib import Path
from fractions import Fraction as F
from datetime import date, timedelta
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
import csv, json, sqlite3, hashlib, argparse

ROOT = Path(__file__).resolve().parents[1]


def read(n):
    with (ROOT / n).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main(phase):
    count = 0

    def ck(v, label):
        nonlocal count
        assert v, label
        count += 1

    facts = read("data/facts.csv")
    metadata = read("data/filings.csv")
    db = sqlite3.connect(":memory:")
    db.execute(
        "create table facts (" + ",".join('"' + k + '" text' for k in facts[0]) + ")"
    )
    db.executemany(
        "insert into facts values (" + ",".join("?" for k in facts[0]) + ")",
        [tuple(r.values()) for r in facts],
    )
    db.execute("create table meta(cik text,accn text,form text,filed text,report text)")
    db.executemany(
        "insert into meta values(?,?,?,?,?)",
        [
            (
                r["cik"],
                r["accessionNumber"],
                r["form"],
                r["filingDate"],
                r["reportDate"],
            )
            for r in metadata
        ],
    )
    unique = db.execute(
        "select cik,accn,min(form),min(filed),min(report) from (select distinct * from meta) group by cik,accn having count(*)=1"
    ).fetchall()
    m = {(a, b): (c, d, e) for a, b, c, d, e in unique}
    expected = []
    states = {}
    for r in facts:
        status = "candidate"
        try:
            if r["form"] != "10-Q":
                status = "not_original_10Q"
            elif (r["cik"], r["accn"]) not in m:
                status = "metadata_absent_or_conflicting"
            elif (r["form"], r["filed"]) != m[r["cik"], r["accn"]][:2]:
                status = "filing_metadata_mismatch"
            elif r["end"] != m[r["cik"], r["accn"]][2]:
                status = "comparative_or_noncurrent_end"
            elif (
                not 61
                <= (
                    (date.fromisoformat(r["end"]) - date.fromisoformat(r["start"])).days
                    + 1
                )
                <= 121
            ):
                status = "not_quarter_duration"
            elif r["fp"] not in ["Q1", "Q2", "Q3"]:
                status = "not_quarter_focus"
            else:
                int(r["fy"])
                date.fromisoformat(r["filed"])
                if F(r["val"]) <= 0:
                    status = "nonpositive_value"
                elif not "2018-01-01" <= r["end"] <= "2026-06-30":
                    status = "outside_observation_window"
        except (ValueError, TypeError, ZeroDivisionError, OverflowError):
            status = "invalid_required_field"
        states[r["file"], r["index"]] = status
        if status == "candidate":
            expected.append(r)
    contexts = {}
    for r in expected:
        contexts.setdefault((r["cik"], r["accn"], r["start"], r["end"]), []).append(r)
    slots = {}
    for group in contexts.values():
        if (
            len({(F(r["val"]), r["fy"], r["fp"], r["form"], r["filed"]) for r in group})
            > 1
        ):
            for r in group:
                states[r["file"], r["index"]] = "conflicting_context"
        else:
            r = group[0]
            states[r["file"], r["index"]] = "context_representative"
            for q in group[1:]:
                states[q["file"], q["index"]] = "exact_context_repeat"
            slots.setdefault((r["cik"], int(r["fy"]), r["fp"]), []).append(
                (r, len(group))
            )
    obs = {}
    for key, group in slots.items():
        if len({r["end"] for r, n in group}) > 1:
            for r, n in group:
                states[r["file"], r["index"]] = "conflicting_slot_ends"
        else:
            group.sort(key=lambda x: (x[0]["filed"], x[0]["accn"]))
            r, n = group[0]
            obs[":".join(map(str, key))] = (r, n)
            states[r["file"], r["index"]] = "selected_observation"
            for q, z in group[1:]:
                states[q["file"], q["index"]] = "later_original_accession"
    actual = read("results/source_accounts.csv")
    ck(len(actual) == len(facts), "full source accounts")
    for a, r in zip(actual, facts):
        ck(all(a[k] == v for k, v in r.items()), "source fields")
        ck(a["status"] == states[r["file"], r["index"]], "source exclusion/selection")
    oo = read("results/observations.csv")
    ck(len(oo) == len(obs), "all selected observations")
    for o in oo:
        r, n = obs[o["id"]]
        for k in ["cik", "fy", "fp", "start", "end", "filed", "accn"]:
            ck(o[k] == r[k], "observation " + k)
        ck(
            F(o["value"]) == F(r["val"]) and int(o["multiplicity"]) == n,
            "amount/multiplicity",
        )
    expected_pairs = {}
    pa = {}
    for ident, (r, n) in obs.items():
        pid = ":".join([r["cik"], str(int(r["fy"]) - 1), r["fp"]])
        prior = obs.get(pid)
        if prior is None:
            pa[ident] = (pid, "prior_slot_unavailable")
            continue
        p = prior[0]
        if (
            not 335
            <= (date.fromisoformat(r["end"]) - date.fromisoformat(p["end"])).days
            <= 395
        ):
            pa[ident] = (pid, "annual_gap_outside_gate")
            continue
        pa[ident] = (pid, "paired")
        expected_pairs[ident] = dict(
            cik=r["cik"],
            company={
                "0000320193": "Apple",
                "0000789019": "Microsoft",
                "0000104169": "Walmart",
            }[r["cik"]],
            fy=r["fy"],
            fp=r["fp"],
            calendar_quarter=str((date.fromisoformat(p["end"]).month - 1) // 3 + 1),
            end=r["end"],
            prior_end=p["end"],
            origin=str(date.fromisoformat(p["filed"]) + timedelta(days=1)),
            available=str(date.fromisoformat(r["filed"]) + timedelta(days=1)),
            prior=str(F(p["val"])),
            actual=str(F(r["val"])),
            growth=str(F(r["val"]) / F(p["val"]) - 1),
            prior_accn=p["accn"],
            target_accn=r["accn"],
        )
    for a in read("results/pair_accounts.csv"):
        pid, s = pa[a["target_id"]]
        ck(a["status"] == s, "pair exclusion")
        ck(a["prior_id"] == (pid if pid in obs else ""), "prior ID")
    pairs = read("results/pairs.csv")
    ck(len(pairs) == len(expected_pairs), "all pairs")
    for r in pairs:
        ck(
            {k: v for k, v in r.items() if k != "id"} == expected_pairs[r["id"]],
            "complete pair facts",
        )
    train = {"0000320193", "0000789019"}
    models = [("zero", 0), ("global", 0)] + [
        (f, a) for f in ["fiscal", "calendar"] for a in [0, 1, 4, 16]
    ]
    selected = json.loads((ROOT / "results/selection.json").read_bytes())
    phases = ["validation"] if phase == "validation" else ["validation", "test"]
    for ph in phases:
        lower, upper = (
            ("2022-01-01", "2023-12-31")
            if ph == "validation"
            else ("2025-01-01", "2026-06-30")
        )
        targets = {
            r["id"]: r
            for r in pairs
            if lower <= r["end"] <= upper and (ph == "test" or r["cik"] in train)
        }
        allowed = (
            models
            if ph == "validation"
            else [("zero", 0), ("global", 0)]
            + [(f, selected["selected_alpha"][f]) for f in ["fiscal", "calendar"]]
        )
        forecasts = read("results/" + ph + "_predictions.csv")
        ck(len(forecasts) == len(targets) * len(allowed), "complete predictions")
        lookup = {
            (
                "zero"
                if f == "zero"
                else "global" if f == "global" else f + "_" + str(a)
            ): (f, a)
            for f, a in allowed
        }
        checked = {}
        seen = set()
        for r in forecasts:
            key = (r["model"], r["pair_id"])
            ck(key not in seen, "unique prediction")
            seen.add(key)
            t = targets[r["pair_id"]]
            f, a = lookup[r["model"]]
            cutoff = "2021-12-31" if ph == "validation" else "2023-12-31"
            fit = [
                q
                for q in pairs
                if q["cik"] in train
                and "2019-01-01" <= q["end"] <= cutoff
                and q["available"] < t["origin"]
            ]
            ck(len(fit) >= 3, "fit minimum")
            ck(
                r["fit_ids"] == ";".join(q["id"] for q in fit)
                and int(r["fit_count"]) == len(fit),
                "exact available fitting membership",
            )
            ck(
                all(
                    q["cik"] in train
                    and q["end"] < "2024-01-01"
                    and q["available"] < t["origin"]
                    for q in fit
                ),
                "no heldout/embargo/test/late label",
            )
            if ph == "test":
                ck(
                    t["origin"] > selected["gates"]["validation_closure"],
                    "selection closure precedes origin",
                )
            gg = sum((F(q["growth"]) for q in fit), F()) / len(fit)
            group = [
                F(q["growth"])
                for q in fit
                if (
                    q["fp"] == t["fp"]
                    if f == "fiscal"
                    else q["calendar_quarter"] == t["calendar_quarter"]
                )
            ]
            growth = (
                F()
                if f == "zero"
                else (
                    gg
                    if f == "global" or not group
                    else (sum(group, F()) + a * gg) / (len(group) + a)
                )
            )
            predicted = F(t["prior"]) * (1 + growth)
            error = predicted - F(t["actual"])
            ape = abs(error) / F(t["actual"])
            for k in [
                "cik",
                "company",
                "end",
                "origin",
                "available",
                "fp",
                "calendar_quarter",
                "prior",
                "actual",
            ]:
                ck(r[k] == t[k], "prediction context " + k)
            ck(
                (F(r["forecast"]), F(r["error"]), F(r["ape"]))
                == (predicted, error, ape),
                "exact forecast/loss",
            )
            checked[key] = (error, ape, t["company"])
        metrics = read("results/" + ph + "_metrics.csv")
        raw = {}
        for m in lookup:
            companies = sorted({v[2] for k, v in checked.items() if k[0] == m})
            for company in companies:
                es = [v for k, v in checked.items() if k[0] == m and v[2] == company]
                n = len(es)
                raw[m, company] = (
                    sum((abs(e) for e, a, c in es), F()) / n,
                    sum((e * e for e, a, c in es), F()) / n,
                    sum((a for e, a, c in es), F()) / n,
                    n,
                )
            raw[m, "MACRO"] = tuple(
                sum((raw[m, c][j] for c in companies), F()) / len(companies)
                for j in range(3)
            ) + (sum(raw[m, c][3] for c in companies),)
        ck(len(metrics) == len(raw), "complete metric cells")
        for r in metrics:
            values = raw[r["model"], r["company"]]
            ck(
                tuple(F(r[k]) for k in ["mae", "mse", "mape"]) == values[:3]
                and int(r["n"]) == values[3],
                "exact metric sums",
            )
            with localcontext() as ctx:
                ctx.prec = 60
                for field, index, mult, sqrt in [
                    ("mae_usd", 0, 1, False),
                    ("mse_usd_squared", 1, 1, False),
                    ("rmse_usd", 1, 1, True),
                    ("mape_percent", 2, 100, False),
                ]:
                    v = values[index] * mult
                    d = Decimal(v.numerator) / Decimal(v.denominator)
                    if sqrt:
                        d = d.sqrt()
                    ck(
                        r[field]
                        == str(
                            d.quantize(Decimal(".000001"), rounding=ROUND_HALF_EVEN)
                        ),
                        "decimal metric display",
                    )
        if ph == "validation":
            loss = {m: raw[m, "MACRO"][2] for m in lookup}
            for f in ["fiscal", "calendar"]:
                ck(
                    selected["selected_alpha"][f]
                    == min([0, 1, 4, 16], key=lambda a: (loss[f + "_" + str(a)], a)),
                    "validation selected strength",
                )
            ck(
                selected["overall_validation_winner"]
                == min(lookup, key=lambda m: (loss[m], list(lookup).index(m))),
                "overall validation winner",
            )
    if phase == "test":
        diffs = read("results/paired_losses.csv")
        fm = "fiscal_" + str(selected["selected_alpha"]["fiscal"])
        cm = "calendar_" + str(selected["selected_alpha"]["calendar"])
        ck(len(diffs) == len(targets), "all paired losses")
        for r in diffs:
            a = checked[fm, r["pair_id"]][1]
            b = checked[cm, r["pair_id"]][1]
            ck(
                (F(r["fiscal_ape"]), F(r["calendar_ape"]), F(r["difference"]))
                == (a, b, a - b),
                "paired comparison",
            )
        sensitivity = read("results/sensitivity.csv")
        ck(len(sensitivity) == 10, "all subgroup/omission accounts")
        for r in sensitivity:
            subset = [
                q
                for q in diffs
                if (q[r["field"]] == r["value"]) == (r["mode"] == "only")
            ]
            companies = {q["company"] for q in subset}
            v = sum(
                (
                    sum((F(q["difference"]) for q in subset if q["company"] == c), F())
                    / sum(q["company"] == c for q in subset)
                    for c in companies
                ),
                F(),
            ) / len(companies)
            ck(
                int(r["n"]) == len(subset) and F(r["macro_ape_difference"]) == v,
                "descriptive dependence account",
            )
    out = dict(
        status="PASS",
        phase=phase,
        independent_sql_fraction_conditions=count,
        source_rows=len(facts),
        pairs=len(pairs),
        production_model_imported=False,
    )
    (ROOT / "results" / ("INDEPENDENT_" + phase.upper() + ".json")).write_bytes(
        (json.dumps(out, indent=2) + "\n").encode()
    )
    print(out)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("phase", choices=["validation", "test"])
    main(p.parse_args().phase)
