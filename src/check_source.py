"""Verify saved projection identities and all committed source controls."""

from common import ROOT, load, digest, rows


def main():
    for n, h in load("data/source_hashes.json").items():
        assert digest(ROOT / "data" / n) == h, n
    facts = rows(ROOT / "data/facts.csv")
    filings = rows(ROOT / "data/filings.csv")
    for control in load("data/source_controls.json"):
        rs = facts if control["kind"] == "facts" else filings
        selected = [r for r in rs if r["file"] == control["file"]]
        assert [int(r["index"]) for r in selected] == list(range(control["count"]))
    assert set(r["cik"] for r in facts) == {"0000320193", "0000789019", "0000104169"}
    print("PASS_SAVED_SOURCE", len(facts), len(filings))


if __name__ == "__main__":
    main()
