# Verified Contact Payment — design resolutions

`docs/spec-build.md` and `docs/spec-screens.md` were not in the repo when the data-replay module was built.
These resolutions (from the team) are the spec the engine and screens follow; they override anything older.

1. The trusted contact sees the amount, the bank, and the masked account, and answers "Yes, it's my account" or "No, it's not mine." They can't approve or cancel anything.
2. The member makes the final decision. "Send anyway" is allowed, logged, and followed by a recovery path.
3. Sound accounts match by owner. External accounts match only if verified.
4. Questions and codes go only to contact details on file for 7+ days and not recently changed.
5. Micro-deposits come last.
6. Demo names: Tommy (Linda's grandson) and the account ••••8723.

The Starter Kit's Capability Assumptions also apply (see `docs/challenge/`):
wires/ACH/external transfers can be held up to 4 hours; P2P can't be recalled, so any pause happens before submit;
large cash happens in a branch with an employee; for an authorized payment Sound delays and advises but the member decides;
for account takeover Sound can stop the payment.
