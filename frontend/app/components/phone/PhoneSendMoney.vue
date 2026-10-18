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
  // /prototype: the selected recipient (Tommy, Margaret or Daniel). Defaults to the walkthrough's Tommy.
  person: { type: Object, default: null },
  // Standalone adds in-phone helper chips and end-of-story buttons.
  standalone: { type: Boolean, default: false }
})
const emit = defineEmits(['go', 'pick', 'update:screen', 'restart'])

const { scam } = demo
const p = scam.payment
const contact = computed(() => props.person ?? scam.contact)
const who = computed(() => contact.value.firstName ?? contact.value.name)
const poss = computed(() => contact.value.possessive ?? 'his')
const relationship = computed(() => contact.value.relationship ? capitalize(contact.value.relationship) : '')
// Demo-fill options: the person's real account, and a different one (for Tommy, the caller's).
const savedAccount = computed(() => contact.value.verified_accounts[0])
const otherAccount = computed(() => (props.standalone && contact.value.differentAccount) || p.recipient)

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
      status.value = matchAccount({ routing: routing.value, account: account.value }, contact.value)
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

// A different recipient starts a fresh form.
watch(() => contact.value.name, () => {
  routing.value = ''
  account.value = ''
  sent.value = false
})

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
  // Tell the app where the money would go (for the "Sent at your request" ending).
  const typedOther = digitsOnly(routing.value) === otherAccount.value.routing_number && digitsOnly(account.value) === otherAccount.value.account_number
  emit('go', 2, typedOther
    ? { bank: otherAccount.value.bank, account_masked: otherAccount.value.account_masked }
    : { account_masked: `••••${digitsOnly(account.value).slice(-4)}` })
}

