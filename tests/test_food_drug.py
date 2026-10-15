import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from food_drug import FoodDrugSafety


class TestFoodDrugSafety(unittest.TestCase):
    def setUp(self):
        self.fds = FoodDrugSafety(tempfile.mkdtemp())

    def test_register_and_list(self):
        self.fds.register_product("P-1", "PainAway", "drug", "Acme")
        prods = self.fds.list_products()
        self.assertEqual(len(prods), 1)
        self.assertEqual(prods[0]["name"], "PainAway")

    def test_duplicate_product_rejected(self):
        self.fds.register_product("P-1", "PainAway", "drug", "Acme")
        with self.assertRaises(ValueError):
            self.fds.register_product("P-1", "PainAway", "drug", "Acme")

    def test_event_requires_known_product(self):
        with self.assertRaises(ValueError):
            self.fds.report_adverse_event("NOPE", "mild", "x", "y")

    def test_event_severity_validated(self):
        self.fds.register_product("P-1", "PainAway", "drug", "Acme")
        with self.assertRaises(ValueError):
            self.fds.report_adverse_event("P-1", "extreme", "x", "y")
        e = self.fds.report_adverse_event("P-1", "serious", "rash", "Clinic")
        self.assertEqual(e["severity"], "serious")

    def test_recall_lifecycle(self):
        self.fds.register_product("P-1", "PainAway", "drug", "Acme")
        r = self.fds.issue_recall("P-1", "contamination", "lot 42")
        self.assertEqual(len(self.fds.active_recalls()), 1)
        self.fds.resolve_recall(r["recall_id"])
        self.assertEqual(len(self.fds.active_recalls()), 0)
        with self.assertRaises(ValueError):
            self.fds.resolve_recall(r["recall_id"])

    def test_summary_flags_unrecalled_serious_events(self):
        self.fds.register_product("P-1", "PainAway", "drug", "Acme")
        self.fds.report_adverse_event("P-1", "serious", "rash", "Clinic")
        s = self.fds.safety_summary("P-1")[0]
        self.assertTrue(s["needs_review"])
        self.assertFalse(s["active_recall"])
        self.fds.issue_recall("P-1", "rash reports", "all lots")
        s = self.fds.safety_summary("P-1")[0]
        self.assertFalse(s["needs_review"])

    def test_persistence(self):
        d = tempfile.mkdtemp()
        a = FoodDrugSafety(d)
        a.register_product("P-1", "PainAway", "drug", "Acme")
        b = FoodDrugSafety(d)
        self.assertEqual(len(b.list_products()), 1)


if __name__ == "__main__":
    unittest.main()
