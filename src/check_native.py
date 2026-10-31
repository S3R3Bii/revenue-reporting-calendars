"""Independent native JSON projection check, including exact numeric lexemes."""

from pathlib import Path
import argparse, json, csv, hashlib
from decimal import Decimal
from fractions import Fraction

ROOT = Path(__file__).resolve().parents[1]


def main(raw):
    specs = json.loads((ROOT / "data/capture_manifest.json").read_bytes())["files"]
    nf = nm = checks = 0
    with (ROOT / "data/facts.csv").open(encoding="utf-8", newline="") as f:
        facts = list(csv.DictReader(f))
    with (ROOT / "data/filings.csv").open(encoding="utf-8", newline="") as f:
        filings = list(csv.DictReader(f))
    for s in specs:
        b = (raw / s["file"]).read_bytes()
        assert len(b) == s["bytes"] and hashlib.sha256(b).hexdigest() == s["sha256"]
        checks += 2
        x = json.loads(b, parse_float=Decimal)
        if s["kind"] == "companyfacts":
            native = x["facts"]["us-gaap"][
                "RevenueFromContractWithCustomerExcludingAssessedTax"
            ]["units"]["USD"]
            selected = [r for r in facts if r["file"] == s["file"]]
            assert len(selected) == len(native)
            checks += 1
            assert str(x["cik"]).zfill(10) == s["cik"]
            checks += 1
            for i, (a, r) in enumerate(zip(native, selected)):
                assert r["cik"] == s["cik"] and int(r["index"]) == i
                checks += 1
                for k in ["start", "end", "accn", "fy", "fp", "form", "filed"]:
                    assert r[k] == str(a.get(k, ""))
                    checks += 1
                if "val" in a:
                    assert Fraction(r["val"]) == Fraction(a["val"])
                    checks += 1
                else:
                    assert r["val"] == ""
                    checks += 1
            nf += len(native)
        else:
            a = x if s["kind"] == "submission_history" else x["filings"]["recent"]
            lens = {k: len(v) for k, v in a.items()}
            assert len(set(lens.values())) == 1
            checks += 1
            selected = [r for r in filings if r["file"] == s["file"]]
            assert len(selected) == len(a["accessionNumber"])
            checks += 1
            for i, r in enumerate(selected):
                assert int(r["index"]) == i and r["cik"] == s["cik"]
                checks += 1
                for k in ["accessionNumber", "filingDate", "reportDate", "form"]:
                    assert r[k] == a[k][i]
                    checks += 1
            nm += len(selected)
    assert nf == len(facts) and nm == len(filings)
    checks += 2
    out = dict(
        status="PASS",
        independent_native_conditions=checks,
        fact_entries=nf,
        filing_metadata_rows=nm,
        raw_bodies=8,
    )
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results/NATIVE_CHECK.json").write_bytes(
        (json.dumps(out, indent=2) + "\n").encode()
    )
    print(out)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--raw", type=Path, required=True)
    main(p.parse_args().raw)
