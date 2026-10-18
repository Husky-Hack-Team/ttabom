"""Verified Contact Payment check: one decision per "Payment Initiated" event.

Pure Python (no pandas) so the live transfer endpoint can import the same code.
A byte-identical copy lives in backend/vcp/engine.py; a test keeps them in sync.

Leakage rules this module enforces itself:
  * It reads only the fields in OBSERVABLE_FIELDS from the payment row.
  * It reads only earlier rows of the member's history (lower event_sequence),
    and never any row of the same payment, so Held/Released/member_response or
    a later payment_status can't reach a decision.
  * It never sees the Member Key. Truthful human answers are simulated in
    oracle.py, which the engine does not import.

evaluate() returns:
  decision       one of DECISIONS
  reasons        plain-language reasons, written for the member or employee
  contact_asked  who gets asked and on which channel, or None
  hold_window    where the pause happens for this rail, or None
  signals_used   the inputs that drove the decision
"""

from datetime import date, datetime

try:  # imported as a package (backend/vcp) or as a top-level module (analysis/)
    from . import config
except ImportError:  # pragma: no cover
    import config

DECISIONS = (
    "PASS",
    "NEW_PAYEE_CONFIRM",
    "MISMATCH_PAUSE",
    "STEP_UP_PRE_CHANGE_CONTACT",
    "EMPLOYEE_REVIEW_HOLD",
    "EMPLOYEE_OUTREACH",
    "BRANCH_EMPLOYEE_PROMPT",
)

# Fields marked "Yes" under Observable at Decision Time whose values are known
# at the moment of initiation. event_note ("Partly") and the lifecycle fields
# (warning_displayed, member_response, case_open, payment_status, ...) are left
# out on purpose: on an initiation row they carry no signal, and on later rows
# they describe what happened after the decision.
OBSERVABLE_FIELDS = (
    "event_id",
    "synthetic_member_id",
    "event_sequence",
    "event_timestamp",
    "event_type",
    "channel",
    "payment_id",
    "payment_rail",
    "amount",
    "recipient_id",
    "recipient_status",
    "recipient_age_days",
    "days_since_last_same_rail",
    "amount_to_baseline_ratio",
    "amount_vs_member_baseline",
    "payment_velocity_band",
    "profile_change_recent",
    "password_reset_recent",
)
# From earlier rows only: when the member's own phone or email changed.
HISTORY_FIELDS = ("event_sequence", "event_timestamp", "event_type", "payment_id")
CHANNEL_CHANGE_EVENTS = {"Phone Change": "phone", "Email Change": "email"}


