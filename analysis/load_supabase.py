"""Load the replay into Supabase (idempotent: every table is upserted on its primary key).

Needs the sim_* tables from supabase/migrations/20261017010000_replay.sql, and
SUPABASE_URL plus SUPABASE_SERVICE_ROLE_KEY in backend/.env. The key stays local
and server-side; nothing here prints it.

Run: analysis/.venv/bin/python analysis/load_supabase.py [--dry-run]
"""

import json
import sys
import math
import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

import config
import engine
import overlay
import replay

ROOT = Path(__file__).resolve().parent.parent
BATCH = 500


def client():
    load_dotenv(ROOT / "backend" / ".env")
    url = os.getenv("SUPABASE_URL", "").strip().rstrip("/").removesuffix("/rest/v1")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not url or not key:
        raise SystemExit("Fill in SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env first.")
    return create_client(url, key)


def ts(value):
    return engine.parse_ts(value).isoformat() if value else None


def num(value, cast=float):
    if value in ("", None) or (isinstance(value, float) and math.isnan(value)):
        return None
    return cast(float(value))


def clean(v):
    if isinstance(v, float) and math.isnan(v):
        return None
    if hasattr(v, "item"):  # numpy scalar
        return v.item()
    return v


def upsert(sb, table, rows, key):
    for i in range(0, len(rows), BATCH):
        sb.table(table).upsert(rows[i : i + BATCH], on_conflict=key).execute()
    print(f"{table}: {len(rows)} rows")


def main(dry_run=False):
    met = replay.main()
    events = overlay.read_csv(overlay.EVENTS_CSV)
    key_rows = overlay.read_csv(overlay.KEY_CSV)
    ov, stated = overlay.load()
    full = replay.run_engine(replay.load_events(), ov, stated)
    dec = replay.pd.read_csv(replay.OUT / "decisions.csv", dtype=str, keep_default_na=False)
    ms = replay.pd.read_csv(replay.OUT / "member_summary.csv", dtype=str, keep_default_na=False)

    ev_rows = []
    for e in events:
        r = dict(e)
        r["event_sequence"] = int(e["event_sequence"])
        r["event_timestamp"] = ts(e["event_timestamp"])
        for f in ("amount", "available_balance_after", "amount_to_baseline_ratio"):
            r[f] = num(e[f])
        for f in ("recipient_age_days", "days_since_last_same_rail"):
            r[f] = num(e[f], int)
        ev_rows.append(r)

    kr = []
    for k in key_rows:
        r = dict(k)
        r["incident_start"], r["first_intervention"] = ts(k["incident_start"]), ts(k["first_intervention"])
        for f in ("dollars_attempted", "dollars_sent", "dollars_prevented", "dollars_recovered", "net_member_loss"):
            r[f] = num(k[f])
        kr.append(r)

    dr = []
    bools = ("is_scam_payment", "paused_before_money_moved", "actual_money_moved", "actual_intervened")
    for d in dec.to_dict("records"):
        _, out = full[d["payment_id"]]
        dr.append(
            {
                **{f: d[f] for f in ("payment_id", "synthetic_member_id", "channel", "payment_rail", "recipient_id",
                                     "recipient_status", "decision", "member_group", "simulated_answer",
                                     "actual_final_status", "actual_member_response", "disclaimer")},
                "event_timestamp": ts(d["event_timestamp"]),
                "amount": num(d["amount"]),
                "reasons": out["reasons"],
                "contact_asked": out["contact_asked"],
                "hold_window": out["hold_window"],
                "signals_used": out["signals_used"],
                **{f: d[f] == "True" for f in bools},
                "friction_minutes": int(d["friction_minutes"]),
                "stop_probability": num(d["stop_probability"]),
                "expected_dollars_stopped": num(d["expected_dollars_stopped"]),
                "actual_first_intervention_ts": ts(d["actual_first_intervention_ts"]),
            }
        )

    mr = []
    ints = ("payments_initiated", "scam_payments", "scam_payments_paused", "key_minutes_to_intervention",
            "our_minutes_to_intervention", "payments_flagged", "non_scam_payments_flagged", "friction_minutes",
            "non_scam_friction_minutes")
    nums = ("scam_dollars_attempted", "scam_dollars_paused", "expected_dollars_stopped", "key_dollars_attempted",
            "key_dollars_sent", "key_dollars_prevented")
    for m in ms.to_dict("records"):
        r = dict(m)
        for f in ints:
            r[f] = num(m[f], int)
        for f in nums:
            r[f] = num(m[f])
        for f in ("incident_start", "key_first_intervention", "our_first_intervention"):
            r[f] = ts(m[f])
        mr.append(r)

    walk = (replay.OUT / "walkthroughs.md").read_text()
    tables = [
        ("sim_events", ev_rows, "event_id"),
        ("sim_member_key", kr, "synthetic_member_id"),
        ("sim_decisions", dr, "payment_id"),
        ("sim_member_summary", mr, "synthetic_member_id"),
        ("sim_metrics", [{"id": "latest", "metrics": json.loads(json.dumps(met, default=clean)), "walkthroughs": walk}], "id"),
    ]
    if dry_run:
        for name, rows, _ in tables:
            json.dumps(rows)  # fails loudly on anything the API couldn't serialize
            print(f"{name}: {len(rows)} rows (dry run, nothing sent)")
        return
    sb = client()
    for name, rows, key in tables:
        upsert(sb, name, rows, key)
    print(config.DISCLAIMER)


if __name__ == "__main__":
    main(dry_run="--dry-run" in sys.argv)
