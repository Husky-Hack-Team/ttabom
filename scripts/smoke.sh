#!/usr/bin/env bash
# Hit every backend endpoint through <base_url>/api and print status + ms.
# Fails (exit 1) if any response isn't HTTP 200 with a JSON body.
#   scripts/smoke.sh http://localhost:3000
#   scripts/smoke.sh https://ttabom-frontend.vercel.app
set -u
BASE="${1:?usage: scripts/smoke.sh <base_url>}"
BASE="${BASE%/}"
USER_HDR="X-Demo-User: smoke"
EVENT='{"event":{"payment_rail":"Wire","amount":"8500","recipient_id":"R1001-11","recipient_status":"New","recipient_age_days":"0","days_since_last_same_rail":"2411","amount_to_baseline_ratio":"4.77","amount_vs_member_baseline":"Significantly Above Typical","profile_change_recent":"No","password_reset_recent":"No"},"ctx":{"stated":{"type":"new_payee"}}}'

fail=0
check() {
  local method="$1" path="$2" body="${3:-}"
  local out tmp; tmp="$(mktemp)"
  if [ "$method" = POST ]; then
    out="$(curl -sS -m 30 -o "$tmp" -w '%{http_code} %{time_total} %{content_type}' -X POST -H "$USER_HDR" -H 'Content-Type: application/json' --data "$body" "$BASE/api$path" 2>&1)"
  else
    out="$(curl -sS -m 30 -o "$tmp" -w '%{http_code} %{time_total} %{content_type}' -H "$USER_HDR" "$BASE/api$path" 2>&1)"
  fi
  local code secs ctype; read -r code secs ctype <<<"$out"
  local ms; ms="$(awk -v s="${secs:-0}" 'BEGIN{printf "%d", s*1000}')"
  local verdict=OK
  if [ "$code" != 200 ] || [[ "$ctype" != application/json* ]]; then verdict=FAIL; fail=1; fi
  printf '%-4s %-5s %-36s %4s %6s ms  %s\n' "$verdict" "$method" "$path" "$code" "$ms" "$(head -c 70 "$tmp" | tr '\n' ' ')"
  rm -f "$tmp"
}

echo "smoke: $BASE/api"
check GET  /health
check GET  /transactions
check GET  /balance
check GET  /replay/metrics
check GET  "/replay/members?filter=anchor"
check GET  /replay/members/M1001
check GET  "/replay/cases?limit=3"
check POST /vcp/check "$EVENT"
exit $fail
