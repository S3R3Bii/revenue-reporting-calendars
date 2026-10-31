"""Project checked native JSON into minimal numeric and filing-date facts."""

import argparse, json
from pathlib import Path
from common import ROOT, load, save, table, digest

CONCEPT = "RevenueFromContractWithCustomerExcludingAssessedTax"
FACT_KEYS = ["start", "end", "val", "accn", "fy", "fp", "form", "filed"]
META_KEYS = ["accessionNumber", "filingDate", "reportDate", "form"]


def main(raw):
    facts = []
    filings = []
    controls = []
    for spec in load("data/capture_manifest.json")["files"]:
        p = raw / spec["file"]
        assert p.stat().st_size == spec["bytes"] and digest(p) == spec["sha256"]
        x = json.loads(p.read_bytes(), parse_int=str, parse_float=str)
        if spec["kind"] == "companyfacts":
            assert str(x["cik"]).zfill(10) == spec["cik"]
            a = x["facts"]["us-gaap"][CONCEPT]["units"]["USD"]
            for i, v in enumerate(a):
                facts.append(
                    dict(
                        file=spec["file"],
                        index=i,
                        cik=spec["cik"],
                        **{k: str(v.get(k, "")) for k in FACT_KEYS}
                    )
                )
            controls.append(dict(file=spec["file"], kind="facts", count=len(a)))
        else:
            a = x if spec["kind"] == "submission_history" else x["filings"]["recent"]
            if spec["kind"] != "submission_history":
                assert str(x["cik"]).zfill(10) == spec["cik"]
            lengths = {k: len(v) for k, v in a.items()}
            assert len(set(lengths.values())) == 1
            n = lengths["accessionNumber"]
            for i in range(n):
                filings.append(
                    dict(
                        file=spec["file"],
                        index=i,
                        cik=spec["cik"],
                        **{k: a[k][i] for k in META_KEYS}
                    )
                )
            controls.append(
                dict(file=spec["file"], kind="filings", count=n, array_lengths=lengths)
            )
    table(ROOT / "data/facts.csv", facts)
    table(ROOT / "data/filings.csv", filings)
    save(ROOT / "data/source_controls.json", controls)
    save(
        ROOT / "data/source_hashes.json",
        {
            n: digest(ROOT / "data" / n)
            for n in [
                "facts.csv",
                "filings.csv",
                "source_controls.json",
                "capture_manifest.json",
            ]
        },
    )
    print("PROJECTED", len(facts), len(filings))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--raw", type=Path, required=True)
    main(p.parse_args().raw)
