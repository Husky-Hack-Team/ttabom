<script setup>
import { CircleCheck, Clock, Landmark, LoaderCircle, Pencil, ShieldCheck, TrendingUp, TriangleAlert, UserRound } from 'lucide-vue-next'
import demo from '~/data/demo.json'
import { matchAccount, digitsOnly } from '~/utils/matchAccount'
import { capitalize, formatInt, formatUsd } from '~/utils/format'

const emit = defineEmits(['go'])

const { scam } = demo
const p = scam.payment
const contact = scam.contact
const tommyAccount = contact.verified_accounts[0]
const callerAccount = p.recipient

const routing = ref('')
const account = ref('')
const status = ref('idle') // idle | checking | verified | not_verified
const sent = ref(false)
const hint = ref('')
let waitTimer
let checkTimer

const ready = computed(() => digitsOnly(routing.value).length === 9 && digitsOnly(account.value).length >= 4)

watch([routing, account], () => {
  clearTimeout(waitTimer)
  clearTimeout(checkTimer)
  hint.value = ''
  sent.value = false
  status.value = 'idle'
  if (!ready.value) return
  // Wait for typing to settle, then check the full numbers.
  waitTimer = setTimeout(() => {
    status.value = 'checking'
    checkTimer = setTimeout(() => {
      status.value = matchAccount({ routing: routing.value, account: account.value }, contact)
    }, 650)
  }, 400)
})
onBeforeUnmount(() => {
  clearTimeout(waitTimer)
  clearTimeout(checkTimer)
})

function fill(acct) {
  routing.value = acct.routing_number
  account.value = acct.account_number
}

function review() {
  if (!ready.value) {
    hint.value = 'Enter the full routing number and account number first.'
    return
  }
  if (status.value === 'checking' || status.value === 'idle') {
    hint.value = 'One moment, we’re still checking the account.'
    return
  }
  if (status.value === 'verified') {
    sent.value = true
    return
  }
  // Not verified: the member can still go ahead, and the story moves to the pause.
  emit('go', 2)
}

const mismatch = computed(() => status.value === 'not_verified')
const fieldClass = computed(() => (mismatch.value ? '!border-alert pr-12' : ''))

const signals = [
  { icon: UserRound, text: `The account doesn’t belong to the person she picked (${contact.name})`, main: true },
  { icon: Clock, text: `New destination, added today at ${p.recipient_added_label}` },
  { icon: Landmark, text: `First ${p.rail.toLowerCase()} in ${p.years_since_last_same_rail}+ years (${formatInt(p.days_since_last_same_rail)} days)` },
  { icon: TrendingUp, text: `Well above her usual amount (${p.amount_vs_member_baseline}, ${p.amount_to_baseline_ratio.toFixed(1)}×)` }
]
</script>