// Standalone (/prototype) on small screens: bring the check's result into view.
const statusEl = ref(null)
watch(status, (v) => {
  if (!props.standalone || (v !== 'verified' && v !== 'not_verified')) return
  setTimeout(() => statusEl.value?.scrollIntoView({ block: 'center', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' }), 250)
})

const mismatch = computed(() => status.value === 'not_verified')
const fieldClass = computed(() => (mismatch.value ? '!border-alert pr-12' : ''))
const selectedKind = computed(() => {
  if (!ready.value) return null
  if (routing.value === savedAccount.value.routing_number && account.value === savedAccount.value.account_number) return 'saved'
  if (routing.value === otherAccount.value.routing_number && account.value === otherAccount.value.account_number) return 'caller'
  return 'custom'
})
</script>

<template>
  <Transition name="fade-slide" mode="out-in">
    <div v-if="sent" key="sent" class="flex flex-1 flex-col items-center justify-center text-center">
      <CircleCheck :size="64" class="text-ok" aria-hidden="true" />
      <p class="mt-4 text-2xl font-bold text-navy" data-screen-title>Sent to {{ who }}</p>
      <p class="mt-2 text-lg text-muted">{{ formatUsd(p.amount) }} is on its way to an account verified as {{ who }}’s. No extra steps.</p>
      <button type="button" class="link mt-6" @click="sent = false">Back to the form</button>
      <StoryEndActions v-if="standalone" @restart="emit('restart')" />
    </div>

    <form v-else key="form" class="flex flex-1 flex-col" novalidate @submit.prevent="review">
      <h3 class="mt-2 text-[26px]">Send money</h3>

      <div class="mt-4 flex items-center gap-3 rounded-2xl border-2 border-line p-3">
        <PersonAvatar :name="contact.name" :size="44" />
        <span class="text-lg" :class="standalone ? 'min-w-0 flex-1' : ''">
          <span class="text-muted">To:</span> <strong class="text-navy">{{ contact.name }}</strong> · {{ relationship }}
        </span>
        <!-- /prototype: choose who to pay. The To card shows only name and relationship. -->
        <button v-if="standalone" type="button" class="link shrink-0 text-base" aria-haspopup="dialog" @click="emit('pick')">
          Change<span class="sr-only"> recipient</span>
        </button>
      </div>

      <label for="amount" class="mt-4 text-base font-semibold text-ink">Amount</label>
      <input id="amount" class="field mt-1.5 text-xl font-semibold" :value="formatUsd(p.amount)" readonly>

      <fieldset
        class="mt-4 rounded-2xl border-2 p-3"
        :class="mismatch ? 'border-alert' : 'border-line'"
        aria-describedby="account-status"
      >
        <legend class="px-1 text-base font-semibold text-ink">Bank details</legend>

        <div class="flex items-center justify-between gap-2">
          <label for="routing" class="text-base font-semibold text-ink">Routing number</label>
          <span class="flex items-center gap-1 rounded-full bg-page px-2 py-0.5 text-xs text-muted">
            <Pencil :size="12" aria-hidden="true" />Type manually
          </span>
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
          >
          <TriangleAlert v-if="mismatch" :size="22" class="absolute right-4 top-1/2 -translate-y-1/2 text-alert" aria-hidden="true" />
        </div>

        <div class="mt-3 flex items-center justify-between gap-2">
          <label for="account" class="text-base font-semibold text-ink">Account number</label>
          <span class="flex items-center gap-1 rounded-full bg-page px-2 py-0.5 text-xs text-muted">
            <Pencil :size="12" aria-hidden="true" />Type manually
          </span>
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
          >
          <TriangleAlert v-if="mismatch" :size="22" class="absolute right-4 top-1/2 -translate-y-1/2 text-alert" aria-hidden="true" />
        </div>

        <p class="mt-3 text-sm text-muted">Or demo-fill both fields:</p>
        <div class="mt-2 grid gap-2" role="group" aria-label="Choose demo account details">
          <button
            type="button"
            class="demo-account-option"
            :class="selectedKind === 'saved' ? 'is-selected is-verified' : ''"
            :aria-pressed="selectedKind === 'saved'"
            @click="fill(savedAccount)"
          >
            <PersonAvatar :name="contact.name" :size="36" />
            <span class="min-w-0 flex-1 text-left">
              <strong class="block text-navy">{{ standalone ? `Try ${who}’s real account` : `${who}’s saved account` }}</strong>
              <span class="block truncate text-sm text-muted">{{ standalone ? savedAccount.account_masked : `${savedAccount.bank} · ${savedAccount.account_masked}` }}</span>
            </span>
            <CircleCheck v-if="selectedKind === 'saved'" :size="20" class="shrink-0 text-ok" aria-hidden="true" />
          </button>
          <button
            type="button"
            class="demo-account-option"
            :class="selectedKind === 'caller' ? 'is-selected is-mismatch' : ''"
            :aria-pressed="selectedKind === 'caller'"
            @click="fill(otherAccount)"
          >
            <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-alert-soft text-alert" aria-hidden="true">
              <TriangleAlert :size="20" />
            </span>
            <span class="min-w-0 flex-1 text-left">
              <strong class="block text-navy">{{ standalone ? otherAccount.label : 'Number the caller gave' }}</strong>
              <span class="block truncate text-sm text-muted">{{ standalone ? otherAccount.account_masked : `${otherAccount.bank} · ${otherAccount.account_masked}` }}</span>
            </span>
            <CircleCheck v-if="selectedKind === 'caller'" :size="20" class="shrink-0 text-alert" aria-hidden="true" />
          </button>
        </div>
      </fieldset>

      <div id="account-status" ref="statusEl" class="mt-4" aria-live="polite">
        <Transition name="fade-slide" mode="out-in">
          <div v-if="status === 'idle'" key="idle" class="flex items-start gap-3 rounded-2xl bg-page p-4 text-base">
            <ShieldCheck :size="22" class="mt-0.5 shrink-0 text-accent" aria-hidden="true" />
            <span>We’ll check this account belongs to {{ who }}.</span>
          </div>
          <div v-else-if="status === 'checking'" key="checking" class="flex items-center gap-3 rounded-2xl bg-page p-4 text-base">
            <LoaderCircle :size="22" class="shrink-0 animate-spin text-accent" aria-hidden="true" />
            <span>Checking…</span>
          </div>
          <div v-else-if="status === 'verified'" key="ok" class="flex items-start gap-3 rounded-2xl border-2 border-ok bg-ok-soft p-4 text-base">
            <CircleCheck :size="22" class="mt-0.5 shrink-0 text-ok" aria-hidden="true" />
            <span><strong class="text-ok">Account verified as {{ who }}’s.</strong> The payment can go straight through.</span>
          </div>
          <div v-else key="bad" class="rounded-2xl border-2 border-alert bg-alert-soft p-4 text-base">
            <p class="flex items-start gap-3">
              <TriangleAlert :size="22" class="mt-0.5 shrink-0 text-alert" aria-hidden="true" />
              <span>
                <strong class="text-alert">This account isn’t one of {{ who }}’s verified accounts.</strong>
                The numbers you entered don’t match any account {{ who }} has verified.
              </span>
            </p>
            <p class="mt-2 pl-[34px]">If you continue, we’ll pause it for up to {{ scam.hold_hours }} hours and ask {{ who }} on {{ poss }} saved phone.</p>
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
