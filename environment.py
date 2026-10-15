"""the-shield: EnvironmentKeeper class.

EPA's one job: air and water stay within limits. This class is the
nation's environmental reading registry: monitoring stations record
readings against a limit, and exceedance alerts fire when a reading
breaches its limit. It records and alerts; it does not clean anything
up. Cleanup is a separate job.
"""

import datetime
import json
import os

SOURCE_LABEL = "nation environmental registry"


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class EnvironmentKeeper:
    """Environmental reading registry with exceedance alerts."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._path = os.path.join(data_dir, "readings.json")
        self._load()

    # -- persistence ---------------------------------------------------
    def _load(self):
        if os.path.exists(self._path):
            with open(self._path) as f:
                doc = json.load(f)
        else:
            doc = {}
        self.readings = doc.get("readings", [])

    def _save(self):
        with open(self._path, "w") as f:
            json.dump({"source": SOURCE_LABEL, "readings": self.readings},
                      f, indent=2)

    # -- readings ---------------------------------------------------------
    def record_reading(self, station_id, metric, value, unit, limit,
                       timestamp=None):
        """Record one station reading against its legal limit.

        A reading breaches when value > limit. Returns the record.
        """
        try:
            value = float(value)
            limit = float(limit)
        except (TypeError, ValueError):
            raise ValueError("value and limit must be numbers")
        rec = {
            "station_id": station_id,
            "metric": metric,
            "value": value,
            "unit": unit,
            "limit": limit,
            "breach": value > limit,
            "timestamp": timestamp or _utcnow(),
            "recorded_at": _utcnow(),
            "source": SOURCE_LABEL,
        }
        self.readings.append(rec)
        self._save()
        return rec

    def list_readings(self, station_id=None, metric=None):
        out = self.readings
        if station_id:
            out = [r for r in out if r["station_id"] == station_id]
        if metric:
            out = [r for r in out if r["metric"] == metric]
        return out

    # -- alerts --------------------------------------------------------------
    def exceedances(self):
        """All readings currently breaching their limit, newest first."""
        out = [r for r in self.readings if r["breach"]]
        out.sort(key=lambda r: r["timestamp"], reverse=True)
        return out

    def stations_summary(self):
        """Per station: reading count, breach count, worst breach ratio."""
        by_station = {}
        for r in self.readings:
            s = by_station.setdefault(r["station_id"], {
                "station_id": r["station_id"],
                "readings": 0,
                "breaches": 0,
                "worst_ratio": 0.0,
                "worst_metric": None,
            })
            s["readings"] += 1
            if r["breach"]:
                s["breaches"] += 1
                ratio = r["value"] / r["limit"] if r["limit"] else 0.0
                if ratio > s["worst_ratio"]:
                    s["worst_ratio"] = round(ratio, 3)
                    s["worst_metric"] = r["metric"]
        return [by_station[k] for k in sorted(by_station)]