def parse_ts(value):
    if isinstance(value, datetime):
        return value
    value = str(value).strip()
    for fmt in ("%m/%d/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise ValueError(f"Unrecognized timestamp: {value!r}")


def parse_date(value):
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _int(value, default=None):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def money(value):
    return f"${float(value):,.2f}"


def project(event):
    """The only view of the payment row the rules below may read."""
    return {f: event.get(f, "") for f in OBSERVABLE_FIELDS}


def prior_history(event, history):
    """Earlier rows of this member, minus every row of the same payment."""
    seq = _int(event.get("event_sequence"), 0)
    member = event.get("synthetic_member_id")
    pid = event.get("payment_id") or None
    rows = []
    for row in history or ():
        if row.get("synthetic_member_id", member) != member:
            continue
        if _int(row.get("event_sequence"), seq) >= seq:
            continue
        if pid and row.get("payment_id") == pid:
            continue
        rows.append({f: row.get(f, "") for f in HISTORY_FIELDS})
    return rows


def member_channel_status(ctx, history, now):
    """The member's phone and email, and which value is safe for a step-up.

    A value changed within CHANNEL_CHANGE_LOOKBACK_DAYS is never used. In its
    place we use the value on file before the change, if that had been on file
    for CONTACT_MIN_ON_FILE_DAYS at the time of the change.
    """
    channels = (ctx or {}).get("member_channels") or {}
    last_change = {}
    for row in history:
        kind = CHANNEL_CHANGE_EVENTS.get(row["event_type"])
        if kind:
            last_change[kind] = parse_ts(row["event_timestamp"])
    out = {}
    for kind in ("phone", "email"):
        info = channels.get(kind)
        if not info:
            continue
        original_added = parse_date(info["added_at"])
        changed = last_change.get(kind)
        if changed is None:
            days = (now.date() - original_added).days
            out[kind] = {
                "masked": info["masked"],
                "on_file_days": days,
                "changed_recently": False,
                "usable_value": "current" if days >= config.CONTACT_MIN_ON_FILE_DAYS else None,
            }
            continue
        days_since_change = (now - changed).total_seconds() / 86400
        recent = days_since_change < config.CHANNEL_CHANGE_LOOKBACK_DAYS
        prior_days_at_change = (changed.date() - original_added).days
        if recent:
            usable = "pre_change" if prior_days_at_change >= config.CONTACT_MIN_ON_FILE_DAYS else None
        else:
            usable = "current"
        out[kind] = {
            "masked": info.get("masked_after_change") if not recent else info["masked"],
            "current_masked": info.get("masked_after_change", ""),
            # For the pre-change value: how long it had been on file when it was replaced.
            "on_file_days": prior_days_at_change if recent else int(days_since_change),
            "changed_recently": recent,
            "changed_at": changed.strftime("%Y-%m-%d %H:%M"),
            "usable_value": usable,
        }
    return out


def contact_eligibility(contact, row, now):
    """Resolution 4: phone on file 7+ days and no recent profile change."""
    days = (now.date() - parse_date(contact["phone_added_at"])).days
    ok_phone = days >= config.CONTACT_MIN_ON_FILE_DAYS
    ok_profile = row["profile_change_recent"] != "Yes"
    return ok_phone and ok_profile, days


def is_verified_for(contact, recipient_id, row, ctx):
    """Resolution 3: Sound accounts match by owner; external only if verified."""
    acct = ((ctx or {}).get("recipients") or {}).get(recipient_id) or {}
    if acct.get("bank") == "Sound" and acct.get("owner_contact_id") == contact["contact_id"]:
        return True, "Sound account owned by this contact"
    age = _int(row["recipient_age_days"], 0)
    if (
        recipient_id in (contact.get("accounts") or ())
        and row["recipient_status"] == "Existing"
        and age >= config.VERIFIED_MIN_DAYS
    ):
        return True, f"account paid successfully {age} days ago"
    return False, ""


def _result(decision, reasons, signals, row, contact_asked=None, extra=None):
    out = {
        "decision": decision,
        "reasons": reasons,
        "contact_asked": contact_asked,
        "hold_window": None if decision == "PASS" else config.HOLD_WINDOWS.get(row["payment_rail"]),
        "signals_used": sorted(set(signals)),
    }
    if extra:
        out.update(extra)
    return out


def evaluate(event, history=(), ctx=None):
    """Decide what happens to one "Payment Initiated" event.

    event    the payment row (a dict of strings, as read from the events CSV)
    history  the member's rows; only earlier rows of other payments are used
    ctx      Sound's records at decision time, plus the member's own input:
             stated       {"type": "saved_contact"|"new_payee"|"myself", "contact_id"}
             contacts     {contact_id: {contact_id, name, relationship,
                           phone_masked, phone_added_at, accounts: [recipient_id]}}
             recipients   {recipient_id: {bank, account_masked, owner_contact_id}}
             member_channels {"phone"|"email": {masked, added_at, masked_after_change}}
    """
    row = project(event)
    ctx = ctx or {}
    if row["event_type"] and row["event_type"] != "Payment Initiated":
        raise ValueError("evaluate() runs on Payment Initiated events only")
    hist = prior_history(event, history)
    now = parse_ts(row["event_timestamp"])
    rail = row["payment_rail"]
    amount = money(row["amount"] or 0)
    signals = ["payment_rail"]

    if rail in config.OUT_OF_SCOPE_RAILS or rail not in config.HOLD_WINDOWS:
        return _result("PASS", [f"{rail or 'This payment type'} is outside this check."], signals, row)

    stated = ctx.get("stated") or {}
    stated_type = stated.get("type")
    contacts = ctx.get("contacts") or {}
    contact = contacts.get(stated.get("contact_id")) if stated_type == "saved_contact" else None

    # Cash has no destination account to show anyone, so a person handles it.
    if rail in config.BRANCH_RAILS:
        signals += ["amount", "amount_vs_member_baseline"]
        reasons = [
            f"{amount} in cash is handed over at the counter, so a teller asks a few questions first.",
            "If someone told you to withdraw cash and keep it secret, that is a scam sign.",
        ]
        if contact:
            signals.append("stated_recipient")
            reasons.append(
                f"You said this is for {contact['name']}. We suggest calling {contact['name']} "
                "on a number you already know before you take the cash."
            )
        return _result("BRANCH_EMPLOYEE_PROMPT", reasons, signals, row)

    recipient_id = row["recipient_id"]
    signals += ["recipient_status", "recipient_age_days"]
    if row["recipient_status"] == "Existing":
        return _result(
            "PASS",
            [f"You've paid this recipient before (added {row['recipient_age_days']} days ago)."],
            signals,
            row,
        )

    takeover = row["password_reset_recent"] == "Yes" or row["profile_change_recent"] == "Yes"
    takeover_reasons = []
    if takeover:
        signals += ["password_reset_recent", "profile_change_recent"]
        if row["password_reset_recent"] == "Yes":
            takeover_reasons.append("The password was reset in the last 7 days.")
        if row["profile_change_recent"] == "Yes":
            takeover_reasons.append("A phone, email, or address on the account changed in the last 30 days.")

    # Stated recipient is a saved contact: the destination must be theirs.
    if contact:
        signals.append("stated_recipient")
        verified, why = is_verified_for(contact, recipient_id, row, ctx)
        if verified:
            signals.append("contact_verified_account")
            return _result(
                "PASS",
                [f"This account is a verified account of {contact['name']} ({why})."],
                signals,
                row,
            )
        acct = (ctx.get("recipients") or {}).get(recipient_id) or {}
        eligible, phone_days = contact_eligibility(contact, row, now)
        signals += ["contact.phone_on_file_days", "profile_change_recent"]
        reasons = [
            f"You said this {amount} is for {contact['name']}, but this account isn't one "
            f"we've verified as {contact['name']}'s.",
        ] + takeover_reasons
        if eligible:
            reasons.append(
                f"We'll ask {contact['name']} on the phone number they've had on file for "
                f"{phone_days} days: is this their account? They can only answer yes or no; "
                "you make the final decision."
            )
            asked = {
                "who": "contact",
                "contact_id": contact["contact_id"],
                "name": contact["name"],
                "relationship": contact.get("relationship", ""),
                "channel": "phone",
                "masked": contact.get("phone_masked", ""),
                "on_file_days": phone_days,
                "shows": {
                    "amount": amount,
                    "bank": acct.get("bank", "Unknown bank"),
                    "account_masked": acct.get("account_masked", "••••"),
                },
                "answers": ["Yes, it's my account", "No, it's not mine"],
            }
            return _result("MISMATCH_PAUSE", reasons, signals, row, asked)
        why_not = (
            f"{contact['name']}'s phone was added only {phone_days} days ago"
            if phone_days < config.CONTACT_MIN_ON_FILE_DAYS
            else "contact details on this account changed recently"
        )
        reasons.append(
            f"We won't send the question because {why_not}. A Sound employee will reach you instead. "
            f"Please call {contact['name']} on a number you already know."
        )
        return _result("EMPLOYEE_OUTREACH", reasons, signals, row)

    # Possible takeover: confirm with the real owner on pre-change contact info.
    if takeover:
        channels = member_channel_status(ctx, hist, now)
        signals.append("member_channel_change_history")
        for kind in ("phone", "email"):
            info = channels.get(kind)
            if not info or not info["usable_value"]:
                continue
            pre = info["usable_value"] == "pre_change"
            asked = {
                "who": "member",
                "channel": kind,
                "value": info["usable_value"],
                "masked": info["masked"],
                "on_file_days": info["on_file_days"],
                "answers": ["Yes, I'm sending this", "No, that wasn't me"],
            }
            reasons = [f"This is a new recipient: {amount}."] + takeover_reasons
            reasons.append(
                f"We'll confirm on the {kind} that was on file before the change ({info['masked']})."
                if pre
                else f"We'll confirm on your {kind} on file for {info['on_file_days']} days ({info['masked']})."
            )
            for other, oinfo in channels.items():
                if oinfo["changed_recently"]:
                    reasons.append(f"The {other} changed on {oinfo['changed_at']}, so we won't use the new {other}.")
            return _result("STEP_UP_PRE_CHANGE_CONTACT", reasons, signals, row, asked)
        return _result(
            "EMPLOYEE_OUTREACH",
            [f"This is a new recipient: {amount}."]
            + takeover_reasons
            + ["No contact detail is old enough to trust, so a Sound employee will reach you on a number you already know."],
            signals,
            row,
        )

    # New payee (or "myself" to an unverified external account).
    signals.append("stated_recipient")
    who = "your own account at another bank" if stated_type == "myself" else "a new payee"
    reasons = [f"This {amount} goes to {who} we haven't verified yet (added {row['recipient_age_days']} days ago)."]
    escalate = []
    if rail in config.HOLDABLE_RAILS:
        signals += ["amount_vs_member_baseline", "days_since_last_same_rail"]
        if row["amount_vs_member_baseline"] in config.ESCALATE_BASELINE_BANDS:
            escalate.append(f"It's far above your usual payments ({row['amount_to_baseline_ratio']}x).")
        gap = _int(row["days_since_last_same_rail"])
        if gap is not None and gap >= config.ESCALATE_DAYS_SINCE_LAST_SAME_RAIL:
            escalate.append(f"It's your first {rail.lower()} in {gap:,} days.")
    if escalate:
        reasons += escalate + [
            f"A Sound employee will review it with you; we can hold it {config.HOLD_WINDOWS[rail]}.",
            "You make the final decision.",
        ]
        return _result("EMPLOYEE_REVIEW_HOLD", reasons, signals, row)
    if stated_type == "myself":
        reasons.append("Confirm it's yours; we'll verify ownership later, with micro-deposits only as a last resort.")
    else:
        reasons.append("Confirm you know this person or business. Sound will never ask you to move money.")
    return _result("NEW_PAYEE_CONFIRM", reasons, signals, row)
