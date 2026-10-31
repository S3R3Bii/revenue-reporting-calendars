"""Accession-bound current-quarter and annual-pair construction."""

from datetime import date, timedelta
from fractions import Fraction
from collections import defaultdict, Counter
from common import ROOT, rows, table, save, COMPANIES


def day(s):
    return date.fromisoformat(s)


def eligible(r, metadata):
    try:
        if r["form"] != "10-Q":
            return "not_original_10Q"
        m = metadata.get((r["cik"], r["accn"]))
        if m is None:
            return "metadata_absent_or_conflicting"
        if (r["form"], r["filed"]) != (m[0], m[1]):
            return "filing_metadata_mismatch"
        if r["end"] != m[2]:
            return "comparative_or_noncurrent_end"
        start, end = day(r["start"]), day(r["end"])
        if not 61 <= (end - start).days + 1 <= 121:
            return "not_quarter_duration"
        if r["fp"] not in ["Q1", "Q2", "Q3"]:
            return "not_quarter_focus"
        int(r["fy"])
        day(r["filed"])
        if Fraction(r["val"]) <= 0:
            return "nonpositive_value"
        if not day("2018-01-01") <= end <= day("2026-06-30"):
            return "outside_observation_window"
        return "candidate"
    except (ValueError, TypeError, ZeroDivisionError, OverflowError):
        return "invalid_required_field"


def construct():
    fs = rows(ROOT / "data/facts.csv")
    ms = rows(ROOT / "data/filings.csv")
    sets = defaultdict(set)
    for r in ms:
        sets[r["cik"], r["accessionNumber"]].add(
            (r["form"], r["filingDate"], r["reportDate"])
        )
    metadata = {k: next(iter(v)) if len(v) == 1 else None for k, v in sets.items()}
    accounts = []
    contexts = defaultdict(list)
    for r in fs:
        status = eligible(r, metadata)
        a = dict(r, status=status)
        accounts.append(a)
        if status == "candidate":
            contexts[tuple(r[k] for k in ["cik", "accn", "start", "end"])].append(a)
    slots = defaultdict(list)
    for key, rs in contexts.items():
        values = {
            (Fraction(r["val"]), r["fy"], r["fp"], r["form"], r["filed"]) for r in rs
        }
        if len(values) != 1:
            for r in rs:
                r["status"] = "conflicting_context"
            continue
        first = rs[0]
        first["status"] = "context_representative"
        for r in rs[1:]:
            r["status"] = "exact_context_repeat"
        slots[first["cik"], int(first["fy"]), first["fp"]].append((first, len(rs)))
    obs = []
    for key, rs in sorted(slots.items()):
        if len({r["end"] for r, n in rs}) != 1:
            for r, n in rs:
                r["status"] = "conflicting_slot_ends"
            continue
        ordered = sorted(rs, key=lambda z: (z[0]["filed"], z[0]["accn"]))
        for r, n in ordered[1:]:
            r["status"] = "later_original_accession"
        r, n = ordered[0]
        r["status"] = "selected_observation"
        obs.append(
            dict(
                id=":".join(map(str, key)),
                cik=key[0],
                company=COMPANIES[key[0]],
                fy=key[1],
                fp=key[2],
                start=r["start"],
                end=r["end"],
                filed=r["filed"],
                accn=r["accn"],
                value=str(Fraction(r["val"])),
                multiplicity=n,
                source_file=r["file"],
                source_index=r["index"],
            )
        )
    index = {(r["cik"], r["fy"], r["fp"]): r for r in obs}
    pairs = []
    pa = []
    for target in obs:
        prior = index.get((target["cik"], target["fy"] - 1, target["fp"]))
        status = "paired"
        if prior is None:
            status = "prior_slot_unavailable"
        elif not 335 <= (day(target["end"]) - day(prior["end"])).days <= 395:
            status = "annual_gap_outside_gate"
        pa.append(
            dict(
                target_id=target["id"],
                prior_id=prior["id"] if prior else "",
                status=status,
            )
        )
        if status != "paired":
            continue
        origin = (day(prior["filed"]) + timedelta(days=1)).isoformat()
        available = (day(target["filed"]) + timedelta(days=1)).isoformat()
        assert origin < available, "target available before origin"
        pairs.append(
            dict(
                id=target["id"],
                cik=target["cik"],
                company=target["company"],
                fy=target["fy"],
                fp=target["fp"],
                calendar_quarter=(day(prior["end"]).month - 1) // 3 + 1,
                end=target["end"],
                prior_end=prior["end"],
                origin=origin,
                available=available,
                prior=str(Fraction(prior["value"])),
                actual=str(Fraction(target["value"])),
                growth=str(Fraction(target["value"]) / Fraction(prior["value"]) - 1),
                prior_accn=prior["accn"],
                target_accn=target["accn"],
            )
        )
    return accounts, obs, pa, pairs


def main(out):
    a, o, pa, p = construct()
    table(out / "source_accounts.csv", a)
    table(out / "observations.csv", o)
    table(out / "pair_accounts.csv", pa)
    table(out / "pairs.csv", p)
    save(
        out / "source_summary.json",
        dict(
            facts=len(a),
            filing_rows=len(rows(ROOT / "data/filings.csv")),
            observations=len(o),
            pairs=len(p),
            statuses=dict(Counter(r["status"] for r in a)),
            pair_statuses=dict(Counter(r["status"] for r in pa)),
            company_observations=dict(Counter(r["company"] for r in o)),
        ),
    )
    print("SOURCE_ACCOUNTS", len(a), "OBSERVATIONS", len(o), "PAIRS", len(p))


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=ROOT / "results")
    main(ap.parse_args().out)
