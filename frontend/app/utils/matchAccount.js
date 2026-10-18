// Live account check for the "Send money" screen.
//
// Compares the FULL typed routing and account numbers against the contact's
// verified accounts. It never decides on the last 4 digits alone, and it only
// says "verified" or "not_verified", never whose account it is.
//
// In production this runs on the server: the contact's verified accounts are
// never sent to the browser, and the check is rate-limited per member and
// device so it can't be used to guess someone's account number.

export const digitsOnly = (value) => String(value ?? '').replace(/\D/g, '')

export function matchAccount({ routing, account }, contact) {
  const r = digitsOnly(routing)
  const a = digitsOnly(account)
  if (r.length !== 9 || a.length < 4) return 'not_verified'
  const match = (contact?.verified_accounts ?? []).some(
    (v) => digitsOnly(v.routing_number) === r && digitsOnly(v.account_number) === a
  )
  return match ? 'verified' : 'not_verified'
}
