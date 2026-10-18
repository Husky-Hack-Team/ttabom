// Shared labels for the replay and case screens. Every status is spelled out in
// text (and a symbol), so nothing depends on color alone.
export const DISCLAIMER = 'Synthetic data, about 41% scam victims by design. Not a measure of real-world performance.'

export const DECISIONS = {
  PASS: { symbol: '✓', label: 'Passed, no pause' },
  NEW_PAYEE_CONFIRM: { symbol: '●', label: 'One-tap confirm' },
  MISMATCH_PAUSE: { symbol: '⏸', label: 'Paused: contact asked' },
  STEP_UP_PRE_CHANGE_CONTACT: { symbol: '⏸', label: 'Paused: confirm on pre-change contact' },
  EMPLOYEE_REVIEW_HOLD: { symbol: '⏸', label: 'Held for employee review' },
  EMPLOYEE_OUTREACH: { symbol: '⏸', label: 'Paused: employee outreach' },
  BRANCH_EMPLOYEE_PROMPT: { symbol: '⏸', label: 'Teller asks first' }
}

// Starter Kit persona names (fictional).
export const ANCHORS = { M1001: 'Linda', M1002: 'Michael', M1003: 'Sarah', M1004: 'James' }

export function errorText(err, fallback) {
  return err?.data?.detail || fallback
}
