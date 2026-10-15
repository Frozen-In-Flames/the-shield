"""the-shield: AirSafety class.

FAA's one job: aircraft stay separated. This class is the nation's
airspace registry: flights are filed with an altitude band and a time
window, and a conflict detector flags overlapping flights in the same
band and window. It records and alerts; it does not direct traffic.
Direction is a separate job.
"""

import datetime
import json
import os

SOURCE_LABEL = "nation airspace registry"

# Altitude bands, feet. A flight occupies exactly one band.
BANDS = {
    "low": (0, 10000),
    "mid": (10000, 25000),
    "high": (25000, 60000),
}


def _parse(dt):
    return datetime.datetime.fromisoformat(dt)


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class AirSafety:
    """Airspace registry with flight records and conflict detection."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._path = os.path.join(data_dir, "flights.json")
        self._load()

    # -- persistence ---------------------------------------------------
    def _load(self):
        if os.path.exists(self._path):
            with open(self._path) as f:
                doc = json.load(f)
        else:
            doc = {}
        self.flights = doc.get("flights", {})

    def _save(self):
        with open(self._path, "w") as f:
            json.dump({"source": SOURCE_LABEL, "flights": self.flights},
                      f, indent=2)

    # -- flights ----------------------------------------------------------
    def file_flight(self, flight_id, origin, destination, band,
                    window_start, window_end):
        """File a flight plan. Returns the flight record."""
        if band not in BANDS:
            raise ValueError("band must be one of %s" % ", ".join(BANDS))
        start, end = _parse(window_start), _parse(window_end)
        if end <= start:
            raise ValueError("window_end must be after window_start")
        if flight_id in self.flights:
            raise ValueError("flight %s already filed" % flight_id)
        rec = {
            "flight_id": flight_id,
            "origin": origin,
            "destination": destination,
            "band": band,
            "window_start": window_start,
            "window_end": window_end,
            "filed_at": _utcnow(),
            "source": SOURCE_LABEL,
        }
        self.flights[flight_id] = rec
        self._save()
        return rec

    def cancel_flight(self, flight_id):
        if flight_id not in self.flights:
            raise ValueError("unknown flight %s" % flight_id)
        rec = self.flights.pop(flight_id)
        self._save()
        return rec

    def list_flights(self):
        return [self.flights[k] for k in sorted(self.flights)]

    # -- conflict detection --------------------------------------------------
    @staticmethod
    def _windows_overlap(a_start, a_end, b_start, b_end):
        return a_start < b_end and b_start < a_end

    def detect_conflicts(self):
        """Flag flight pairs sharing a band with overlapping windows.

        Returns a list of conflict records, each naming the two flights,
        the shared band, and the overlapping window. Sorted by flight id.
        """
        flights = self.list_flights()
        conflicts = []
        for i in range(len(flights)):
            for j in range(i + 1, len(flights)):
                a, b = flights[i], flights[j]
                if a["band"] != b["band"]:
                    continue
                a_s, a_e = _parse(a["window_start"]), _parse(a["window_end"])
                b_s, b_e = _parse(b["window_start"]), _parse(b["window_end"])
                if not self._windows_overlap(a_s, a_e, b_s, b_e):
                    continue
                overlap_start = max(a_s, b_s).isoformat()
                overlap_end = min(a_e, b_e).isoformat()
                conflicts.append({
                    "flight_a": a["flight_id"],
                    "flight_b": b["flight_id"],
                    "band": a["band"],
                    "band_feet": BANDS[a["band"]],
                    "overlap_start": overlap_start,
                    "overlap_end": overlap_end,
                    "detected_at": _utcnow(),
                    "source": SOURCE_LABEL,
                })
        return conflicts