<template>
  <StepLayout
    :number="1"
    title="Signal: the account doesn’t match the person"
    :data="['recipient_status', 'recipient_age_days', 'days_since_last_same_rail', 'amount_vs_member_baseline', 'contacts_overlay', 'recipient_numbers']"
    next="Intervention"
    @next="emit('go', 2)"
  >
    <template #explain>
      <p>
        {{ scam.member_name }} is sending {{ formatUsd(p.amount) }} by {{ p.rail.toLowerCase() }} to her grandson {{ contact.name }}, or so a
        caller told her. As she types the account details, we check them against the accounts {{ contact.name }} has already been paid at.
      </p>
      <p>The check compares the full routing and account numbers. It says only “verified” or “not verified”.</p>
      <ul class="space-y-2 pt-1" aria-label="Signals">
        <li v-for="s in signals" :key="s.text" class="flex items-start gap-3">
          <component :is="s.icon" :size="22" class="mt-0.5 shrink-0" :class="s.main ? 'text-navy' : 'text-muted'" aria-hidden="true" />
          <span :class="s.main ? 'font-semibold text-navy' : ''">
            {{ s.text }}<span v-if="s.main" class="ml-2 rounded-full bg-navy px-2 py-0.5 text-sm font-semibold text-white">Main signal</span>
          </span>
        </li>
      </ul>
      <p class="font-semibold text-navy">
        No single flag stops {{ scam.member_name }}. The mismatch between who she thinks she’s paying and who owns the account does.
      </p>
      <p class="rounded-2xl bg-accent-soft p-4 text-base text-ink">{{ demo.source_note }}</p>
    </template>

    <div class="w-full max-w-[390px]">
      <PhoneFrame :label="`${scam.member_name}'s phone: Send money`" :time="p.time_label.replace(/ [AP]M/, '')">
        <Transition name="fade-slide" mode="out-in">
          <div v-if="sent" key="sent" class="flex flex-1 flex-col items-center justify-center text-center">
            <CircleCheck :size="64" class="text-ok" aria-hidden="true" />
            <p class="mt-4 text-2xl font-bold text-navy">Sent to {{ contact.name }}</p>
            <p class="mt-2 text-lg text-muted">{{ formatUsd(p.amount) }} is on its way to an account verified as {{ contact.name }}’s. No extra steps.</p>
            <button type="button" class="link mt-6" @click="sent = false">Back to the form</button>
          </div>

          <form v-else key="form" class="flex flex-1 flex-col" novalidate @submit.prevent="review">
            <h3 class="mt-2 text-[26px]">Send money</h3>

            <div class="mt-4 flex items-center gap-3 rounded-2xl border-2 border-line p-3">
              <span class="flex h-11 w-11 items-center justify-center rounded-full bg-accent-soft text-lg font-bold text-navy" aria-hidden="true">
                {{ contact.name[0] }}
              </span>
              <span class="text-lg">
                <span class="text-muted">To:</span> <strong class="text-navy">{{ contact.name }}</strong> · {{ capitalize(contact.relationship) }}
              </span>
            </div>

            <label for="amount" class="mt-4 text-base font-semibold text-ink">Amount</label>
            <input id="amount" class="field mt-1.5 text-xl font-semibold" :value="formatUsd(p.amount)" readonly>

            <div class="mt-4 flex items-center justify-between">
              <label for="routing" class="text-base font-semibold text-ink">Routing number</label>
              <span class="flex items-center gap-1 rounded-full bg-page px-2 py-0.5 text-sm text-muted"><Pencil :size="13" aria-hidden="true" />Typed manually</span>
            </div>
            <div class="relative mt-1.5">
              <input
                id="routing"
                v-model="routing"
                class="field"
                :class="fieldClass"
                inputmode="numeric"
                autocomplete="off"
                maxlength="11"
                placeholder="9 digits"
                :aria-invalid="mismatch ? 'true' : 'false'"
                aria-describedby="account-status"
              >
              <TriangleAlert v-if="mismatch" :size="22" class="absolute right-4 top-1/2 -translate-y-1/2 text-alert" aria-hidden="true" />
            </div>

            <div class="mt-4 flex items-center justify-between">
              <label for="account" class="text-base font-semibold text-ink">Account number</label>
              <span class="flex items-center gap-1 rounded-full bg-page px-2 py-0.5 text-sm text-muted"><Pencil :size="13" aria-hidden="true" />Typed manually</span>
            </div>
            <div class="relative mt-1.5">
              <input
                id="account"
                v-model="account"
                class="field"
                :class="fieldClass"
                inputmode="numeric"
                autocomplete="off"
                maxlength="17"
                placeholder="Account number"
                :aria-invalid="mismatch ? 'true' : 'false'"
                aria-describedby="account-status"
              >
              <TriangleAlert v-if="mismatch" :size="22" class="absolute right-4 top-1/2 -translate-y-1/2 text-alert" aria-hidden="true" />
            </div>

            <div id="account-status" class="mt-4" aria-live="polite">
              <Transition name="fade-slide" mode="out-in">
                <div v-if="status === 'idle'" key="idle" class="flex items-start gap-3 rounded-2xl bg-page p-4 text-base">
                  <ShieldCheck :size="22" class="mt-0.5 shrink-0 text-accent" aria-hidden="true" />
                  <span>We’ll check this account belongs to {{ contact.name }}.</span>
                </div>
                <div v-else-if="status === 'checking'" key="checking" class="flex items-center gap-3 rounded-2xl bg-page p-4 text-base">
                  <LoaderCircle :size="22" class="shrink-0 animate-spin text-accent" aria-hidden="true" />
                  <span>Checking…</span>
                </div>
                <div v-else-if="status === 'verified'" key="ok" class="flex items-start gap-3 rounded-2xl border-2 border-ok bg-ok-soft p-4 text-base">
                  <CircleCheck :size="22" class="mt-0.5 shrink-0 text-ok" aria-hidden="true" />
                  <span><strong class="text-ok">Account verified as {{ contact.name }}’s.</strong> The payment can go straight through.</span>
                </div>
                <div v-else key="bad" class="rounded-2xl border-2 border-alert bg-alert-soft p-4 text-base">
                  <p class="flex items-start gap-3">
                    <TriangleAlert :size="22" class="mt-0.5 shrink-0 text-alert" aria-hidden="true" />
                    <span>
                      <strong class="text-alert">This account isn’t one of {{ contact.name }}’s verified accounts.</strong>
                      The numbers you typed don’t match any account {{ contact.name }} has verified.
                    </span>
                  </p>
                  <p class="mt-2 pl-[34px]">If you continue, we’ll pause it for up to {{ scam.hold_hours }} hours and ask {{ contact.name }} on his saved phone.</p>
                </div>
              </Transition>
            </div>

            <p v-if="hint" class="mt-3 text-base text-muted" role="status">{{ hint }}</p>
            <div class="sticky bottom-0 mt-auto bg-white pt-4">
              <button type="submit" class="btn btn-phone btn-primary text-lg">Review payment</button>
            </div>
          </form>
        </Transition>
      </PhoneFrame>

      <div class="mt-6">
        <p class="text-center text-base text-muted">Try it without typing:</p>
        <div class="mt-2 flex flex-col gap-3">
          <button type="button" class="btn btn-secondary w-full text-base" @click="fill(tommyAccount)">Try {{ contact.name }}’s real account</button>
          <button type="button" class="btn btn-secondary w-full text-base" @click="fill(callerAccount)">Try the number the caller gave</button>
        </div>
        <p class="mt-3 text-center text-base text-muted">
          Or type your own. {{ contact.name }}’s real account: {{ tommyAccount.bank }} {{ tommyAccount.account_masked }}.
        </p>
      </div>
    </div>
  </StepLayout>
</template>
