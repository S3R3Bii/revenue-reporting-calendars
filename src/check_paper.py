"""Independently bind every used value, all metric rows and reviewed PDF bytes."""

from pathlib import Path
from fractions import Fraction
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
from pypdf import PdfReader
import json, csv, re, hashlib, unicodedata

ROOT = Path(__file__).resolve().parents[1]


def load(n):
    if n.endswith(".csv"):
        with (ROOT / n).open(encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))
    return json.loads((ROOT / n).read_bytes())


def value(b):
    x = load(b["file"])
    if b["query"] is not None:
        rs = [r for r in x if all(r[k] == v for k, v in b["query"].items())]
        assert len(rs) == 1
        x = rs[0]
    for k in b["field"]:
        x = x[k]
    if b["operation"] in ["billion", "pp"]:
        x = Fraction(x) * (
            Fraction(1, 1000000000) if b["operation"] == "billion" else 100
        )
        with localcontext() as c:
            c.prec = 80
            return str(
                (Decimal(x.numerator) / Decimal(x.denominator)).quantize(
                    Decimal(".000001"), rounding=ROUND_HALF_EVEN
                )
            )
    return format(int(x), ",") if b["operation"] == "commas" else str(x)


def main():
    n = 0

    def ck(v, label):
        nonlocal n
        assert v, label
        n += 1

    pdf = PdfReader(ROOT / "paper/manuscript.pdf")
    ck(len(pdf.pages) == 6, "six current pages")
    pages = [
        re.sub(r"\s+", " ", unicodedata.normalize("NFKC", p.extract_text() or ""))
        for p in pdf.pages
    ]
    text = " ".join(pages)
    tex = (ROOT / "paper/main.tex").read_text(encoding="utf-8")
    bindings = load("paper/bindings.json")
    ck(
        len(bindings) == 90 and len({b["name"] for b in bindings}) == 90,
        "all unique used bindings",
    )
    for b in bindings:
        v = value(b)
        ck(v == b["display"], "independent source display")
        ck(
            chr(92) + "newcommand{" + chr(92) + b["name"] + "}{" + v + "}" in tex,
            "actual definition",
        )
        ck(len(re.findall(chr(92) * 2 + b["name"] + r"\b", tex)) >= 2, "actually used")
        ck(v in text, "rendered PDF value")
    rows = load("paper/table_rows.json")
    ck(len(rows) == 16, "complete test metric rows")
    for r in rows:
        company = "Macro" if r["company"] == "MACRO" else r["company"]
        fields = ["n", "mae_usd", "rmse_usd", "mape_percent"]
        values = []
        for field in fields:
            b = dict(
                file="results/test_metrics.csv",
                field=[field],
                query=dict(model=r["model"], company=r["company"]),
                operation="billion" if field in ["mae_usd", "rmse_usd"] else "value",
            )
            values.append(value(b))
        ck(
            " ".join([company, r["label"], *values]) in pages[3],
            "complete actual PDF metric table row",
        )
    scope = load("paper/PUBLICATION_SCOPE.json")
    ck(
        scope["scope"] == "independent-program-study"
        and scope["formal_submission_target"] is False,
        "authorized independent scope",
    )
    ck(len(scope["public_files"]) == 5, "five scoped paper files")
    for name, h in scope["public_files"].items():
        ck(
            hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == h,
            "current scoped file hash",
        )
    ck("not peer reviewed" in text.lower(), "review qualification")
    ck(
        "771dfdb4c9a45fad55bc826be633f5ec13c1716d" in text,
        "selection-before-test commit",
    )
    ck("not a verified immutable production" in text, "source availability limitation")
    ck("Azure optimization" in text, "private formal work boundary")
    for name in ["validation_candidates", "company_test", "dependence_checks"]:
        ck(
            (ROOT / "paper/images" / (name + ".pdf")).read_bytes()
            == (ROOT / "figures" / (name + ".pdf")).read_bytes(),
            "actual figure copied into paper",
        )
    out = dict(
        status="PASS",
        finite_conditions=n,
        used_bindings=len(bindings),
        complete_metric_rows=16,
        pages=6,
        scope_files=5,
        rendered_visual_review="separate",
    )
    (ROOT / "paper/verification.json").write_bytes(
        (json.dumps(out, indent=2) + "\n").encode()
    )
    print(out)


if __name__ == "__main__":
    main()
