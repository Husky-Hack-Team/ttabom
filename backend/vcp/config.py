"""Thresholds and replay assumptions for the Verified Contact Payment check.

Everything a reviewer might want to argue with lives here, so changing a number
never means hunting through engine code. Pure Python: the backend imports a copy.
"""

DISCLAIMER = "Synthetic data, about 41% scam victims by design. Not a measure of real-world performance."

# --- Rails -----------------------------------------------------------------
# Starter Kit capability assumptions: wires, ACH, and external transfers can be
# held up to 4 hours; P2P can't be recalled, so the check runs before submit;
# large cash happens in a branch with an employee.
HOLDABLE_RAILS = ("Wire", "ACH", "External Transfer")
PRE_SUBMIT_RAILS = ("P2P",)
BRANCH_RAILS = ("Cash",)
OUT_OF_SCOPE_RAILS = ("Debit Card", "Bill Pay", "Automatic Payment", "Not Applicable", "")

HOLD_WINDOW_HOURS = 4
HOLD_WINDOWS = {
    "Wire": "up to 4h hold",
    "ACH": "up to 4h hold",
    "External Transfer": "up to 4h hold",
    "P2P": "before submit",
    "Cash": "at the branch counter",
}

# --- Verification and contact eligibility ------------------------------------
# An external account counts as verified for a contact only once it has been
# paid successfully at least this many days before the payment under test.
VERIFIED_MIN_DAYS = 30
# Questions and codes go only to contact details on file at least this long
# and not recently changed (resolution 4).
CONTACT_MIN_ON_FILE_DAYS = 7
# A member phone/email changed within this many days is never used for a
# step-up; the pre-change value is used instead.
CHANNEL_CHANGE_LOOKBACK_DAYS = 7

# --- Escalation for new payees -------------------------------------------------
ESCALATE_BASELINE_BANDS = ("Significantly Above Typical",)
ESCALATE_DAYS_SINCE_LAST_SAME_RAIL = 365

# --- Replay assumptions (scoring only; the engine never reads these) ------------
# Share of members who cancel after their contact says "No, it's not mine".
CANCEL_RATE_AFTER_NOT_MINE = 0.8
CANCEL_RATE_SENSITIVITY = (0.5, 0.8, 1.0)
# Share of account-takeover payments stopped when the real member, reached on
# pre-change contact info, says "That wasn't me". Sound can stop ATO payments.
ATO_STOP_RATE = 1.0
# Stops from an employee conversation alone are NOT credited: the replay has no
# truthful way to simulate how a coached victim responds to staff. Counted as
# "paused", never as "stopped".
EMPLOYEE_STOP_RATE = 0.0
# A one-tap "Yes, I meant to pay this new payee" is assumed never to stop a scam
# (victims believe the story) and never to stop a legitimate payment.
CONFIRM_STOP_RATE = 0.0

# Friction minutes added to the member's payment, by decision.
FRICTION_MINUTES = {
    "PASS": 0,                         # fast path
    "NEW_PAYEE_CONFIRM": 1,            # one-tap confirm
    "STEP_UP_PRE_CHANGE_CONTACT": 1,   # one-tap confirm on pre-change phone/email
    "MISMATCH_PAUSE": 10,              # contact answers
    "BRANCH_EMPLOYEE_PROMPT": 10,      # teller asks the scam questions (assumption)
    "EMPLOYEE_REVIEW_HOLD": 60,        # employee review
    "EMPLOYEE_OUTREACH": 60,           # employee reaches member on a known number
}
