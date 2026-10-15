# the-shield

Safety core for a new nation. Step 3 of the Nation Kit's 17-to-1
reverse-SDG build sequence.

## The idea

Every federal agency is one class with one job. This build centralizes the
three safety classes:

- `FoodDrugSafety` — one job: nothing sold kills people. Product safety
  registry with adverse-event reports and a recall tracker (issue, list,
  resolve).
- `AirSafety` — one job: aircraft stay separated. Airspace registry of
  filed flights plus a conflict detector that flags overlapping flights
  in the same altitude band and time window.
- `EnvironmentKeeper` — one job: air and water stay within limits.
  Environmental reading registry with exceedance alerts when a reading
  breaches its limit.

## SDGs unlocked

This build unlocks **SDG 13 (Climate Action)**, **SDG 14 (Life Below
Water)**, **SDG 15 (Life on Land)**, and **SDG 3 (Good Health and
Well-Being)**:

- `EnvironmentKeeper` maps to 13, 14, and 15: climate, oceans, and land
  are protected by measuring them against limits and sounding the alarm
  when the limits break.
- `FoodDrugSafety` maps to 3: a population cannot be healthy if what it
  buys can kill it.

It is step 3 of the 17-to-1 sequence because a nation must keep its
people alive and its land and water within limits before it builds the
shared infrastructure (step 5, the-commons) and the welfare outcomes
(step 6, the-safety-net) on top of them. Safety is a prerequisite, not
an outcome.

## Usage

```bash
# Food and drug safety
python3 shield_cli.py food register --id P-001 --name PainAway --category drug --maker "Acme Pharma"
python3 shield_cli.py food event --product P-001 --severity serious --description "rash reports" --reporter "Clinic A"
python3 shield_cli.py food recall --product P-001 --reason "contamination in lot 42" --scope "lot 42"
python3 shield_cli.py food recalls
python3 shield_cli.py food resolve --recall R-1
python3 shield_cli.py food summary

# Air safety
python3 shield_cli.py air file --id FL-101 --origin AAA --destination BBB --band high --start 2026-10-16T08:00 --end 2026-10-16T10:00
python3 shield_cli.py air file --id FL-102 --origin CCC --destination DDD --band high --start 2026-10-16T09:00 --end 2026-10-16T11:00
python3 shield_cli.py air conflicts
python3 shield_cli.py air flights
python3 shield_cli.py air cancel --id FL-102

# Environment
python3 shield_cli.py env record --station RIVER-1 --metric lead --value 22 --unit ppb --limit 15
python3 shield_cli.py env record --station AIR-1 --metric pm25 --value 20 --unit ug/m3 --limit 35
python3 shield_cli.py env exceedances
python3 shield_cli.py env stations
python3 shield_cli.py env readings --station RIVER-1
```

Data lives in `data/` (JSON). `--data-dir` overrides the location.

## Data sources and labels

All records are the nation's own registry entries. Every record carries a
`source` label ("nation product safety registry", "nation airspace
registry", or "nation environmental registry") and timestamps
(`registered_at`, `filed_at`, `recorded_at`, `issued_at`) in UTC. No
external data, no estimates.

## Honest limits

These are registries. They record and alert; they do not enforce.

- `FoodDrugSafety` flags products with serious or fatal events and no
  active recall as NEEDS REVIEW. Issuing the recall, pulling the product,
  and punishing the maker are enforcement, a separate job.
- `AirSafety` detects conflicts. Rerouting aircraft and grounding
  violators are air-traffic control, a separate job.
- `EnvironmentKeeper` sounds exceedance alerts. Cleanup and penalties
  are enforcement, a separate job.

Conflict detection compares flights in the same altitude band
(low 0-10k ft, mid 10-25k ft, high 25-60k ft) with overlapping time
windows. It does not model routes, speeds, or vertical separation
inside a band.

## Tests

```bash
python3 -m unittest discover -s tests
```

27 tests, no network access. TRL 8: complete, tested, demonstrated,
released. The gap to 9 is operational use by a real safety authority.
