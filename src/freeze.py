"""Hash actual source, method, requests and tests before validation comparisons."""

from common import ROOT, load, save, digest
import argparse, subprocess


def main(create):
    path = ROOT / "PLAN_FREEZE.json"
    if create:
        assert not path.exists()
        names = [
            str(p.relative_to(ROOT)).replace("\\", "/")
            for folder in ["src", "tests", "data"]
            for p in (ROOT / folder).glob("*")
            if p.is_file() and p.suffix in [".py", ".csv", ".json"]
        ]
        names += [
            "NUMERICAL_PROTOCOL.md",
            "PROTOCOL.md",
            "SOURCE_TRANSPORT.md",
            "DATA_RIGHTS.md",
            "ORIGINAL_PROPOSAL.md",
            ".gitattributes",
            "requirements.txt",
        ]
        save(
            path,
            dict(
                source_checkpoint=subprocess.check_output(
                    ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
                ).strip(),
                hashes={n: digest(ROOT / n) for n in sorted(names)},
                qualification="Before validation comparisons; source informed, not blinded. Selection must be committed before final test.",
            ),
        )
    x = load("PLAN_FREEZE.json")
    for n, h in x["hashes"].items():
        assert digest(ROOT / n) == h, n
    print("PASS_METHOD_FREEZE", len(x["hashes"]), digest(path))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--create", action="store_true")
    main(p.parse_args().create)
