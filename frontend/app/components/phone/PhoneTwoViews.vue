<script setup>
// Step 3 phone: Linda's screens and Tommy's "Is this your account?" screen.
// Shared by the walkthrough (StepTwoViews) and the standalone /prototype app.
// `view` and `answer` are owned by the parent (the walkthrough's toggle and
// employee card read them); `screen` is optional and only bound by /prototype.
//
// Outcomes are explicit so a report can never land on a "sent" screen:
//   reported            cancelled + fraud report filed, BEFORE any money moved (shown here)
//   report-after-send   event, only from "Sent at your request" in the walkthrough (/ step 5);
//                       /prototype ends the story on that screen instead
import { CircleCheck, Hourglass, Info, Phone, PhoneCall, ShieldAlert, ShieldCheck, Smartphone, TriangleAlert } from 'lucide-vue-next'
import demo from '~/data/demo.json'
import { formatUsd } from '~/utils/format'
import StoryEndActions from '~/components/phone/StoryEndActions.vue'
import ReportedOutcome from '~/components/phone/ReportedOutcome.vue'

const props = defineProps({
  view: { type: String, default: 'linda' }, // linda | tommy
  answer: { type: String, default: null }, // null | yes | no
  screen: { type: String, default: undefined }, // main | confirm-send | sent | cancelled | reported
  // /prototype: who Linda meant to pay (Tommy, Margaret or Daniel) and where the
  // money would actually go. Defaults are the walkthrough's Tommy story.
  person: { type: Object, default: null },
  dest: { type: Object, default: null }, // { bank?, account_masked }
  standalone: { type: Boolean, default: false }
})
const emit = defineEmits(['report-after-send', 'specialist', 'update:view', 'update:answer', 'update:screen', 'restart'])

const { scam } = demo
const p = scam.payment
const contact = computed(() => props.person ?? scam.contact)
const who = computed(() => contact.value.firstName ?? contact.value.name)
const poss = computed(() => contact.value.possessive ?? 'his')
const destination = computed(() => props.dest ?? p.recipient)
const destLabel = computed(() => [destination.value.bank, destination.value.account_masked].filter(Boolean).join(' '))
const realAccount = computed(() => contact.value.verified_accounts[0])
const realAccountLine = computed(() =>
  `${who.value}’s real account (${[realAccount.value.bank, realAccount.value.account_masked].filter(Boolean).join(' ')}) was not affected.`
)
// Deterministic fraud-report reference from the payment id (P1001-003 → SC-001003).
const reportRef = `SC-${p.payment_id.replace(/\D/g, '').slice(-6)}`

const lindaScreen = ref(props.screen ?? 'main')
watch(() => props.screen, (v) => { if (v !== undefined) lindaScreen.value = v })
watch(lindaScreen, (v) => emit('update:screen', v))

function answerAs(a) {
  emit('update:answer', a)
  lindaScreen.value = 'main'
  emit('update:view', 'linda')
}
// Standalone: Tommy gets an automated call from Sound instead of a message.
// ringing → talk (transcript, one question) → replied, then Linda's screen updates.
const tommyStage = ref('ringing')
const tommyReply = ref(null)
let replyTimer
watch(() => props.view, (v) => {
  if (v === 'tommy') { tommyStage.value = 'ringing'; tommyReply.value = null }
})
onBeforeUnmount(() => clearTimeout(replyTimer))
const memberRole = computed(() => contact.value.memberRole ?? (contact.value.relationship === 'grandson' ? 'grandmother' : 'family member'))
// Small screens: keep the newest line of the call transcript in view.
const transcript = ref(null)
const reveal = (el) => el?.scrollIntoView({ block: 'center', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })
watch([tommyStage, tommyReply], () => nextTick(() => reveal(transcript.value?.lastElementChild)))
function tommySays(a) {
  tommyReply.value = a
  tommyStage.value = 'replied'
  clearTimeout(replyTimer)
  replyTimer = setTimeout(() => answerAs(a), 1600)
}

