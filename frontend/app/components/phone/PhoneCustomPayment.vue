<script setup>
// /prototype only: Linda pays a custom recipient's account she has never paid before.
// There's no saved account to compare against, so instead of an ownership
// check this runs a deterministic risk check (utils/riskCheck.js) on Review:
//   low     → review → Send → success
//   medium  → review → 10-second caution step → Send or Cancel
//   high    → paused before sending → Cancel & report / specialist / Send anyway
import { CircleCheck, Hourglass, Info, ShieldAlert, ShieldCheck, Sparkles, TriangleAlert, UserRound } from 'lucide-vue-next'
import demo from '~/data/demo.json'
import { formatUsd } from '~/utils/format'
import { KNOW_ANSWERS, riskCheck } from '~/utils/riskCheck'
import { CUSTOM_SAMPLE, TYPICAL_PAYMENT } from '~/data/prototypeRecipients'
import StoryEndActions from '~/components/phone/StoryEndActions.vue'
import ReportedOutcome from '~/components/phone/ReportedOutcome.vue'

const props = defineProps({
  answer: { type: String, default: null }, // answer to "Do you know this person?"
  screen: { type: String, default: 'form' } // form | review | caution | paused | confirm-send | sent | success | cancelled | reported
})
const emit = defineEmits(['update:screen', 'change-answer', 'pick', 'specialist', 'restart'])

const { scam } = demo
const view = ref(props.screen)
watch(() => props.screen, (v) => { if (v) view.value = v })
watch(view, (v) => emit('update:screen', v))

// ----- Form -----
const name = ref('')
const routing = ref('')
const account = ref('')
const amount = ref('')
const touched = reactive({ name: false, routing: false, account: false, amount: false })

const amountNum = computed(() => {
  const n = Number(String(amount.value).replace(/[$,\s]/g, ''))
  return Number.isFinite(n) ? Math.round(n * 100) / 100 : NaN
})
const errors = computed(() => ({
  name: name.value.trim() ? '' : 'Enter the recipient’s name',
  routing: /^\d{9}$/.test(routing.value) ? '' : 'Routing number must be exactly 9 digits',
  account: !account.value
    ? 'Enter the account number'
    : !/^\d+$/.test(account.value)
      ? 'Use numbers only'
      : account.value.length < 4 ? 'Account number is too short' : '',
  amount: amountNum.value > 0 ? '' : 'Enter an amount greater than $0'
}))
const valid = computed(() => Object.values(errors.value).every((e) => !e))
const show = (field) => touched[field] && errors.value[field]

function fillSample() {
  name.value = CUSTOM_SAMPLE.name
  routing.value = CUSTOM_SAMPLE.routing
  account.value = CUSTOM_SAMPLE.account
  amount.value = CUSTOM_SAMPLE.amount
  Object.keys(touched).forEach((k) => { touched[k] = true })
}

const recipientName = computed(() => name.value.trim())
const masked = computed(() => `••••${account.value.slice(-4)}`)
const answerLabel = computed(() => KNOW_ANSWERS.find((a) => a.id === props.answer)?.label ?? 'Not answered')

// ----- Risk check: recomputed from the current answer and amount every time -----
const risk = computed(() => riskCheck({ answer: props.answer, amount: amountNum.value, typical: TYPICAL_PAYMENT }))
const LEVEL = {
  low: { label: 'Low risk', icon: ShieldCheck, cls: 'border-ok text-ok' },
  medium: { label: 'Medium risk', icon: TriangleAlert, cls: 'border-[#9a5b00] text-[#7a4700]' },
  high: { label: 'High risk', icon: ShieldAlert, cls: 'border-alert text-alert' }
}

function review() {
  Object.keys(touched).forEach((k) => { touched[k] = true })
  if (!valid.value) return
  view.value = risk.value.level === 'high' ? 'paused' : 'review'
}

// ----- Medium risk: a 10-second "take a moment" pause before Send -----
const WAIT = 10
const left = ref(WAIT)
let tick
watch(view, (v) => {
  clearInterval(tick)
  if (v !== 'caution') return
  left.value = WAIT
  tick = setInterval(() => {
    left.value -= 1
    if (left.value <= 0) clearInterval(tick)
  }, 1000)
}, { immediate: true })
onBeforeUnmount(() => clearInterval(tick))

const reportRef = computed(() => `SC-${account.value.slice(-6).padStart(6, '0')}`)
</script>

