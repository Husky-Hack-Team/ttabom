# Replay walkthroughs
> Synthetic data, about 41% scam victims by design. Not a measure of real-world performance.

Each card shows our check, computed only from what Sound could see at the moment the payment was started, next to what the synthetic data says actually happened.

## 1. Linda (M1001), P1001-003: $8,500 wire in a branch
| | |
|---|---|
| Payment | P1001-003 · Wire · $8,500.00 · Branch · 10/20/2026 14:11 |
| Recipient | R1001-11 (New) |
| Our decision | **MISMATCH_PAUSE** (up to 4h hold) |
| Asked | Tommy via phone (•••) •••-4417 → No, it's not mine |
| Friction added | 10 min |
| Signals | contact.phone_on_file_days, payment_rail, profile_change_recent, recipient_age_days, recipient_status, stated_recipient |
| What actually happened | Completed after Confirmed Intended (Sound intervened) |

What the check says:
- You said this $8,500.00 is for Tommy, but this account isn't one we've verified as Tommy's.
- We'll ask Tommy on the phone number they've had on file for 240 days: is this their account? They can only answer yes or no; you make the final decision.

Tommy's screen shows the amount, the bank, and the masked account, and two buttons: "Yes, it's my account" or "No, it's not mine". Tommy can't approve or cancel. Tommy answers "No, it's not mine." Linda still decides. If Linda cancels, the wire never leaves. If Linda chooses "Send anyway", that's logged, the wire goes, and a recall request opens at once.

Time to intervention: the key's first intervention came 14.0 min after the incident started. Ours is at initiation, 11.0 min after. In the data, Linda overrode a generic hold and lost $8,500. At a 80% cancel rate after "not mine", the replay expects $6,800.00 of this wire to be stopped.

## 2. M1037, P1037-002: $1,188.37 P2P to a family member's new account
| | |
|---|---|
| Payment | P1037-002 · P2P · $1,188.37 · Mobile · 10/6/2026 9:35 |
| Recipient | R1037-09 (New) |
| Our decision | **MISMATCH_PAUSE** (before submit) |
| Asked | Uma via phone (•••) •••-5948 → Yes, it's my account |
| Friction added | 10 min |
| Signals | contact.phone_on_file_days, payment_rail, profile_change_recent, recipient_age_days, recipient_status, stated_recipient |
| What actually happened | Completed after Confirmed Intended (Sound intervened) |

What the check says:
- You said this $1,188.37 is for Uma, but this account isn't one we've verified as Uma's.
- We'll ask Uma on the phone number they've had on file for 479 days: is this their account? They can only answer yes or no; you make the final decision.

The family member answers "Yes, it's my account" and the payment is submitted. Friction added: 10 min, the time for one contact answer. This is a legitimate look-alike, and it goes through within minutes.

## 3. A miss
| | |
|---|---|
| Payment | P1102-005 · Wire · $5,000.00 · Branch · 10/19/2026 13:50 |
| Recipient | R1102-11 (New) |
| Our decision | **NEW_PAYEE_CONFIRM** (up to 4h hold) |
| Asked | nobody → Confirmed |
| Friction added | 1 min |
| Signals | amount_vs_member_baseline, days_since_last_same_rail, payment_rail, recipient_age_days, recipient_status, stated_recipient |
| What actually happened | Completed (no intervention) |

What the check says:
- This $5,000.00 goes to a new payee we haven't verified yet (added 0 days ago).
- Confirm you know this person or business. Sound will never ask you to move money.

Why it's a miss: the member is the one being deceived and taps "confirm" for a payee they believe in. The check paused the payment, but nothing independent contradicted the member's story, so the replay credits no stop. A confirmation screen can't beat a scam the member believes. These journeys need pattern-aware human outreach (the Starter Kit's suggestion), which this check doesn't model.

Scam payments that passed with no pause at all: 0.

## 4. A false positive
| | |
|---|---|
| Payment | P1104-006 · Wire · $76,385.98 · Branch · 10/14/2026 12:31 |
| Recipient | R1104-09 (New) |
| Our decision | **EMPLOYEE_REVIEW_HOLD** (up to 4h hold) |
| Asked | nobody → Employee conversation |
| Friction added | 60 min |
| Signals | amount_vs_member_baseline, days_since_last_same_rail, payment_rail, recipient_age_days, recipient_status, stated_recipient |
| What actually happened | Completed after Confirmed Intended (Sound intervened) |

What the check says:
- This $76,385.98 goes to a new payee we haven't verified yet (added 2 days ago).
- It's far above your usual payments (35.44x).
- It's your first wire in 684 days.
- A Sound employee will review it with you; we can hold it up to 4h hold.
- You make the final decision.

Why it's a false positive: this is a legitimate member. The check adds 60 min of employee review to a real payment. That cost is the price of escalating a first wire in years or an unusually large one. The pilot tracks it as look-alike friction minutes.
