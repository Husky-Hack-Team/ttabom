# 90-day pilot: Verified Contact Payment

> Synthetic data, about 41% scam victims by design. Not a measure of real-world performance.
> Every baseline and target below is an **assumption** to replace with Sound's own numbers in week 1. None of them comes from real fraud rates.

## Scope

- **Who:** members who opt in at a branch or in the app and save at least one contact with a phone on file for 7+ days. Branch staff in two pilot branches, plus one contact-center pod.
- **Rails:** wires, ACH, and external transfers (up to a 4-hour hold); P2P (the check runs before submit); cash over the branch prompt threshold. Debit, Bill Pay, and Automatic Payment are out of scope.
- **What changes for the member:** when a payment to a new account is "for" a saved contact, the contact is asked "Is this your account?". The contact sees the amount, the bank, and the masked account, and answers yes or no. The member makes the final decision. "Send anyway" is allowed, logged, and followed by a recovery path.

## Phases

| Days | Phase | Exit criterion |
| --- | --- | --- |
| 1–14 | Shadow mode: the engine logs decisions and nobody is asked | Decision log matches the replay's decision mix within ±10 points |
| 15–45 | Live for staff-assisted payments (branch wires, cash) | Hold timer and case screen used on ≥ 90% of paused payments |
| 46–90 | Live in app for P2P and online transfers | All guardrails below hold for 4 straight weeks |

## Measures

| Measure | Definition | Baseline (assumed) | Target (assumed) | Replay reference |
| --- | --- | --- | --- | --- |
| Contact questions answered ≤ 10 min | answered within 10 min ÷ questions sent | none (new) | ≥ 70% | 10 min is assumed for every contact answer |
| Look-alike friction minutes | minutes added to legitimate payments the check paused, per paused member | ~60 min per held wire today | ≤ 20 min median | 19.4 min per look-alike member; 387 min across 20 members |
| Override rate | "Send anyway" after "No, it's not mine" ÷ "not mine" answers | none (new) | ≤ 25% | 20% assumed (cancel rate 0.8; tested at 0.5 and 1.0) |
| Reports within 1 hour | scam reports filed within 1 h of the payment ÷ all scam reports | ~20% (assumed: most reports take days, as in the data) | ≥ 50% | Recovery path opens at once after "Send anyway" |
| Paused before money moved | confirmed-scam payments the check paused ÷ confirmed-scam payments | per Sound's case data | ≥ 90% | 143 of 143 scam payments paused in the replay |
| Routine members interrupted | routine members with ≥ 1 pause ÷ routine members | none | ≤ 15% | 10 of 50 routine members, 1 min each |
| Contact-question safety | questions sent to a phone on file < 7 days or changed recently | none | **0** (hard rule) | 0 by construction (tested) |

## Guardrails (stop or roll back if any trips)

1. A question or code is ever sent to contact details on file for less than 7 days or recently changed.
2. Median look-alike friction is above 30 minutes for two weeks in a row.
3. Complaints about the contact question are above 2% of questions sent.
4. Any accessibility defect: screen reader, 200% zoom, or color-only status.

## What the replay can't tell us

- Whether victims really cancel after their own contact says "not mine". This is the cancel-rate assumption; the pilot measures it.
- What employee conversations achieve. The replay credits no stops for them, so they need to be measured.
- Romance and investment scams. The member believes the payee, and a one-tap confirm stops nothing (in the replay, $86,589.79 confirmed and sent). That gap needs pattern-aware outreach, which is outside this pilot.
