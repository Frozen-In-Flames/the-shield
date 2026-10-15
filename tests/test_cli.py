import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import shield_cli


def run_cli(tmp, *args):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = shield_cli.main(["--data-dir", tmp] + list(args))
    return code, buf.getvalue()


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_food_flow(self):
        code, out = run_cli(self.tmp, "food", "register", "--id", "P-1",
                            "--name", "PainAway", "--category", "drug",
                            "--maker", "Acme")
        self.assertEqual(code, 0)
        self.assertIn("registered product P-1", out)
        code, out = run_cli(self.tmp, "food", "event", "--product", "P-1",
                            "--severity", "serious", "--description", "rash",
                            "--reporter", "Clinic A")
        self.assertIn("recorded serious event", out)
        code, out = run_cli(self.tmp, "food", "summary", "--product", "P-1")
        self.assertIn("NEEDS REVIEW", out)
        code, out = run_cli(self.tmp, "food", "recall", "--product", "P-1",
                            "--reason", "rash reports", "--scope", "all")
        self.assertIn("issued recall", out)
        code, out = run_cli(self.tmp, "food", "recalls")
        self.assertIn("active", out)
        rid = "R-1"
        code, out = run_cli(self.tmp, "food", "resolve", "--recall", rid)
        self.assertIn("resolved recall", out)
        code, out = run_cli(self.tmp, "food", "recalls")
        self.assertIn("no active recalls", out)

    def test_food_error_path(self):
        code, out = run_cli(self.tmp, "food", "event", "--product", "NOPE",
                            "--severity", "mild", "--description", "x",
                            "--reporter", "y")
        self.assertEqual(code, 1)
        self.assertIn("error", out)

    def test_air_flow(self):
        code, out = run_cli(self.tmp, "air", "file", "--id", "FL-1",
                            "--origin", "AAA", "--destination", "BBB",
                            "--band", "high",
                            "--start", "2026-10-16T08:00",
                            "--end", "2026-10-16T10:00")
        self.assertEqual(code, 0)
        self.assertIn("filed flight FL-1", out)
        code, out = run_cli(self.tmp, "air", "file", "--id", "FL-2",
                            "--origin", "CCC", "--destination", "DDD",
                            "--band", "high",
                            "--start", "2026-10-16T09:00",
                            "--end", "2026-10-16T11:00")
        self.assertIn("CONFLICT", out)
        code, out = run_cli(self.tmp, "air", "conflicts")
        self.assertIn("FL-1 x FL-2", out)
        code, out = run_cli(self.tmp, "air", "flights")
        self.assertIn("FL-1", out)
        code, out = run_cli(self.tmp, "air", "cancel", "--id", "FL-2")
        self.assertIn("cancelled", out)
        code, out = run_cli(self.tmp, "air", "conflicts")
        self.assertIn("no conflicts", out)

    def test_env_flow(self):
        code, out = run_cli(self.tmp, "env", "record", "--station", "S-1",
                            "--metric", "pm25", "--value", "42",
                            "--unit", "ug/m3", "--limit", "35")
        self.assertEqual(code, 0)
        self.assertIn("BREACH", out)
        code, out = run_cli(self.tmp, "env", "record", "--station", "S-1",
                            "--metric", "pm25", "--value", "20",
                            "--unit", "ug/m3", "--limit", "35")
        self.assertNotIn("BREACH", out)
        code, out = run_cli(self.tmp, "env", "exceedances")
        self.assertIn("EXCEEDANCE", out)
        code, out = run_cli(self.tmp, "env", "stations")
        self.assertIn("S-1", out)
        self.assertIn("breaches=1", out)
        code, out = run_cli(self.tmp, "env", "readings",
                            "--station", "S-1")
        self.assertIn("pm25", out)


if __name__ == "__main__":
    unittest.main()
