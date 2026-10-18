"""Read-only replay endpoints for the employee Data Replay page and case screen.

sim_member_key is never selected here. Scoring columns (is_scam_payment, the
key's dollars) appear only on the employee-facing replay views; the case queue
returns engine output and observable event fields only.
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from . import config, engine

MEMBER_ID = re.compile(r"^M\d{4}$")
CASE_DECISIONS = (
    "MISMATCH_PAUSE",
    "EMPLOYEE_REVIEW_HOLD",
    "EMPLOYEE_OUTREACH",
    "BRANCH_EMPLOYEE_PROMPT",
    "STEP_UP_PRE_CHANGE_CONTACT",
)
FEATURED_CASE = "P1001-003"
# Observable fields only; the lifecycle fields after initiation stay out of the case view.
CASE_EVENT_FIELDS = (
    "event_id, event_sequence, event_timestamp, event_type, channel, payment_id, payment_rail, amount, "
    "recipient_id, recipient_status, recipient_age_days, days_since_last_same_rail, amount_vs_member_baseline, "
    "profile_change_recent, password_reset_recent"
)
MEMBER_FIELDS = (
    "synthetic_member_id, anchor_persona, member_group, scenario_type, scenario_subtype, payments_initiated, "
    "scam_payments, scam_payments_paused, payments_flagged, friction_minutes, key_journey_outcome"
)


def build_router(get_supabase):
    router = APIRouter(prefix="/api")

    @router.get("/replay/metrics")
    def replay_metrics():
        rows = get_supabase().table("sim_metrics").select("metrics, walkthroughs, loaded_at").eq("id", "latest").execute().data
        if not rows:
            raise HTTPException(404, "No replay loaded yet. Run analysis/load_supabase.py.")
        return {"disclaimer": config.DISCLAIMER, **rows[0]}

    @router.get("/replay/members")
    def replay_members(filter: Literal["all", "anchor", "lookalike", "scam", "routine"] = "all"):
        q = get_supabase().table("sim_member_summary").select(MEMBER_FIELDS).order("synthetic_member_id")
        if filter != "all":
            q = q.eq("member_group", filter)
        return {"disclaimer": config.DISCLAIMER, "members": q.execute().data}

    @router.get("/replay/members/{member_id}")
    def replay_member(member_id: str):
        if not MEMBER_ID.match(member_id):
            raise HTTPException(422, "Member IDs look like M1001.")
        sb = get_supabase()
        summary = sb.table("sim_member_summary").select("*").eq("synthetic_member_id", member_id).execute().data
        if not summary:
            raise HTTPException(404, f"No replay for {member_id}.")
        events = (
            sb.table("sim_events").select("*").eq("synthetic_member_id", member_id).order("event_sequence").execute().data
        )
        decisions = (
            sb.table("sim_decisions").select("*").eq("synthetic_member_id", member_id).order("event_timestamp").execute().data
        )
        return {"disclaimer": config.DISCLAIMER, "summary": summary[0], "events": events, "decisions": decisions}

    @router.get("/replay/cases")
    def replay_cases(limit: int = Query(25, ge=1, le=200)):
        sb = get_supabase()
        cols = (
            "payment_id, synthetic_member_id, event_timestamp, channel, payment_rail, amount, recipient_id, "
            "recipient_status, decision, reasons, contact_asked, hold_window, signals_used"
        )
        rows = (
            sb.table("sim_decisions").select(cols).in_("decision", list(CASE_DECISIONS))
            .order("event_timestamp", desc=True).limit(limit).execute().data
        )
        featured = sb.table("sim_decisions").select(cols).eq("payment_id", FEATURED_CASE).execute().data
        cases = featured + [r for r in rows if r["payment_id"] != FEATURED_CASE]
        for c in cases:
            started = datetime.fromisoformat(c["event_timestamp"])
            c["hold_expires_at"] = (
                (started + timedelta(hours=config.HOLD_WINDOW_HOURS)).isoformat()
                if c["payment_rail"] in config.HOLDABLE_RAILS
                else None
            )
        if featured:
            f = featured[0]
            seq = sb.table("sim_events").select("event_sequence").eq("payment_id", FEATURED_CASE).eq(
                "event_type", "Payment Initiated"
            ).execute().data[0]["event_sequence"]
            f["recent_events"] = (
                sb.table("sim_events").select(CASE_EVENT_FIELDS).eq("synthetic_member_id", f["synthetic_member_id"])
                .lte("event_sequence", seq).order("event_sequence", desc=True).limit(12).execute().data
            )
        return {"disclaimer": config.DISCLAIMER, "featured": FEATURED_CASE if featured else None, "cases": cases}

    class CheckIn(BaseModel):
        event: dict
        history: list[dict] = []
        ctx: dict = {}

    @router.post("/vcp/check")
    def vcp_check(body: CheckIn):
        # The same engine the replay scores, callable by a live transfer flow. No database access.
        event = {"event_type": "Payment Initiated", "event_sequence": "1", **{k: str(v) for k, v in body.event.items()}}
        # Accept "timestamp" as an alias, and default to now (UTC) when missing or empty.
        if not event.get("event_timestamp", "").strip():
            event["event_timestamp"] = event.pop("timestamp", "").strip() or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        try:
            return engine.evaluate(event, body.history, body.ctx)
        except (KeyError, ValueError) as exc:
            raise HTTPException(422, f"Can't evaluate this payment: {exc}") from exc

    return router
