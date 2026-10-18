# Synthetic overlay (seed 2026)

> Synthetic data, about 41% scam victims by design. Not a measure of real-world performance.

The HuskyHack v2 events don't include the records the Verified Contact Payment check relies on: a member's saved contacts, which bank a recipient account is at, the member's own phone and email history, and what the member says a payment is for. `analysis/overlay.py` invents these deterministically (`random.Random(2026)`). Running it again produces the same files byte for byte.

```sh
analysis/.venv/bin/python analysis/overlay.py
```

## Files

| File | One row per | Columns |
| --- | --- | --- |
| `contacts_overlay.csv` | saved contact | member, contact_id, name, relationship, masked phone, date the phone was added, verified accounts (`;`-separated recipient_ids) |
| `stated_recipient.csv` | New-recipient or cash payment | payment_id, member, recipient, stated_type (`saved_contact` / `new_payee` / `myself`), contact_id |
| `recipients_overlay.csv` | recipient | member, recipient_id, bank (`Sound` or a fictional external bank), masked account, whether the account predates the data window, owning contact |
| `recipient_numbers.csv` | recipient | **synthetic** 9-digit routing number (valid ABA checksum, one per bank) and full account number ending in the overlay's masked last 4. Built by `scripts/build_demo_data.py` (seed 2026) only if missing |
| `member_channels.csv` | member | the member's own masked phone and email, the date each was added, and the masked value each changes to if a Phone Change or Email Change event happens |

## Assumptions

### Contacts
1. Each member has 0–2 saved contacts. The count is drawn from {0, 1, 1, 2}.
2. Every anchor member (M1001–M1004) and every Family Emergency or "Helping a real family member" member has at least one family contact. Their first contact is always family.
3. Each later contact is family with probability 0.6; otherwise friend, neighbor, roommate, or coworker. Relationships are gender-neutral (child, grandchild, sibling, niece or nephew, cousin). The one exception is Tommy.
4. **M1001 Linda → Tommy, grandson, phone (•••) •••-4417, on file since 2026-02-22.** That is 240 days on file on 2026-10-20, the day of the $8,500 wire.
5. Contact phones were added 30–2,000 days before the window starts (2026-08-31). The one exception is a single fixture: **the first non-anchor Family Emergency member (M1012)**. That contact's phone was added 3 days before the member's first scam payment, so the replay exercises the fallback "employee outreach, call a number you already know". This choice uses the Member Key and exists only to make the fallback visible.
6. Being a saved contact is separate from the events file's `trusted_contact_enrolled` flag. The contact asked is the person the member says the money is for, not a formally enrolled trusted contact. Linda has no enrolled trusted contact in the data, but she has Tommy saved.

### Recipient accounts and verification
7. A recipient "predates the window" if, the first time it appears on a Payment Initiated row, it is Existing with `recipient_age_days ≥ 30`. Such accounts are assumed to have been paid successfully before the window.
8. 30% of accounts that predate the window are Sound accounts. All other accounts, and every New recipient, are at a fictional external bank.
9. Each contact's verified accounts are the member's most-paid P2P recipients that predate the window, one per contact, in order. A contact may have no verified account at all.
10. An external account counts as verified for a contact only if it is in that contact's list, is `Existing`, and has `recipient_age_days ≥ 30` on the payment under test. New recipients are never pre-verified. A Sound account matches by owner (`owner_contact_id`), even when it's new (resolution 3).
11. **R1001-11 (Linda's wire destination) is ••••8723 at Cascade Federal Bank.** This is the account Tommy is shown.

### Routing and account numbers
The HuskyHack data has no account or routing numbers. `recipient_numbers.csv` makes them up for the demo page: one synthetic routing number per bank name, and an account number made of 6 random digits followed by the last 4 already shown in `recipients_overlay.csv`. None of them are real; they exist so the demo can check full typed numbers rather than last 4.

### The member's own phone and email
12. Each member's phone and email were added 200–3,000 days before the window.
13. A `Phone Change` or `Email Change` event in the events file switches that channel to `*_masked_after_change`. The engine reads these events from the member's earlier rows only.
14. A takeover step-up never uses a value changed in the last 7 days. It uses the value on file before the change, provided that value had been on file for 7+ days at the time of the change (resolution 4).

### Stated recipient (simulated member input)
15. Only payments to a New recipient, and cash, get a stated recipient. Payments to an Existing recipient pass on the fast path and never ask.
16. The member answers honestly from their own point of view. A scam victim repeats the scammer's story.
    - **Saved contact:** Family Emergency scam payments ("it's for my grandson", including the "bail" cash) and every "Helping a real family member" payment. The contact is the member's first family contact.
    - **Myself:** "Funding a new brokerage account".
    - **New payee or business:** everything else. That covers contractors, landlords (real move), home-closing wires, romance partners, the "federal agent" or "safe account" in government impersonation, account-takeover payments (typed by the attacker), routine new payees, vehicle cash, and non-scam payments by members in scam journeys.
17. The stated type comes from the Member Key, through `analysis/oracle.py`. It stands in for what a person would type on the payment screen. It is never derived from event fields, and the engine never sees the scenario.

## What the overlay does not do

- It never changes the events or the Member Key.
- It never marks a New recipient as verified.
- It never gives the engine a scenario label. The engine reads only `stated_recipient.stated_type` and `contact_id`, plus Sound's records (contacts, accounts, channels).
