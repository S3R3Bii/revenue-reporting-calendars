"""Render all validation candidates, company tests and dependence checks."""

from pathlib import Path
from fractions import Fraction
import csv, json, hashlib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def read(n):
    with (ROOT / n).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "svg.fonttype": "none",
            "svg.hashsalt": "revenue-reporting-calendars",
        }
    )
    folder = ROOT / "figures"
    folder.mkdir(exist_ok=True)
    manifest = []
    items = []

    def bar(ax, file, query, field, i, color, label):
        rs = [r for r in read(file) if all(r[k] == v for k, v in query.items())]
        assert len(rs) == 1
        value = float(Fraction(rs[0][field]) * 100)
        gid = "source-" + str(len(manifest)) + "-" + str(len(items))
        patch = ax.barh(i, value, height=0.58, color=color)[0]
        patch.set_gid(gid)
        shown = format(value, ".6f")
        ax.annotate(
            shown,
            (value, i),
            xytext=(4 if value >= 0 else -4, 0),
            textcoords="offset points",
            ha="left" if value >= 0 else "right",
            va="center",
            fontsize=9,
        )
        items.append(
            (
                dict(
                    gid=gid,
                    source_file=file,
                    query=query,
                    field=field,
                    multiplier=100,
                    value=value,
                    position=i,
                    thickness=0.58,
                    label=shown,
                    category=label,
                ),
                ax,
            )
        )

    def finish(fig, name):
        fig.canvas.draw()
        w, h = fig.get_size_inches() * 72
        for item, ax in items:
            box = ax.get_position()
            item["axis_points"] = dict(
                left=float(box.x0 * w),
                top=float((1 - box.y1) * h),
                width=float(box.width * w),
                height=float(box.height * h),
                xlim=list(map(float, ax.get_xlim())),
                ylim=list(map(float, ax.get_ylim())),
            )
        for ext in ["png", "svg", "pdf"]:
            meta = (
                {"Date": None}
                if ext == "svg"
                else {"CreationDate": None, "ModDate": None} if ext == "pdf" else None
            )
            fig.savefig(
                folder / (name + "." + ext), dpi=160, facecolor="white", metadata=meta
            )
        p = folder / (name + ".svg")
        p.write_bytes(
            (
                "\n".join(
                    x.rstrip() for x in p.read_text(encoding="utf-8").splitlines()
                )
                + "\n"
            ).encode()
        )
        manifest.append(
            dict(
                name=name,
                artists=[a for a, ax in items],
                asset_sha256={
                    e: hashlib.sha256(
                        (folder / (name + "." + e)).read_bytes()
                    ).hexdigest()
                    for e in ["png", "svg", "pdf"]
                },
            )
        )
        plt.close(fig)

    names = ["zero", "global"] + [
        f + "_" + str(a) for f in ["fiscal", "calendar"] for a in [0, 1, 4, 16]
    ]
    labels = ["Same quarter, zero growth", "Global mean growth"] + [
        f.title() + " / strength " + str(a)
        for f in ["fiscal", "calendar"]
        for a in [0, 1, 4, 16]
    ]
    fig, ax = plt.subplots(figsize=(10, 5.8))
    fig.subplots_adjust(left=0.28, right=0.84, top=0.78, bottom=0.15)
    fig.suptitle(
        "Validation preferred the zero-growth baseline",
        x=0.04,
        ha="left",
        y=0.97,
        fontsize=16,
    )
    fig.text(
        0.04,
        0.88,
        "12 targets from Apple and Microsoft; equal-company macro MAPE; all ten candidates retained",
        fontsize=10,
    )
    items = []
    for i, (m, label) in enumerate(zip(names, labels)):
        bar(
            ax,
            "results/validation_metrics.csv",
            dict(model=m, company="MACRO"),
            "mape",
            i,
            "#177f83" if m == "zero" else "#657182",
            label,
        )
    ax.set_yticks(range(10), labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 15)
    ax.set_xlabel("Mean absolute percentage error (%) — lower is better")
    ax.grid(axis="x", alpha=0.18)
    ax.set_axisbelow(True)
    fig.text(
        0.04,
        0.03,
        "Group strength was selected separately for each family before the protected test; both selected strength 0.",
        fontsize=10,
    )
    finish(fig, "validation_candidates")
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.5))
    fig.subplots_adjust(left=0.17, right=0.9, top=0.72, bottom=0.21, wspace=0.45)
    fig.suptitle(
        "A small overall difference hides company variation",
        x=0.04,
        ha="left",
        y=0.97,
        fontsize=16,
    )
    fig.text(
        0.04,
        0.86,
        "Protected 2025–June 2026 targets: Apple 5, Microsoft 4, Walmart 4; Walmart labels never fit or select.",
        fontsize=10,
    )
    items = []
    models = ["zero", "global", "fiscal_0", "calendar_0"]
    labels = ["Zero growth", "Global growth", "Fiscal / 0", "Calendar / 0"]
    colors = ["#657182", "#d18a22", "#177f83", "#5d59b1"]
    for ax, c in zip(axes, ["Apple", "Microsoft", "Walmart"]):
        for i, (m, label, color) in enumerate(zip(models, labels, colors)):
            bar(
                ax,
                "results/test_metrics.csv",
                dict(model=m, company=c),
                "mape",
                i,
                color,
                label,
            )
        ax.set_title(c)
        ax.set_yticks(range(4), labels if c == "Apple" else [""] * 4)
        ax.invert_yaxis()
        ax.set_xlim(0, 19)
        ax.set_xlabel("MAPE (%)")
        ax.grid(axis="x", alpha=0.18)
        ax.set_axisbelow(True)
    fig.text(
        0.04,
        0.05,
        "Fixed candidates, conditional current-source filing-day reconstruction; descriptive finite results, not investment evidence.",
        fontsize=10,
    )
    finish(fig, "company_test")
    fig, ax = plt.subplots(figsize=(10, 5.8))
    fig.subplots_adjust(left=0.28, right=0.83, top=0.78, bottom=0.16)
    fig.suptitle(
        "The fiscal-versus-calendar ordering changes with the block",
        x=0.04,
        ha="left",
        y=0.97,
        fontsize=15,
    )
    fig.text(
        0.04,
        0.88,
        "Fiscal minus calendar macro MAPE; negative favors fiscal. All company/year inclusion and omission checks.",
        fontsize=10,
    )
    items = []
    rs = read("results/sensitivity.csv")
    labels = []
    for i, r in enumerate(rs):
        label = ("Only " if r["mode"] == "only" else "Omit ") + r["value"]
        labels.append(label)
        bar(
            ax,
            "results/sensitivity.csv",
            {k: r[k] for k in ["field", "value", "mode"]},
            "macro_ape_difference",
            i,
            "#177f83" if Fraction(r["macro_ape_difference"]) < 0 else "#bc5262",
            label,
        )
    ax.set_yticks(range(10), labels)
    ax.invert_yaxis()
    ax.set_xlim(-0.16, 0.24)
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set_xlabel("Difference in MAPE (percentage points)")
    ax.grid(axis="x", alpha=0.18)
    ax.set_axisbelow(True)
    fig.text(
        0.04,
        0.04,
        "Dependence checks are descriptive; three firms and two years do not support calibrated intervals or significance.",
        fontsize=10,
    )
    finish(fig, "dependence_checks")
    (folder / "manifest.json").write_bytes(
        (json.dumps(manifest, indent=2) + "\n").encode()
    )
    print("THREE_FIGURES", sum(len(x["artists"]) for x in manifest))


if __name__ == "__main__":
    main()
