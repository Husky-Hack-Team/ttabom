<script setup>
// Step 1 phone: "Send money" with the live account check.
// Shared by the walkthrough (StepSignal) and the standalone /prototype app.
import { CircleCheck, LoaderCircle, ShieldCheck, TriangleAlert } from 'lucide-vue-next'
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
    hint.value = 'Choose one of the demo accounts first.'
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
const selectedKind = computed(() => {
  if (!ready.value) return null
  return routing.value === tommyAccount.routing_number && account.value === tommyAccount.account_number ? 'saved' : 'caller'
})
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
        <PersonAvatar :name="contact.name" :size="44" />
        <span class="text-lg">
          <span class="text-muted">To:</span> <strong class="text-navy">{{ contact.name }}</strong> · {{ capitalize(contact.relationship) }}
        </span>
      </div>

      <label for="amount" class="mt-4 text-base font-semibold text-ink">Amount</label>
      <input id="amount" class="field mt-1.5 text-xl font-semibold" :value="formatUsd(p.amount)" readonly>

      <fieldset
        class="mt-4 rounded-2xl border-2 p-3"
        :class="mismatch ? 'border-alert' : 'border-line'"
        aria-describedby="account-status"
      >
        <legend class="px-1 text-base font-semibold text-ink">Routing + account number</legend>
        <p class="text-sm text-muted">Demo-fill both fields together:</p>
        <div class="mt-2 grid gap-2" role="group" aria-label="Choose demo account details">
          <button
            type="button"
            class="demo-account-option"
            :class="selectedKind === 'saved' ? 'is-selected is-verified' : ''"
            :aria-pressed="selectedKind === 'saved'"
            @click="fill(tommyAccount)"
          >
            <PersonAvatar :name="contact.name" :size="36" />
            <span class="min-w-0 flex-1 text-left">
              <strong class="block text-navy">{{ contact.name }}’s saved account</strong>
              <span class="block truncate text-sm text-muted">{{ tommyAccount.bank }} · {{ tommyAccount.account_masked }}</span>
            </span>
            <CircleCheck v-if="selectedKind === 'saved'" :size="20" class="shrink-0 text-ok" aria-hidden="true" />
          </button>
          <button
            type="button"
            class="demo-account-option"
            :class="selectedKind === 'caller' ? 'is-selected is-mismatch' : ''"
            :aria-pressed="selectedKind === 'caller'"
            @click="fill(callerAccount)"
          >
            <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-alert-soft text-alert" aria-hidden="true">
              <TriangleAlert :size="20" />
            </span>
            <span class="min-w-0 flex-1 text-left">
              <strong class="block text-navy">Number the caller gave</strong>
              <span class="block truncate text-sm text-muted">{{ callerAccount.bank }} · {{ callerAccount.account_masked }}</span>
            </span>
            <CircleCheck v-if="selectedKind === 'caller'" :size="20" class="shrink-0 text-alert" aria-hidden="true" />
          </button>
        </div>
      </fieldset>

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
                The selected numbers don’t match any account {{ contact.name }} has verified.
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
