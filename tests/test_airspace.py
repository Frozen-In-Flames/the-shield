import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from airspace import AirSafety


class TestAirSafety(unittest.TestCase):
    def setUp(self):
        self.air = AirSafety(tempfile.mkdtemp())

    def _file(self, fid, band="high", start="2026-10-16T08:00",
              end="2026-10-16T10:00"):
        return self.air.file_flight(fid, "AAA", "BBB", band, start, end)

    def test_file_and_list(self):
        self._file("FL-1")
        self.assertEqual(len(self.air.list_flights()), 1)

    def test_bad_band_rejected(self):
        with self.assertRaises(ValueError):
            self._file("FL-1", band="orbit")

    def test_bad_window_rejected(self):
        with self.assertRaises(ValueError):
            self._file("FL-1", start="2026-10-16T10:00",
                       end="2026-10-16T08:00")

    def test_conflict_same_band_overlap(self):
        self._file("FL-1", start="2026-10-16T08:00", end="2026-10-16T10:00")
        self._file("FL-2", start="2026-10-16T09:00", end="2026-10-16T11:00")
        c = self.air.detect_conflicts()
        self.assertEqual(len(c), 1)
        self.assertEqual(c[0]["flight_a"], "FL-1")
        self.assertEqual(c[0]["flight_b"], "FL-2")
        self.assertEqual(c[0]["band"], "high")

    def test_no_conflict_different_bands(self):
        self._file("FL-1", band="high")
        self._file("FL-2", band="low")
        self.assertEqual(self.air.detect_conflicts(), [])

    def test_no_conflict_disjoint_windows(self):
        self._file("FL-1", start="2026-10-16T08:00", end="2026-10-16T09:00")
        self._file("FL-2", start="2026-10-16T09:00", end="2026-10-16T10:00")
        self.assertEqual(self.air.detect_conflicts(), [])

    def test_touching_windows_not_conflict(self):
        # end == start is not an overlap
        self._file("FL-1", start="2026-10-16T08:00", end="2026-10-16T09:00")
        self._file("FL-2", start="2026-10-16T09:00", end="2026-10-16T10:00")
        self.assertEqual(self.air.detect_conflicts(), [])

    def test_cancel_removes_conflict(self):
        self._file("FL-1")
        self._file("FL-2")
        self.assertEqual(len(self.air.detect_conflicts()), 1)
        self.air.cancel_flight("FL-2")
        self.assertEqual(self.air.detect_conflicts(), [])

    def test_cancel_unknown_rejected(self):
        with self.assertRaises(ValueError):
            self.air.cancel_flight("NOPE")


if __name__ == "__main__":
    unittest.main()
