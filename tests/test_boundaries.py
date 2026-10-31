import sys, unittest, copy
from pathlib import Path
from fractions import Fraction as F

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dataset import eligible
from model import forecast, fitting, partition, gates


class SourceBoundaries(unittest.TestCase):
    def setUp(self):
        self.r = dict(
            cik="x",
            accn="a",
            form="10-Q",
            filed="2020-05-01",
            end="2020-03-31",
            start="2020-01-01",
            fp="Q1",
            fy="2020",
            val="100",
        )
        self.m = {("x", "a"): ("10-Q", "2020-05-01", "2020-03-31")}

    def test_current_quarter(self):
        self.assertEqual(eligible(self.r, self.m), "candidate")

    def test_comparative_end(self):
        self.r["end"] = "2019-03-31"
        self.assertEqual(eligible(self.r, self.m), "comparative_or_noncurrent_end")

    def test_amendment(self):
        self.r["form"] = "10-Q/A"
        self.assertEqual(eligible(self.r, self.m), "not_original_10Q")

    def test_annual(self):
        self.r["form"] = "10-K"
        self.assertEqual(eligible(self.r, self.m), "not_original_10Q")

    def test_metadata_missing(self):
        self.assertEqual(eligible(self.r, {}), "metadata_absent_or_conflicting")

    def test_conflicting_metadata(self):
        self.assertEqual(
            eligible(self.r, {("x", "a"): None}), "metadata_absent_or_conflicting"
        )

    def test_filing_mismatch(self):
        self.r["filed"] = "2020-05-02"
        self.assertEqual(eligible(self.r, self.m), "filing_metadata_mismatch")

    def test_zero(self):
        self.r["val"] = "0"
        self.assertEqual(eligible(self.r, self.m), "nonpositive_value")

    def test_negative(self):
        self.r["val"] = "-3"
        self.assertEqual(eligible(self.r, self.m), "nonpositive_value")

    def test_missing_value(self):
        self.r["val"] = ""
        self.assertEqual(eligible(self.r, self.m), "invalid_required_field")

    def test_nan(self):
        self.r["val"] = "NaN"
        self.assertEqual(eligible(self.r, self.m), "invalid_required_field")

    def test_no_q4(self):
        self.r["fp"] = "Q4"
        self.assertEqual(eligible(self.r, self.m), "not_quarter_focus")

    def test_missing_focus(self):
        self.r["fy"] = ""
        self.assertEqual(eligible(self.r, self.m), "invalid_required_field")

    def test_lower_inclusive(self):
        self.r["start"] = "2020-01-31"
        self.assertEqual(eligible(self.r, self.m), "candidate")

    def test_below_lower(self):
        self.r["start"] = "2020-02-01"
        self.assertEqual(eligible(self.r, self.m), "not_quarter_duration")

    def test_upper_inclusive(self):
        self.r["start"] = "2019-12-02"
        self.assertEqual(eligible(self.r, self.m), "candidate")

    def test_above_upper(self):
        self.r["start"] = "2019-12-01"
        self.assertEqual(eligible(self.r, self.m), "not_quarter_duration")

    def test_year_to_date(self):
        self.r["start"] = "2019-10-01"
        self.assertEqual(eligible(self.r, self.m), "not_quarter_duration")


class ForecastBoundaries(unittest.TestCase):
    def setUp(self):
        self.fit = [
            dict(growth="0", fp="Q1", calendar_quarter="1"),
            dict(growth="1", fp="Q2", calendar_quarter="1"),
            dict(growth="2", fp="Q2", calendar_quarter="2"),
        ]

    def test_seasonal(self):
        self.assertEqual(forecast("100", "Q1", 1, self.fit, "zero", 0), 100)

    def test_global(self):
        self.assertEqual(forecast("100", "Q1", 1, self.fit, "global", 0), 200)

    def test_fiscal_unpooled(self):
        self.assertEqual(forecast("100", "Q1", 1, self.fit, "fiscal", 0), 100)

    def test_calendar_unpooled(self):
        self.assertEqual(forecast("100", "Q1", 1, self.fit, "calendar", 0), 150)

    def test_shrinkage(self):
        self.assertEqual(forecast("100", "Q1", 1, self.fit, "fiscal", 1), 150)

    def test_unseen_unpooled(self):
        self.assertEqual(forecast("100", "Q3", 4, self.fit, "fiscal", 0), 200)

    def test_insufficient(self):
        self.assertRaises(
            ValueError, forecast, "100", "Q1", 1, self.fit[:2], "global", 0
        )

    def test_exact_fraction(self):
        self.fit[0]["growth"] = "1/3"
        self.assertEqual(forecast("3", "Q1", 1, self.fit, "fiscal", 0), 4)

    def test_strict_availability(self):
        rs = [
            dict(cik="0000320193", end="2020-01-01", available="2021-01-01"),
            dict(cik="0000320193", end="2020-01-01", available="2020-12-31"),
        ]
        self.assertEqual(fitting(rs, "2021-01-01", "validation"), [rs[1]])

    def test_company_embargo(self):
        rs = [
            dict(cik="0000104169", end="2020-01-01", available="2020-02-01"),
            dict(cik="0000320193", end="2024-01-01", available="2024-02-01"),
        ]
        self.assertEqual(fitting(rs, "2025-01-01", "test"), [])

    def test_validation_company_holdout(self):
        self.assertEqual(
            partition([dict(cik="0000104169", end="2023-01-01")], "validation"), []
        )

    def test_2024_no_test(self):
        self.assertEqual(
            partition([dict(cik="0000320193", end="2024-12-31")], "test"), []
        )

    def test_minimum_fails(self):
        self.assertRaises(AssertionError, gates, [])

    def test_invalid_model(self):
        self.assertRaises(
            AssertionError, forecast, "100", "Q1", 1, self.fit, "advice", 0
        )


if __name__ == "__main__":
    unittest.main()
