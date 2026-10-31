"""Verify complete source bindings, labels, hashes and actual SVG bar geometry."""

from pathlib import Path
from fractions import Fraction
import csv, json, hashlib, re, xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def main():
    n = 0
    coordinates = 0
    seen = set()
    bindings = set()

    def ck(v, s):
        nonlocal n
        assert v, s
        n += 1

    figures = json.loads((ROOT / "figures/manifest.json").read_bytes())
    ck(len(figures) == 3, "three figures")
    expected = set()
    for phase in ["validation", "test"]:
        with (ROOT / ("results/" + phase + "_metrics.csv")).open(
            encoding="utf-8", newline=""
        ) as f:
            rr = list(csv.DictReader(f))
        for r in rr:
            if (phase == "validation" and r["company"] == "MACRO") or (
                phase == "test" and r["company"] != "MACRO"
            ):
                expected.add(
                    (
                        "results/" + phase + "_metrics.csv",
                        tuple(
                            sorted(dict(model=r["model"], company=r["company"]).items())
                        ),
                        "mape",
                    )
                )
    with (ROOT / "results/sensitivity.csv").open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            expected.add(
                (
                    "results/sensitivity.csv",
                    tuple(
                        sorted({k: r[k] for k in ["field", "value", "mode"]}.items())
                    ),
                    "macro_ape_difference",
                )
            )
    for fig in figures:
        tree = ET.fromstring((ROOT / "figures" / (fig["name"] + ".svg")).read_bytes())
        groups = {e.attrib.get("id"): e for e in tree.iter() if e.tag.endswith("g")}
        texts = [
            "".join(e.itertext()).strip() for e in tree.iter() if e.tag.endswith("text")
        ]
        for ext, h in fig["asset_sha256"].items():
            ck(
                hashlib.sha256(
                    (ROOT / "figures" / (fig["name"] + "." + ext)).read_bytes()
                ).hexdigest()
                == h,
                "asset hash",
            )
        for a in fig["artists"]:
            gid = a["gid"]
            ck(gid not in seen, "unique bar")
            seen.add(gid)
            key = (a["source_file"], tuple(sorted(a["query"].items())), a["field"])
            ck(
                key in expected and key not in bindings,
                "complete unique source binding",
            )
            bindings.add(key)
            with (ROOT / a["source_file"]).open(encoding="utf-8", newline="") as f:
                rr = [
                    r
                    for r in csv.DictReader(f)
                    if all(r[k] == v for k, v in a["query"].items())
                ]
            ck(len(rr) == 1, "unique source row")
            v = float(Fraction(rr[0][a["field"]]) * 100)
            ck(a["value"] == v and a["multiplier"] == 100, "source percent/pp value")
            ck(
                a["label"] == format(v, ".6f") and a["label"] in texts,
                "actual numeric label",
            )
            ck(a["category"] in texts, "actual category label")
            paths = [p for p in groups[gid].iter() if p.tag.endswith("path")]
            ck(len(paths) == 1, "one actual bar path")
            numbers = list(
                map(
                    float,
                    re.findall(
                        r"[-+]?(?:\d*\.)?\d+(?:[eE][-+]?\d+)?", paths[0].attrib["d"]
                    ),
                )
            )
            ck(len(numbers) == 8, "four corners")
            xs = numbers[::2]
            ys = numbers[1::2]
            axis = a["axis_points"]
            lo, hi = axis["xlim"]
            bottom, top = axis["ylim"]
            x = lambda z: axis["left"] + (z - lo) / (hi - lo) * axis["width"]
            y = lambda z: axis["top"] + (top - z) / (top - bottom) * axis["height"]
            xx = [x(0), x(v)]
            yy = [
                y(a["position"] - a["thickness"] / 2),
                y(a["position"] + a["thickness"] / 2),
            ]
            for actual, target in [
                (min(xs), min(xx)),
                (max(xs), max(xx)),
                (min(ys), min(yy)),
                (max(ys), max(yy)),
            ]:
                ck(abs(actual - target) < 0.02, "source SVG corner")
                coordinates += 1
    ck(bindings == expected and len(seen) == 32, "all 32 complete source bars")
    out = dict(
        status="PASS",
        finite_conditions=n,
        source_bound_artists=len(seen),
        svg_coordinate_conditions=coordinates,
        asset_hashes=9,
        visual_review="separate; no accessibility conformance claim",
    )
    (ROOT / "figures/verification.json").write_bytes(
        (json.dumps(out, indent=2) + "\n").encode()
    )
    print(out)


if __name__ == "__main__":
    main()
