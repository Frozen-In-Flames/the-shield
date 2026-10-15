"""the-shield: FoodDrugSafety class.

FDA's one job: nothing sold kills people. This class is the nation's
product safety registry: products are registered, adverse events are
reported, and recalls are issued, listed, and resolved. It records and
alerts; it does not enforce. Enforcement is a separate job.
"""

import datetime
import json
import os

SOURCE_LABEL = "nation product safety registry"


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class FoodDrugSafety:
    """Product safety registry with adverse-event reports and recalls."""

    def __init__(self, data_dir):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        self._path = os.path.join(data_dir, "products.json")
        self._load()

    # -- persistence ---------------------------------------------------
    def _load(self):
        if os.path.exists(self._path):
            with open(self._path) as f:
                doc = json.load(f)
        else:
            doc = {}
        self.products = doc.get("products", {})
        self.events = doc.get("adverse_events", [])
        self.recalls = doc.get("recalls", [])
        self._recall_seq = doc.get("recall_seq", 0)

    def _save(self):
        with open(self._path, "w") as f:
            json.dump({
                "source": SOURCE_LABEL,
                "products": self.products,
                "adverse_events": self.events,
                "recalls": self.recalls,
                "recall_seq": self._recall_seq,
            }, f, indent=2)

    # -- products ------------------------------------------------------
    def register_product(self, product_id, name, category, maker):
        """Record a product cleared for sale. Returns the product record."""
        if product_id in self.products:
            raise ValueError("product %s already registered" % product_id)
        rec = {
            "product_id": product_id,
            "name": name,
            "category": category,
            "maker": maker,
            "registered_at": _utcnow(),
            "source": SOURCE_LABEL,
        }
        self.products[product_id] = rec
        self._save()
        return rec

    def get_product(self, product_id):
        return self.products.get(product_id)

    def list_products(self):
        return [self.products[k] for k in sorted(self.products)]

    # -- adverse events -------------------------------------------------
    SEVERITIES = ("mild", "moderate", "serious", "fatal")

    def report_adverse_event(self, product_id, severity, description,
                             reporter):
        """File an adverse-event report against a registered product."""
        if product_id not in self.products:
            raise ValueError("unknown product %s" % product_id)
        if severity not in self.SEVERITIES:
            raise ValueError("severity must be one of %s"
                             % ", ".join(self.SEVERITIES))
        ev = {
            "product_id": product_id,
            "severity": severity,
            "description": description,
            "reporter": reporter,
            "reported_at": _utcnow(),
            "source": SOURCE_LABEL,
        }
        self.events.append(ev)
        self._save()
        return ev

    def events_for(self, product_id):
        return [e for e in self.events if e["product_id"] == product_id]

    # -- recalls ---------------------------------------------------------
    def issue_recall(self, product_id, reason, scope):
        """Issue a recall. Returns the recall record."""
        if product_id not in self.products:
            raise ValueError("unknown product %s" % product_id)
        self._recall_seq += 1
        rec = {
            "recall_id": "R-%d" % self._recall_seq,
            "product_id": product_id,
            "reason": reason,
            "scope": scope,
            "status": "active",
            "issued_at": _utcnow(),
            "resolved_at": None,
            "source": SOURCE_LABEL,
        }
        self.recalls.append(rec)
        self._save()
        return rec

    def active_recalls(self):
        return [r for r in self.recalls if r["status"] == "active"]

    def resolve_recall(self, recall_id):
        for r in self.recalls:
            if r["recall_id"] == recall_id:
                if r["status"] != "active":
                    raise ValueError("recall %s is not active" % recall_id)
                r["status"] = "resolved"
                r["resolved_at"] = _utcnow()
                self._save()
                return r
        raise ValueError("unknown recall %s" % recall_id)

    # -- safety rollup ----------------------------------------------------
    def safety_summary(self, product_id=None):
        """Per-product counts of events by severity and recall status.

        Flags products with serious or fatal events that have no active
        recall: those need a human decision, which this registry cannot
        make for them.
        """
        ids = [product_id] if product_id else sorted(self.products)
        out = []
        for pid in ids:
            if pid not in self.products:
                raise ValueError("unknown product %s" % pid)
            evs = self.events_for(pid)
            counts = {s: 0 for s in self.SEVERITIES}
            for e in evs:
                counts[e["severity"]] += 1
            has_active = any(r["product_id"] == pid
                             for r in self.active_recalls())
            out.append({
                "product_id": pid,
                "name": self.products[pid]["name"],
                "event_counts": counts,
                "active_recall": has_active,
                "needs_review": (counts["serious"] + counts["fatal"] > 0
                                 and not has_active),
                "source": SOURCE_LABEL,
            })
        return out
