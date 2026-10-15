import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from environment import EnvironmentKeeper


class TestEnvironmentKeeper(unittest.TestCase):
    def setUp(self):
        self.env = EnvironmentKeeper(tempfile.mkdtemp())

    def test_record_and_list(self):
        self.env.record_reading("S-1", "pm25", 20, "ug/m3", 35)
        rows = self.env.list_readings()
        self.assertEqual(len(rows), 1)
        self.assertFalse(rows[0]["breach"])

    def test_breach_flagged(self):
        r = self.env.record_reading("S-1", "pm25", 42, "ug/m3", 35)
        self.assertTrue(r["breach"])
        self.assertEqual(len(self.env.exceedances()), 1)

    def test_equal_to_limit_not_breach(self):
        r = self.env.record_reading("S-1", "pm25", 35, "ug/m3", 35)
        self.assertFalse(r["breach"])

    def test_non_numeric_rejected(self):
        with self.assertRaises(ValueError):
            self.env.record_reading("S-1", "pm25", "high", "ug/m3", 35)

    def test_filters(self):
        self.env.record_reading("S-1", "pm25", 20, "ug/m3", 35)
        self.env.record_reading("S-2", "pm25", 20, "ug/m3", 35)
        self.env.record_reading("S-1", "lead", 5, "ppb", 15)
        self.assertEqual(len(self.env.list_readings(station_id="S-1")), 2)
        self.assertEqual(len(self.env.list_readings(metric="pm25")), 2)

    def test_stations_summary(self):
        self.env.record_reading("S-1", "pm25", 70, "ug/m3", 35)
        self.env.record_reading("S-1", "lead", 30, "ppb", 15)
        s = self.env.stations_summary()
        self.assertEqual(len(s), 1)
        self.assertEqual(s[0]["readings"], 2)
        self.assertEqual(s[0]["breaches"], 2)
        self.assertEqual(s[0]["worst_ratio"], 2.0)

    def test_persistence(self):
        d = tempfile.mkdtemp()
        a = EnvironmentKeeper(d)
        a.record_reading("S-1", "pm25", 20, "ug/m3", 35)
        b = EnvironmentKeeper(d)
        self.assertEqual(len(b.list_readings()), 1)


if __name__ == "__main__":
    unittest.main()
