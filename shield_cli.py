#!/usr/bin/env python3
"""the-shield CLI: safety core for a new nation.

Subcommands:
  food register --id ID --name NAME --category CAT --maker MAKER
  food event --product ID --severity S --description D --reporter R
  food recall --product ID --reason R --scope S
  food recalls [--all]
  food resolve --recall R-ID
  food summary [--product ID]
  air file --id ID --origin O --destination D --band BAND
             --start ISO --end ISO
  air flights
  air conflicts
  air cancel --id ID
  env record --station S --metric M --value V --unit U --limit L [--at ISO]
  env readings [--station S] [--metric M]
  env exceedances
  env stations

Global: --data-dir DIR (default: data/)
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from food_drug import FoodDrugSafety
from airspace import AirSafety, BANDS
from environment import EnvironmentKeeper


def _iso(s):
    return s


def main(argv=None):
    ap = argparse.ArgumentParser(prog="shield_cli.py",
                                 description="the-shield: safety core")
    ap.add_argument("--data-dir", default="data/",
                    help="registry storage directory")
    sub = ap.add_subparsers(dest="area", required=True)

    # -- food -----------------------------------------------------------
    food = sub.add_parser("food")
    fsub = food.add_subparsers(dest="cmd", required=True)

    p = fsub.add_parser("register")
    p.add_argument("--id", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--category", required=True)
    p.add_argument("--maker", required=True)

    p = fsub.add_parser("event")
    p.add_argument("--product", required=True)
    p.add_argument("--severity", required=True,
                   choices=["mild", "moderate", "serious", "fatal"])
    p.add_argument("--description", required=True)
    p.add_argument("--reporter", required=True)

    p = fsub.add_parser("recall")
    p.add_argument("--product", required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--scope", required=True)

    p = fsub.add_parser("recalls")
    p.add_argument("--all", action="store_true",
                   help="include resolved recalls")

    p = fsub.add_parser("resolve")
    p.add_argument("--recall", required=True)

    p = fsub.add_parser("summary")
    p.add_argument("--product", default=None)

    # -- air ------------------------------------------------------------
    air = sub.add_parser("air")
    asub = air.add_subparsers(dest="cmd", required=True)

    p = asub.add_parser("file")
    p.add_argument("--id", required=True)
    p.add_argument("--origin", required=True)
    p.add_argument("--destination", required=True)
    p.add_argument("--band", required=True, choices=sorted(BANDS))
    p.add_argument("--start", required=True, help="ISO datetime")
    p.add_argument("--end", required=True, help="ISO datetime")

    asub.add_parser("flights")
    asub.add_parser("conflicts")

    p = asub.add_parser("cancel")
    p.add_argument("--id", required=True)

    # -- env ------------------------------------------------------------
    env = sub.add_parser("env")
    esub = env.add_subparsers(dest="cmd", required=True)

    p = esub.add_parser("record")
    p.add_argument("--station", required=True)
    p.add_argument("--metric", required=True)
    p.add_argument("--value", required=True)
    p.add_argument("--unit", required=True)
    p.add_argument("--limit", required=True)
    p.add_argument("--at", default=None, help="ISO datetime")

    p = esub.add_parser("readings")
    p.add_argument("--station", default=None)
    p.add_argument("--metric", default=None)

    esub.add_parser("exceedances")
    esub.add_parser("stations")

    args = ap.parse_args(argv)
    try:
        if args.area == "food":
            return _food(args)
        if args.area == "air":
            return _air(args)
        if args.area == "env":
            return _env(args)
    except ValueError as e:
        print("error: %s" % e)
        return 1
    return 0


def _food(args):
    fds = FoodDrugSafety(args.data_dir)
    c = args.cmd
    if c == "register":
        r = fds.register_product(args.id, args.name, args.category,
                                 args.maker)
        print("registered product %s (%s)" % (r["product_id"], r["name"]))
    elif c == "event":
        e = fds.report_adverse_event(args.product, args.severity,
                                     args.description, args.reporter)
        print("recorded %s event for %s" % (e["severity"], e["product_id"]))
    elif c == "recall":
        r = fds.issue_recall(args.product, args.reason, args.scope)
        print("issued recall %s for %s" % (r["recall_id"], r["product_id"]))
    elif c == "recalls":
        recs = fds.recalls if args.all else fds.active_recalls()
        if not recs:
            print("no recalls" if args.all else "no active recalls")
        for r in recs:
            print("%s | %s | %s | %s" % (r["recall_id"], r["product_id"],
                                         r["status"], r["reason"][:60]))
    elif c == "resolve":
        r = fds.resolve_recall(args.recall)
        print("resolved recall %s" % r["recall_id"])
    elif c == "summary":
        for s in fds.safety_summary(args.product):
            counts = ", ".join("%s=%d" % (k, v)
                               for k, v in s["event_counts"].items())
            flag = " NEEDS REVIEW" if s["needs_review"] else ""
            print("%s %s | %s | recall=%s%s" % (
                s["product_id"], s["name"], counts,
                "active" if s["active_recall"] else "none", flag))
    return 0


def _air(args):
    air = AirSafety(args.data_dir)
    c = args.cmd
    if c == "file":
        f = air.file_flight(args.id, args.origin, args.destination,
                            args.band, _iso(args.start), _iso(args.end))
        print("filed flight %s %s->%s band %s" % (
            f["flight_id"], f["origin"], f["destination"], f["band"]))
        conflicts = [x for x in air.detect_conflicts()
                     if x["flight_a"] == args.id or x["flight_b"] == args.id]
        for x in conflicts:
            print("CONFLICT: %s x %s band %s overlap %s..%s" % (
                x["flight_a"], x["flight_b"], x["band"],
                x["overlap_start"], x["overlap_end"]))
    elif c == "flights":
        flights = air.list_flights()
        if not flights:
            print("no flights filed")
        for f in flights:
            print("%s | %s->%s | band %s | %s..%s" % (
                f["flight_id"], f["origin"], f["destination"], f["band"],
                f["window_start"], f["window_end"]))
    elif c == "conflicts":
        conflicts = air.detect_conflicts()
        if not conflicts:
            print("no conflicts detected")
        for x in conflicts:
            print("CONFLICT: %s x %s band %s overlap %s..%s" % (
                x["flight_a"], x["flight_b"], x["band"],
                x["overlap_start"], x["overlap_end"]))
    elif c == "cancel":
        air.cancel_flight(args.id)
        print("cancelled flight %s" % args.id)
    return 0


def _env(args):
    env = EnvironmentKeeper(args.data_dir)
    c = args.cmd
    if c == "record":
        r = env.record_reading(args.station, args.metric, args.value,
                               args.unit, args.limit, timestamp=args.at)
        flag = " BREACH" if r["breach"] else ""
        print("recorded %s=%s %s at %s (limit %s)%s" % (
            r["metric"], r["value"], r["unit"], r["station_id"],
            r["limit"], flag))
    elif c == "readings":
        rows = env.list_readings(args.station, args.metric)
        if not rows:
            print("no readings")
        for r in rows:
            flag = " BREACH" if r["breach"] else ""
            print("%s | %s=%s %s (limit %s)%s" % (
                r["station_id"], r["metric"], r["value"], r["unit"],
                r["limit"], flag))
    elif c == "exceedances":
        rows = env.exceedances()
        if not rows:
            print("no exceedances: all readings within limits")
        for r in rows:
            print("EXCEEDANCE: %s %s=%s %s over limit %s at %s" % (
                r["station_id"], r["metric"], r["value"], r["unit"],
                r["limit"], r["timestamp"]))
    elif c == "stations":
        rows = env.stations_summary()
        if not rows:
            print("no stations")
        for s in rows:
            print("%s | readings=%d breaches=%d worst=%s x%s" % (
                s["station_id"], s["readings"], s["breaches"],
                s["worst_metric"] or "-", s["worst_ratio"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