function reset() {
  emit('update:answer', null)
  lindaScreen.value = 'main'
}
</script>

<template>
  <Transition name="fade-slide" mode="out-in">
    <!-- Tommy, standalone: an automated call from Sound Credit Union. -->
    <div v-if="view === 'tommy' && standalone && tommyStage === 'ringing'" key="tommy-ring" class="flex flex-1 flex-col items-center text-center">
      <p class="mt-6 text-sm font-semibold uppercase tracking-wider text-muted">Incoming call</p>
      <span class="relative mt-5 flex h-24 w-24 items-center justify-center rounded-full bg-accent-soft">
        <span class="absolute inset-0 rounded-full bg-accent/25 motion-safe:animate-ping" aria-hidden="true" />
        <PhoneCall :size="40" class="relative text-accent" aria-hidden="true" />
      </span>
      <h3 class="mt-5 text-[26px]">Sound Credit Union</h3>
      <p class="mt-1 text-lg text-muted">Automated assistant</p>
      <p class="mt-5 flex items-start gap-2 rounded-2xl bg-page p-4 text-left text-base">
        <ShieldCheck :size="20" class="mt-0.5 shrink-0 text-ok" aria-hidden="true" />
        <span>Sound’s assistant never asks for codes, passwords or account numbers, and never shares {{ scam.member_name }}’s balance or the payment amount.</span>
      </p>
      <div class="phone-actions mt-auto w-full pt-5">
        <button type="button" class="btn btn-phone btn-primary text-lg" @click="tommyStage = 'talk'">
          <Phone :size="20" aria-hidden="true" />Answer
        </button>
      </div>
    </div>
    <div v-else-if="view === 'tommy' && standalone" key="tommy-talk" class="flex flex-1 flex-col">
      <p class="mt-4 flex items-center gap-2 text-base font-semibold text-accent"><PhoneCall :size="18" aria-hidden="true" />On a call · Sound Credit Union</p>
      <h3 class="mt-1 text-[26px]">Call with Sound’s assistant</h3>
      <ol ref="transcript" class="mt-4 space-y-3 text-base" aria-label="Call transcript" aria-live="polite">
        <li class="max-w-[88%] rounded-2xl rounded-tl-md bg-page p-3">
          <span class="block text-sm font-semibold text-muted">Sound’s assistant (automated)</span>
          Hi {{ who }}, I’m an automated assistant from Sound Credit Union. This is a quick security check. I won’t ask for any codes, passwords or account numbers.
        </li>
        <li class="max-w-[88%] rounded-2xl rounded-tl-md bg-page p-3">
          <span class="block text-sm font-semibold text-muted">Sound’s assistant (automated)</span>
          Did you ask your {{ memberRole }} {{ scam.member_name }} to send you money today?
        </li>
        <li v-if="tommyReply" class="ml-auto max-w-[80%] rounded-2xl rounded-tr-md bg-navy p-3 text-white">
          <span class="block text-sm font-semibold text-white/80">{{ who }}</span>
          {{ tommyReply === 'no' ? 'No, that’s not me.' : 'Yes, I did.' }}
        </li>
        <li v-if="tommyReply" class="max-w-[88%] rounded-2xl rounded-tl-md bg-page p-3">
          <span class="block text-sm font-semibold text-muted">Sound’s assistant (automated)</span>
          Thank you, {{ who }}. I’ll let {{ scam.member_name }} know. Goodbye.
        </li>
      </ol>
      <p class="mt-4 flex items-start gap-2 text-sm text-muted">
        <ShieldCheck :size="16" class="mt-0.5 shrink-0 text-ok" aria-hidden="true" />
        No codes, passwords or account numbers are ever asked. {{ scam.member_name }}’s balance and the amount are never shared. Your answer goes to {{ scam.member_name }}; you can’t approve or cancel her payment.
      </p>
      <div v-if="!tommyReply" class="phone-actions mt-auto space-y-3 pt-5">
        <button type="button" class="btn btn-phone btn-primary text-lg" @click="tommySays('no')">No, that’s not me</button>
        <button type="button" class="btn btn-phone btn-secondary text-lg" @click="tommySays('yes')">Yes, I did</button>
        <button type="button" class="link block w-full py-2 text-center" @click="emit('specialist', 'tommy')">Talk to a person</button>
      </div>
      <p v-else class="mt-auto pt-5 text-center text-base text-muted" role="status">Call ended. Updating {{ scam.member_name }}’s phone…</p>
    </div>
    <!-- Tommy -->
    <div v-else-if="view === 'tommy'" key="tommy" class="flex flex-1 flex-col">
      <p class="mt-4 text-base font-semibold text-accent">Message from Sound</p>
      <h3 class="mt-2 text-[26px]">Is this your account?</h3>
      <p class="mt-2 text-lg">{{ scam.member_name }} is about to send money to an account she says is yours.</p>
      <dl class="mt-5 space-y-3 rounded-2xl bg-page p-4 text-lg">
        <div class="flex justify-between gap-3"><dt class="text-muted">Amount</dt><dd class="font-bold">{{ formatUsd(p.amount) }}</dd></div>
        <div class="flex justify-between gap-3"><dt class="text-muted">Bank</dt><dd class="text-right font-bold">{{ p.recipient.bank }}</dd></div>
        <div class="flex justify-between gap-3"><dt class="text-muted">Account</dt><dd class="font-bold tabular-nums">{{ p.recipient.account_masked }}</dd></div>
      </dl>
      <p class="mt-4 flex items-start gap-2 text-base text-muted">
        <Info :size="18" class="mt-1 shrink-0" aria-hidden="true" />
        Your answer goes to {{ scam.member_name }}. You can’t approve or cancel her payment.
      </p>
      <p v-if="answer" class="mt-3 text-base font-semibold" role="status">You answered: {{ answer === 'no' ? 'No, it’s not mine' : 'Yes, it’s my account' }}</p>
      <div class="phone-actions mt-auto space-y-3 pt-5">
        <button type="button" class="btn btn-phone btn-secondary text-lg" @click="answerAs('yes')">Yes, it’s my account</button>
        <button type="button" class="btn btn-phone btn-primary text-lg" @click="answerAs('no')">No, it’s not mine</button>
      </div>
    </div>

    <!-- Linda -->
    <div v-else-if="lindaScreen === 'confirm-send'" key="confirm" class="flex flex-1 flex-col">
      <TriangleAlert :size="40" class="mt-6 text-alert" aria-hidden="true" />
      <h3 class="mt-4 text-[26px]">You can still send this.</h3>
      <p class="mt-3 text-lg">Money sent by wire is hard to get back.</p>
      <div class="phone-actions mt-auto space-y-3 pt-5">
        <button type="button" class="btn btn-phone btn-primary text-lg" @click="lindaScreen = 'main'">Go back</button>
        <button type="button" class="btn btn-phone btn-secondary text-lg" @click="lindaScreen = 'sent'">Send anyway</button>
      </div>
    </div>
    <!-- Separate outcome screens: "sent" is reachable only from Send anyway / Send after Tommy confirms. -->
    <div v-else-if="lindaScreen === 'sent'" key="sent" class="flex flex-1 flex-col items-center justify-center text-center">
      <CircleCheck :size="60" class="text-ok" aria-hidden="true" />
      <p class="mt-4 text-2xl font-bold text-navy" data-screen-title>Sent at your request</p>
      <!-- /prototype ends the story here; the walkthrough continues to its Report step (step 5). -->
      <template v-if="standalone">
        <p class="mt-2 text-lg text-muted">Your choice is logged. {{ formatUsd(p.amount) }} was sent to {{ destLabel }}.</p>
        <StoryEndActions @restart="emit('restart')" />
      </template>
      <template v-else>
        <p class="mt-2 text-lg text-muted">Your choice is logged. If you change your mind, report it within the hour.</p>
        <button type="button" class="btn btn-phone btn-primary mt-6 text-lg" @click="emit('report-after-send')">Report fraud</button>
        <button type="button" class="link mt-4" @click="reset">Start over</button>
      </template>
    </div>
    <div v-else-if="lindaScreen === 'cancelled'" key="cancelled" class="flex flex-1 flex-col items-center justify-center text-center">
      <CircleCheck :size="60" class="text-ok" aria-hidden="true" />
      <p class="mt-4 text-2xl font-bold text-navy" data-screen-title>Payment cancelled</p>
      <p class="mt-2 text-lg text-muted">Nothing was sent.</p>
      <button v-if="!standalone" type="button" class="link mt-4" @click="reset">Start over</button>
      <StoryEndActions v-else @restart="emit('restart')" />
    </div>
    <ReportedOutcome
      v-else-if="lindaScreen === 'reported'"
      key="reported"
      :amount="p.amount"
      :report-ref="reportRef"
      :member-phone="scam.member_phone_masked"
      :real-account-line="realAccountLine"
      :standalone="standalone"
      @reset="reset"
      @restart="emit('restart')"
    />
    <div v-else key="linda" class="flex flex-1 flex-col">
      <div class="mt-6 flex h-16 w-16 items-center justify-center rounded-full" :class="answer === 'yes' ? 'bg-ok-soft' : 'bg-alert-soft'">
        <CircleCheck v-if="answer === 'yes'" :size="34" class="text-ok" aria-hidden="true" />
        <ShieldAlert v-else :size="34" class="text-alert" aria-hidden="true" />
      </div>
      <template v-if="answer === 'no'">
        <h3 class="mt-4 text-[26px]">{{ who }} says this isn’t {{ poss }} account.</h3>
        <p class="mt-3 text-lg"><strong>This may be fraud.</strong> Your {{ formatUsd(p.amount) }} is still paused. Nothing has been sent.</p>
      </template>
      <template v-else-if="answer === 'yes'">
        <h3 class="mt-4 text-[26px]">{{ who }} says this is {{ poss }} account.</h3>
        <p class="mt-3 text-lg">You can send it now. Your {{ formatUsd(p.amount) }} is ready to go.</p>
      </template>
      <template v-else>
        <h3 class="mt-4 text-[26px]">This account isn’t {{ who }}’s.</h3>
        <p class="mt-3 text-lg">Your {{ formatUsd(p.amount) }} is paused. <strong>Nothing has been sent.</strong></p>
        <p class="mt-4 flex items-start gap-3 rounded-2xl bg-page p-4 text-base">
          <Hourglass :size="20" class="mt-0.5 shrink-0 text-accent" aria-hidden="true" />Waiting for {{ who }}’s answer. Switch to {{ who }}’s phone to answer.
        </p>
        <!-- Standalone only: the walkthrough has a Linda | Tommy toggle above the phone. -->
        <button v-if="standalone" type="button" class="proto-chip mt-4 self-start" @click="emit('update:view', 'tommy')">
          <Smartphone :size="18" aria-hidden="true" />Open {{ who }}’s phone
        </button>
      </template>
      <div class="phone-actions mt-auto space-y-3 pt-5">
        <template v-if="answer === 'yes'">
          <button type="button" class="btn btn-phone btn-primary text-lg" @click="lindaScreen = 'sent'">Send {{ formatUsd(p.amount) }}</button>
          <button type="button" class="btn btn-phone btn-secondary text-lg" @click="lindaScreen = 'cancelled'">Cancel payment</button>
        </template>
        <template v-else>
          <button type="button" class="btn btn-phone btn-primary text-lg" @click="lindaScreen = 'reported'">Cancel payment &amp; report fraud</button>
          <button v-if="answer === 'no'" type="button" class="link block w-full py-2 text-center" @click="lindaScreen = 'confirm-send'">Send anyway</button>
        </template>
      </div>
    </div>
  </Transition>
</template>
