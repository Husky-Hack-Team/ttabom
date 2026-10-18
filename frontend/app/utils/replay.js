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

const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })
const dt = new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeStyle: 'short' })
const tm = new Intl.DateTimeFormat('en-US', { timeStyle: 'short' })
export const formatUsd = (v) => usd.format(Number(v || 0))
export const formatDate = (v) => (v ? dt.format(new Date(v)) : '')
export const formatTime = (v) => (v ? tm.format(new Date(v)) : '')

export function useApiBase() {
  return useRuntimeConfig().public.apiBase.replace(/\/+$/, '')
}

export function errorText(err, fallback) {
  return err?.data?.detail || fallback
}
