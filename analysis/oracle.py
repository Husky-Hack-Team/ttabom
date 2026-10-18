"""ORACLE: the only module that reads the Member Key.

The Member Key is ground truth. It is used for exactly two things:
  1. scoring the replay (which payments were scams, what the key says happened);
  2. simulating truthful human input and answers: what the member says the
     payment is for, how a contact answers "Is this your account?", and how the
     real owner answers a takeover step-up.

It is NEVER a trigger input. engine.py does not import this module, and nothing
returned here is passed to engine.evaluate() except the simulated "stated
recipient", which stands in for what a real member would type on the screen.
"""

import csv

try:
    from . import config
except ImportError:  # pragma: no cover
    import config

FAMILY_SUBTYPES = ("Grandparent / fake attorney", "Helping a real family member")


def load_key(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {r["synthetic_member_id"]: r for r in csv.DictReader(f)}


def scam_payment_ids(key):
    return {p for r in key.values() for p in r["scam_payment_ids"].split(";") if p}


def needs_family_contact(key_row):
    """Anchors and every family-story member get a family contact (overlay rule)."""
    return bool(key_row["anchor_persona"]) or key_row["scenario_type"] == "Family Emergency" or (
        key_row["scenario_subtype"] == "Helping a real family member"
    )


def stated_recipient_type(key_row, is_scam):
    """Who the member would say a New-recipient or cash payment is for (simulated member input).

    The member answers honestly from their own point of view: a scam victim
    repeats the scammer's story, they don't know it's a scam.
    """
    sub = key_row["scenario_subtype"]
    stype = key_row["scenario_type"]
    if (stype == "Family Emergency" and is_scam) or sub == "Helping a real family member":
        return "saved_contact"  # "It's for my grandson" / "for my sister"
    if sub == "Funding a new brokerage account":
        return "myself"
    # Contractors, landlords, home closing, romance partner, "federal agent",
    # takeover payments, and routine new payees all read as a new payee/business.
    return "new_payee"


def contact_answer(is_scam):
    """A contact shown amount, bank, and masked account answers truthfully."""
    return "No, it's not mine" if is_scam else "Yes, it's my account"


def owner_answer(key_row, is_scam):
    """The real owner, reached on pre-change contact info, answers truthfully.

    Only a takeover scam is "not me": a victim of an authorized scam is the one
    sending the money, so they confirm.
    """
    if is_scam and key_row["scenario_type"] == "Sound Impersonation + ATO":
        return "No, that wasn't me"
    return "Yes, I'm sending this"


def simulate(decision, key_row, is_scam, cancel_rate=config.CANCEL_RATE_AFTER_NOT_MINE):
    """Simulated answer, stop probability, and friction for one decision."""
    d = decision["decision"]
    friction = config.FRICTION_MINUTES[d]
    answer = ""
    stop = 0.0
    if d == "MISMATCH_PAUSE":
        answer = contact_answer(is_scam)
        stop = cancel_rate if is_scam else 0.0
    elif d == "STEP_UP_PRE_CHANGE_CONTACT":
        answer = owner_answer(key_row, is_scam)
        stop = config.ATO_STOP_RATE if answer == "No, that wasn't me" else 0.0
    elif d == "NEW_PAYEE_CONFIRM":
        answer = "Confirmed"
        stop = config.CONFIRM_STOP_RATE if is_scam else 0.0
    elif d in ("EMPLOYEE_REVIEW_HOLD", "EMPLOYEE_OUTREACH", "BRANCH_EMPLOYEE_PROMPT"):
        answer = "Employee conversation"
        stop = config.EMPLOYEE_STOP_RATE if is_scam else 0.0
    return {"simulated_answer": answer, "stop_probability": stop, "friction_minutes": friction}
