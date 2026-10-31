"""Stable exact accounts; no network or binary-float modeling."""

from pathlib import Path
import csv, json, hashlib
from fractions import Fraction
from decimal import Decimal, localcontext, ROUND_HALF_EVEN

ROOT = Path(__file__).resolve().parents[1]
COMPANIES = {"0000320193": "Apple", "0000789019": "Microsoft", "0000104169": "Walmart"}
TRAIN = {"0000320193", "0000789019"}


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_bytes())


def save(p, x):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes((json.dumps(x, indent=2, sort_keys=True) + "\n").encode())


def rows(p):
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def table(p, values, fields=None):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields or list(values[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(values)


def shown(x, sqrt=False):
    x = Fraction(x)
    with localcontext() as c:
        c.prec = 60
        v = Decimal(x.numerator) / Decimal(x.denominator)
        if sqrt:
            v = v.sqrt()
        return str(v.quantize(Decimal(".000001"), rounding=ROUND_HALF_EVEN))
