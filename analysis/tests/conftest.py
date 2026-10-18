import sys
from pathlib import Path

import pytest

ANALYSIS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ANALYSIS))

import oracle  # noqa: E402
import overlay  # noqa: E402


@pytest.fixture(scope="session")
def data():
    """Events (as dict rows), Member Key, and the overlay, built fresh from seed 2026."""
    overlay.build()
    events = overlay.read_csv(overlay.EVENTS_CSV)
    by_member = {}
    for e in events:
        by_member.setdefault(e["synthetic_member_id"], []).append(e)
    for rows in by_member.values():
        rows.sort(key=lambda r: int(r["event_sequence"]))
    ov, stated = overlay.load()
    return {
        "events": events,
        "by_member": by_member,
        "initiated": {e["payment_id"]: e for e in events if e["event_type"] == "Payment Initiated"},
        "key": oracle.load_key(overlay.KEY_CSV),
        "ov": ov,
        "stated": stated,
    }


@pytest.fixture(scope="session")
def decide(data):
    import engine

    def run(payment_id, history=None, event=None):
        ev = event or data["initiated"][payment_id]
        m = ev["synthetic_member_id"]
        ctx = dict(data["ov"][m], stated=data["stated"].get(payment_id))
        return engine.evaluate(ev, data["by_member"][m] if history is None else history, ctx)

    return run
