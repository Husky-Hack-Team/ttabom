<script setup>
// Step 1 phone: "Send money" with the live account check.
// Shared by the walkthrough (StepSignal) and the standalone /prototype app.
import { CircleCheck, LoaderCircle, Pencil, ShieldCheck, TriangleAlert } from 'lucide-vue-next'
import demo from '~/data/demo.json'
import { matchAccount, digitsOnly } from '~/utils/matchAccount'
import { capitalize, formatUsd } from '~/utils/format'
import StoryEndActions from '~/components/phone/StoryEndActions.vue'

const props = defineProps({
  screen: { type: String, default: undefined }, // form | sent (bound only by /prototype)
  // Standalone adds in-phone helper chips and end-of-story buttons.
  standalone: { type: Boolean, default: false }
})
const emit = defineEmits(['go', 'update:screen', 'other-story', 'home'])

const { scam } = demo
const p = scam.payment
const contact = scam.contact
const tommyAccount = contact.verified_accounts[0]
const callerAccount = p.recipient

const routing = ref('')
const account = ref('')
const status = ref('idle') // idle | checking | verified | not_verified
const sent = ref(props.screen === 'sent')
watch(() => props.screen, (v) => { if (v !== undefined) sent.value = v === 'sent' })
watch(sent, (v) => emit('update:screen', v ? 'sent' : 'form'))
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
defineExpose({ fill })

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

// Standalone (/prototype) on small screens: bring the check's result into view.
const statusEl = ref(null)
watch(status, (v) => {
  if (!props.standalone || (v !== 'verified' && v !== 'not_verified')) return
  setTimeout(() => statusEl.value?.scrollIntoView({ block: 'center', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }), 250)
})

const mismatch = computed(() => status.value === 'not_verified')
const fieldClass = computed(() => (mismatch.value ? '!border-alert pr-12' : ''))
</script>

<template>
  <Transition name="fade-slide" mode="out-in">
    <div v-if="sent" key="sent" class="flex flex-1 flex-col items-center justify-center text-center">
      <CircleCheck :size="64" class="text-ok" aria-hidden="true" />
      <p class="mt-4 text-2xl font-bold text-navy" data-screen-title>Sent to {{ contact.name }}</p>
      <p class="mt-2 text-lg text-muted">{{ formatUsd(p.amount) }} is on its way to an account verified as {{ contact.name }}’s. No extra steps.</p>
      <button type="button" class="link mt-6" @click="sent = false">Back to the form</button>
      <StoryEndActions v-if="standalone" @other="emit('other-story')" @home="emit('home')" />
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

      <!-- Standalone only: the walkthrough has these as buttons under the phone. -->
      <div v-if="standalone" class="mt-3" role="group" aria-label="Fill the account for me">
        <p class="text-sm text-muted">Fill it for me:</p>
        <div class="mt-1.5 flex flex-wrap gap-2">
          <button type="button" class="proto-chip" @click="fill(tommyAccount)">{{ contact.name }}’s real account</button>
          <button type="button" class="proto-chip" @click="fill(callerAccount)">Number the caller gave</button>
        </div>
      </div>

      <div id="account-status" ref="statusEl" class="mt-4" aria-live="polite">
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
      <div class="phone-actions sticky bottom-0 mt-auto bg-white pt-4">
        <button type="submit" class="btn btn-phone btn-primary text-lg">Review payment</button>
      </div>
    </form>
  </Transition>
</template>