<template>
  <Transition name="fade-slide" mode="out-in">
    <!-- Form -->
    <form v-if="view === 'form'" key="form" class="flex flex-1 flex-col" novalidate @submit.prevent="review">
      <h3 class="mt-2 text-[26px]">Send money</h3>

      <div class="mt-4 flex items-center gap-3 rounded-2xl border-2 border-line p-3">
        <PersonAvatar :name="recipientName || '+'" :size="44" />
        <span class="min-w-0 flex-1 text-lg">
          <span class="text-muted">To:</span> <strong class="text-navy">{{ recipientName || 'Custom recipient' }}</strong> · New recipient
        </span>
        <button type="button" class="link shrink-0 text-base" aria-haspopup="dialog" @click="emit('pick')">
          Change<span class="sr-only"> recipient</span>
        </button>
      </div>
      <p class="mt-2 flex items-center gap-2 text-base text-muted">
        <UserRound :size="18" class="shrink-0" aria-hidden="true" />
        <span class="min-w-0 flex-1">You said: <strong class="text-ink">{{ answerLabel }}</strong></span>
        <button type="button" class="link shrink-0 text-base" aria-haspopup="dialog" @click="emit('change-answer')">
          Change<span class="sr-only"> answer</span>
        </button>
      </p>

      <label for="custom-name" class="mt-4 text-base font-semibold text-ink">Recipient’s name</label>
      <input
        id="custom-name"
        v-model="name"
        class="field mt-1.5"
        :class="show('name') ? '!border-alert' : ''"
        autocomplete="off"
        :aria-invalid="show('name') ? 'true' : 'false'"
        :aria-describedby="show('name') ? 'custom-name-error' : undefined"
        @blur="touched.name = true"
      >
      <p v-if="show('name')" id="custom-name-error" class="mt-1 flex items-center gap-1.5 text-base text-alert"><TriangleAlert :size="16" aria-hidden="true" />{{ errors.name }}</p>

      <label for="custom-routing" class="mt-3 text-base font-semibold text-ink">Routing number</label>
      <input
        id="custom-routing"
        v-model="routing"
        class="field mt-1.5"
        :class="show('routing') ? '!border-alert' : ''"
        inputmode="numeric"
        autocomplete="off"
        maxlength="9"
        placeholder="9 digits"
        :aria-invalid="show('routing') ? 'true' : 'false'"
        :aria-describedby="show('routing') ? 'custom-routing-error' : undefined"
        @blur="touched.routing = true"
      >
      <p v-if="show('routing')" id="custom-routing-error" class="mt-1 flex items-center gap-1.5 text-base text-alert"><TriangleAlert :size="16" aria-hidden="true" />{{ errors.routing }}</p>

      <label for="custom-account" class="mt-3 text-base font-semibold text-ink">Account number</label>
      <input
        id="custom-account"
        v-model="account"
        class="field mt-1.5"
        :class="show('account') ? '!border-alert' : ''"
        inputmode="numeric"
        autocomplete="off"
        maxlength="17"
        :aria-invalid="show('account') ? 'true' : 'false'"
        :aria-describedby="show('account') ? 'custom-account-error' : undefined"
        @blur="touched.account = true"
      >
      <p v-if="show('account')" id="custom-account-error" class="mt-1 flex items-center gap-1.5 text-base text-alert"><TriangleAlert :size="16" aria-hidden="true" />{{ errors.account }}</p>

      <label for="custom-amount" class="mt-3 text-base font-semibold text-ink">Amount</label>
      <input
        id="custom-amount"
        v-model="amount"
        class="field mt-1.5 text-xl font-semibold"
        :class="show('amount') ? '!border-alert' : ''"
        inputmode="decimal"
        autocomplete="off"
        placeholder="$0.00"
        :aria-invalid="show('amount') ? 'true' : 'false'"
        :aria-describedby="show('amount') ? 'custom-amount-error' : 'custom-amount-hint'"
        @blur="touched.amount = true"
      >
      <p v-if="show('amount')" id="custom-amount-error" class="mt-1 flex items-center gap-1.5 text-base text-alert"><TriangleAlert :size="16" aria-hidden="true" />{{ errors.amount }}</p>
      <p v-else id="custom-amount-hint" class="mt-1 text-sm text-muted">Your typical payment is about {{ formatUsd(TYPICAL_PAYMENT) }}.</p>

      <button type="button" class="proto-chip mt-4 self-start" @click="fillSample">
        <Sparkles :size="18" aria-hidden="true" />Fill a sample ({{ CUSTOM_SAMPLE.name }})
      </button>

      <div class="phone-actions sticky bottom-0 mt-auto bg-white pt-4">
        <p v-if="!valid" id="custom-review-hint" class="mb-2 text-center text-sm text-muted">Fill in every field to continue.</p>
        <button type="submit" class="btn btn-phone btn-primary text-lg disabled:opacity-40" :disabled="!valid" :aria-describedby="!valid ? 'custom-review-hint' : undefined">
          Review payment
        </button>
      </div>
    </form>

    <!-- Review (low / medium) -->
    <div v-else-if="view === 'review'" key="review" class="flex flex-1 flex-col">
      <h3 class="mt-2 text-[26px]">Review payment</h3>
      <dl class="mt-4 space-y-2 rounded-2xl bg-page p-4 text-lg">
        <div class="flex justify-between gap-3"><dt class="text-muted">To</dt><dd class="text-right font-bold">{{ recipientName }}</dd></div>
        <div class="flex justify-between gap-3"><dt class="text-muted">Account</dt><dd class="font-bold tabular-nums">{{ masked }}</dd></div>
        <div class="flex justify-between gap-3"><dt class="text-muted">Amount</dt><dd class="font-bold">{{ formatUsd(amountNum) }}</dd></div>
      </dl>
      <section class="mt-4 rounded-2xl border-2 border-line p-4" aria-labelledby="risk-title">
        <h4 id="risk-title" class="flex flex-wrap items-center gap-2 text-base font-semibold text-ink">
          Risk check
          <span class="inline-flex items-center gap-1 rounded-full border-2 px-2.5 py-0.5 text-sm font-bold" :class="LEVEL[risk.level].cls">
            <component :is="LEVEL[risk.level].icon" :size="14" aria-hidden="true" />{{ LEVEL[risk.level].label }}
          </span>
        </h4>
        <ul class="mt-3 space-y-2 text-base" aria-label="Signals used">
          <li v-for="sig in risk.signals" :key="sig.id" class="flex items-start gap-2">
            <TriangleAlert v-if="sig.warn" :size="18" class="mt-0.5 shrink-0 text-alert" aria-hidden="true" />
            <CircleCheck v-else :size="18" class="mt-0.5 shrink-0 text-ok" aria-hidden="true" />
            <span><span class="sr-only">{{ sig.warn ? 'Warning: ' : 'OK: ' }}</span>{{ sig.text }}</span>
          </li>
        </ul>
      </section>
      <p class="mt-4 flex items-start gap-2 text-base">
        <Info :size="18" class="mt-1 shrink-0 text-accent" aria-hidden="true" />New recipient. We can’t verify who owns this account.
      </p>
      <div class="phone-actions mt-auto space-y-3 pt-5">
        <button v-if="risk.level === 'low'" type="button" class="btn btn-phone btn-primary text-lg" @click="view = 'success'">Send {{ formatUsd(amountNum) }}</button>
        <button v-else type="button" class="btn btn-phone btn-primary text-lg" @click="view = 'caution'">Continue</button>
      </div>
    </div>

    <!-- Medium: take a moment -->
    <div v-else-if="view === 'caution'" key="caution" class="flex flex-1 flex-col">
      <div class="mt-6 flex h-16 w-16 items-center justify-center rounded-full bg-accent-soft">
        <Hourglass :size="32" class="text-accent" aria-hidden="true" />
      </div>
      <h3 class="mt-4 text-[26px]">Take a moment before you send</h3>
      <ul class="mt-4 space-y-3 text-base">
        <li class="flex items-start gap-2"><ShieldCheck :size="18" class="mt-0.5 shrink-0 text-ok" aria-hidden="true" />Sound will never ask you to move money to protect it.</li>
        <li class="flex items-start gap-2"><ShieldCheck :size="18" class="mt-0.5 shrink-0 text-ok" aria-hidden="true" />Scammers rush you. Someone you really know will wait while you check.</li>
        <li class="flex items-start gap-2"><ShieldCheck :size="18" class="mt-0.5 shrink-0 text-ok" aria-hidden="true" />If you can, call them on a number you already know before sending.</li>
      </ul>
      <p class="mt-4 rounded-2xl bg-page p-4 text-lg font-semibold text-navy" aria-live="polite">
        {{ left > 0 ? `You can send in ${left} second${left === 1 ? '' : 's'}.` : 'You can send now.' }}
      </p>
      <div class="phone-actions mt-auto space-y-3 pt-5">
        <button type="button" class="btn btn-phone btn-primary text-lg disabled:opacity-40" :disabled="left > 0" @click="view = 'success'">
          {{ left > 0 ? `Send (${left})` : `Send ${formatUsd(amountNum)}` }}
        </button>
        <button type="button" class="btn btn-phone btn-secondary text-lg" @click="view = 'cancelled'">Cancel payment</button>
      </div>
    </div>

    <!-- High: paused before sending -->
    <div v-else-if="view === 'paused'" key="paused" class="flex flex-1 flex-col">
      <div class="mt-6 flex h-16 w-16 items-center justify-center rounded-full bg-alert-soft">
        <ShieldAlert :size="34" class="text-alert" aria-hidden="true" />
      </div>
      <h3 class="mt-4 text-[26px]">Payment paused before sending</h3>
      <p class="mt-3 text-lg">Your {{ formatUsd(amountNum) }} to {{ recipientName }} <strong>hasn’t been sent.</strong></p>
      <section class="mt-4 rounded-2xl border-2 border-alert bg-alert-soft p-4" aria-labelledby="why-title">
        <h4 id="why-title" class="flex flex-wrap items-center gap-2 text-base font-semibold text-ink">
          Why we paused it
          <span class="inline-flex items-center gap-1 rounded-full border-2 border-alert bg-white px-2.5 py-0.5 text-sm font-bold text-alert">
            <ShieldAlert :size="14" aria-hidden="true" />High risk
          </span>
        </h4>
        <ul class="mt-3 space-y-2 text-base" aria-label="Signals used">
          <li v-for="sig in risk.signals" :key="sig.id" class="flex items-start gap-2">
            <TriangleAlert v-if="sig.warn" :size="18" class="mt-0.5 shrink-0 text-alert" aria-hidden="true" />
            <CircleCheck v-else :size="18" class="mt-0.5 shrink-0 text-ok" aria-hidden="true" />
            <span><span class="sr-only">{{ sig.warn ? 'Warning: ' : 'OK: ' }}</span>{{ sig.text }}</span>
          </li>
        </ul>
      </section>
      <div class="phone-actions mt-auto space-y-3 pt-5">
        <button type="button" class="btn btn-phone btn-primary text-lg" @click="view = 'reported'">Cancel payment &amp; report fraud</button>
        <button type="button" class="btn btn-phone btn-secondary text-lg" @click="emit('specialist', amountNum)">Talk to a Sound specialist</button>
        <button type="button" class="link block w-full py-2 text-center" @click="view = 'confirm-send'">Send anyway</button>
      </div>
    </div>

    <div v-else-if="view === 'confirm-send'" key="confirm" class="flex flex-1 flex-col">
      <TriangleAlert :size="40" class="mt-6 text-alert" aria-hidden="true" />
      <h3 class="mt-4 text-[26px]">You can still send this.</h3>
      <p class="mt-3 text-lg">Money sent to a new account is hard to get back.</p>
      <div class="phone-actions mt-auto space-y-3 pt-5">
        <button type="button" class="btn btn-phone btn-primary text-lg" @click="view = 'paused'">Go back</button>
        <button type="button" class="btn btn-phone btn-secondary text-lg" @click="view = 'sent'">Send anyway</button>
      </div>
    </div>

    <!-- Endings: Start over only -->
    <div v-else-if="view === 'sent'" key="sent" class="flex flex-1 flex-col items-center justify-center text-center">
      <CircleCheck :size="60" class="text-ok" aria-hidden="true" />
      <p class="mt-4 text-2xl font-bold text-navy" data-screen-title>Sent at your request</p>
      <p class="mt-2 text-lg text-muted">Your choice is logged. {{ formatUsd(amountNum) }} was sent to {{ recipientName }} {{ masked }}.</p>
      <StoryEndActions @restart="emit('restart')" />
    </div>
    <div v-else-if="view === 'success'" key="success" class="flex flex-1 flex-col items-center justify-center text-center">
      <CircleCheck :size="64" class="text-ok" aria-hidden="true" />
      <p class="mt-4 text-2xl font-bold text-navy" data-screen-title>{{ formatUsd(amountNum) }} sent to {{ recipientName }}</p>
      <p class="mt-2 text-lg text-muted">New recipient · {{ masked }}</p>
      <StoryEndActions @restart="emit('restart')" />
    </div>
    <div v-else-if="view === 'cancelled'" key="cancelled" class="flex flex-1 flex-col items-center justify-center text-center">
      <CircleCheck :size="60" class="text-ok" aria-hidden="true" />
      <p class="mt-4 text-2xl font-bold text-navy" data-screen-title>Payment cancelled</p>
      <p class="mt-2 text-lg text-muted">Nothing was sent.</p>
      <StoryEndActions @restart="emit('restart')" />
    </div>
    <ReportedOutcome
      v-else-if="view === 'reported'"
      key="reported"
      :amount="amountNum"
      :report-ref="reportRef"
      :member-phone="scam.member_phone_masked"
      standalone
      @restart="emit('restart')"
    />
  </Transition>
</template>
