"""Reset the demo `transactions` table to the rows in supabase/seed.sql.

Deletes every transaction and re-inserts the seed rows, so the balance goes
back to the seed total. Uses SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY from
backend/.env, which may point at PRODUCTION, so it only previews by default.

  backend/.venv/bin/python backend/scripts/reset_demo_data.py         # preview, changes nothing
  backend/.venv/bin/python backend/scripts/reset_demo_data.py --yes   # actually reset
"""

import os
import re
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "supabase" / "seed.sql"
ROW = re.compile(r"\('((?:[^']|'')*)',\s*(-?\d+(?:\.\d+)?),\s*now\(\)\s*-\s*interval\s*'(\d+)\s+days?'\)")


def seed_rows():
    now = datetime.now(timezone.utc)
    rows = []
    for desc, amount, days in ROW.findall(SEED.read_text()):
        rows.append(
            {
                "description": desc.replace("''", "'"),
                "amount": str(Decimal(amount)),
                "created_at": (now - timedelta(days=int(days))).isoformat(),
            }
        )
    if not rows:
        raise SystemExit(f"No seed rows found in {SEED}")
    return rows


def main(apply):
    load_dotenv(ROOT / "backend" / ".env")
    url = os.getenv("SUPABASE_URL", "").strip().rstrip("/").removesuffix("/rest/v1")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not url or not key:
        raise SystemExit("Fill in SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env first.")
    sb = create_client(url, key)

    current = sb.table("transactions").select("id, description, amount").order("id").execute().data
    seed = seed_rows()
    total_now = sum(Decimal(str(r["amount"])) for r in current)
    total_seed = sum(Decimal(r["amount"]) for r in seed)
    print(f"Project: {url}")
    print(f"Now:   {len(current)} transactions, balance {total_now:,.2f}")
    for r in current:
        print(f"  delete #{r['id']}: {r['description']!r} {Decimal(str(r['amount'])):,.2f}")
    print(f"After: {len(seed)} seed transactions, balance {total_seed:,.2f}")
    if not apply:
        print("Preview only. Rerun with --yes to apply.")
        return
    if current:
        sb.table("transactions").delete().in_("id", [r["id"] for r in current]).execute()
    sb.table("transactions").insert(seed).execute()
    print("Done.")


if __name__ == "__main__":
    main(apply="--yes" in sys.argv)
