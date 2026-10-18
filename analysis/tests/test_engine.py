import filecmp
from pathlib import Path

import config
import engine
import oracle

REPO = Path(__file__).resolve().parents[2]


def test_linda_wire_is_paused_and_tommy_is_asked(decide):
    d = decide("P1001-003")
    assert d["decision"] == "MISMATCH_PAUSE"
    assert d["hold_window"] == "up to 4h hold"
    asked = d["contact_asked"]
    assert asked["name"] == "Tommy" and asked["relationship"] == "grandson"
    assert asked["on_file_days"] == 240
    assert asked["shows"] == {"amount": "$8,500.00", "bank": "Cascade Federal Bank", "account_masked": "••••8723"}
    assert asked["answers"] == ["Yes, it's my account", "No, it's not mine"]


def test_m1037_family_payment_paused_then_yes_completes_fast(decide, data):
    d = decide("P1037-002")
    assert d["decision"] == "MISMATCH_PAUSE"
    assert d["hold_window"] == "before submit"
    key_row = data["key"]["M1037"]
    assert key_row["is_legitimate_lookalike"] == "Yes"
    sim = oracle.simulate(d, key_row, is_scam=False)
    assert sim["simulated_answer"] == "Yes, it's my account"
    assert sim["stop_probability"] == 0
    assert sim["friction_minutes"] <= 10


def _new_p2p(recipient_id, **overrides):
    ev = {
        "event_id": "T1",
        "synthetic_member_id": "M9999",
        "event_sequence": "10",
        "event_timestamp": "10/10/2026 10:00",
        "event_type": "Payment Initiated",
        "channel": "Mobile",
        "payment_id": "P9999-001",
        "payment_rail": "P2P",
        "amount": "250.00",
        "recipient_id": recipient_id,
        "recipient_status": "New",
        "recipient_age_days": "0",
        "days_since_last_same_rail": "3",
        "amount_to_baseline_ratio": "0.8",
        "amount_vs_member_baseline": "Typical",
        "payment_velocity_band": "Low",
        "profile_change_recent": "No",
        "password_reset_recent": "No",
    }
    ev.update(overrides)
    return ev


CONTACT = {
    "contact_id": "C9999-1",
    "name": "Ava",
    "relationship": "child",
    "phone_masked": "(•••) •••-0001",
    "phone_added_at": "2025-01-01",
    "accounts": ["R9999-01"],
}


def _ctx(**extra):
    ctx = {
        "stated": {"type": "saved_contact", "contact_id": "C9999-1"},
        "contacts": {"C9999-1": CONTACT},
        "recipients": {
            "R9999-01": {"bank": "Evergreen National", "account_masked": "••••1111", "owner_contact_id": "C9999-1"},
            "R9999-02": {"bank": "Sound", "account_masked": "••••2222", "owner_contact_id": "C9999-1"},
        },
    }
    ctx.update(extra)
    return ctx


def test_verified_contact_payment_passes_with_zero_friction():
    # Sound account owned by the contact: matches by owner even though it's new.
    d = engine.evaluate(_new_p2p("R9999-02"), [], _ctx())
    assert d["decision"] == "PASS" and d["contact_asked"] is None
    assert config.FRICTION_MINUTES[d["decision"]] == 0
    # External account the contact was paid at successfully 45 days ago.
    d = engine.evaluate(_new_p2p("R9999-01", recipient_status="Existing", recipient_age_days="45"), [], _ctx())
    assert d["decision"] == "PASS"
    # Same external account, but only 12 days old: not verified yet.
    d = engine.evaluate(_new_p2p("R9999-01", recipient_age_days="12"), [], _ctx())
    assert d["decision"] == "MISMATCH_PAUSE"


def test_contact_with_new_phone_is_never_asked():
    ctx = _ctx(contacts={"C9999-1": dict(CONTACT, phone_added_at="2026-10-07")})
    d = engine.evaluate(_new_p2p("R9999-03"), [], ctx)
    assert d["decision"] == "EMPLOYEE_OUTREACH" and d["contact_asked"] is None
    assert any("number you already know" in r for r in d["reasons"])
    # A recent profile change on the member's account also blocks the question.
    d = engine.evaluate(_new_p2p("R9999-03", profile_change_recent="Yes"), [], _ctx())
    assert d["decision"] == "EMPLOYEE_OUTREACH"


def test_takeover_never_confirmed_via_recently_changed_phone_or_email(decide, data):
    ato = [m for m, k in data["key"].items() if k["scenario_type"] == "Sound Impersonation + ATO"]
    scams = oracle.scam_payment_ids(data["key"])
    checked = 0
    for m in ato:
        rows = data["by_member"][m]
        for ev in rows:
            if ev["event_type"] != "Payment Initiated" or ev["payment_id"] not in scams:
                continue
            d = decide(ev["payment_id"])
            assert d["decision"] in ("STEP_UP_PRE_CHANGE_CONTACT", "EMPLOYEE_OUTREACH")
            asked = d["contact_asked"]
            if asked is None:
                continue
            now = engine.parse_ts(ev["event_timestamp"])
            changed = [
                r for r in rows
                if engine.CHANNEL_CHANGE_EVENTS.get(r["event_type"]) == asked["channel"]
                and 0 <= (now - engine.parse_ts(r["event_timestamp"])).days < 7
                and int(r["event_sequence"]) < int(ev["event_sequence"])
            ]
            ch = data["ov"][m]["member_channels"][asked["channel"]]
            if changed:
                assert asked["value"] == "pre_change"
                assert asked["masked"] == ch["masked"] != ch["masked_after_change"]
            assert asked["on_file_days"] >= config.CONTACT_MIN_ON_FILE_DAYS
            checked += 1
    assert checked >= 20


def test_engine_reads_only_observable_fields_and_earlier_rows(decide, data):
    scrub = {"event_note": "SCAM!", "member_response": "Reported Not Me", "payment_status": "Stopped by Sound",
             "warning_displayed": "Yes", "case_open": "Yes", "employee_interaction": "Yes",
             "trusted_contact_enrolled": "Yes", "available_balance_after": "0"}
    for pid, ev in data["initiated"].items():
        m = ev["synthetic_member_id"]
        full = data["by_member"][m]
        base = decide(pid)
        truncated = [r for r in full if int(r["event_sequence"]) <= int(ev["event_sequence"])]
        assert decide(pid, history=truncated) == base, pid
        poisoned = [dict(r, **scrub) for r in full]
        assert decide(pid, history=poisoned, event=dict(ev, **scrub)) == base, pid
        for s in base["signals_used"]:
            # Event fields must be observable; the rest come from Sound's records (overlay) or member input.
            assert s in engine.OBSERVABLE_FIELDS or s in (
                "stated_recipient", "contact.phone_on_file_days", "contact_verified_account", "member_channel_change_history"
            ), s


def test_engine_has_no_member_key_or_pandas_dependency():
    src = (Path(engine.__file__)).read_text()
    for banned in ("import pandas", "import oracle", "Member_Key", "scam_payment_ids", "is_legitimate_lookalike"):
        assert banned not in src


def test_backend_copy_is_in_sync():
    for name in ("engine.py", "config.py"):
        assert filecmp.cmp(REPO / "analysis" / name, REPO / "backend" / "vcp" / name, shallow=False), name
