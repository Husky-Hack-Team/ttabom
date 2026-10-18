<script setup>
// Step 3 phone: Linda's screens and Tommy's "Is this your account?" screen.
// Shared by the walkthrough (StepTwoViews) and the standalone /prototype app.
// `view` and `answer` are owned by the parent (the walkthrough's toggle and
// employee card read them); `screen` is optional and only bound by /prototype.
import { CircleCheck, Hourglass, Info, ShieldAlert, Smartphone, TriangleAlert } from 'lucide-vue-next'
import demo from '~/data/demo.json'
import { formatUsd } from '~/utils/format'
import StoryEndActions from '~/components/phone/StoryEndActions.vue'

const props = defineProps({
  view: { type: String, default: 'linda' }, // linda | tommy
  answer: { type: String, default: null }, // null | yes | no
  screen: { type: String, default: undefined }, // main | confirm-send | sent | cancelled
  standalone: { type: Boolean, default: false }
})
const emit = defineEmits(['go', 'update:view', 'update:answer', 'update:screen', 'other-story', 'home'])

const { scam } = demo
const p = scam.payment
const contact = scam.contact

const lindaScreen = ref(props.screen ?? 'main')
watch(() => props.screen, (v) => { if (v !== undefined) lindaScreen.value = v })
watch(lindaScreen, (v) => emit('update:screen', v))

function answerAs(a) {
  emit('update:answer', a)
  lindaScreen.value = 'main'
  emit('update:view', 'linda')
}
function reset() {
  emit('update:answer', null)
  lindaScreen.value = 'main'
}
</script>

<template>
  <Transition name="fade-slide" mode="out-in">
    <!-- Tommy -->
    <div v-if="view === 'tommy'" key="tommy" class="flex flex-1 flex-col">
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
    <div v-else-if="lindaScreen === 'sent' || lindaScreen === 'cancelled'" key="end" class="flex flex-1 flex-col items-center justify-center text-center">
      <CircleCheck :size="60" class="text-ok" aria-hidden="true" />
      <p class="mt-4 text-2xl font-bold text-navy" data-screen-title>{{ lindaScreen === 'sent' ? 'Sent at your request' : 'Payment cancelled' }}</p>
      <p class="mt-2 text-lg text-muted">
        {{ lindaScreen === 'sent' ? 'Your choice is logged. If you change your mind, report it within the hour.' : 'Nothing was sent.' }}
      </p>
      <button v-if="lindaScreen === 'sent'" type="button" class="btn btn-phone btn-primary mt-6 text-lg" @click="emit('go', 5)">Report fraud</button>
      <button v-if="!standalone" type="button" class="link mt-4" @click="reset">Start over</button>
      <StoryEndActions v-else @other="emit('other-story')" @home="emit('home')" />
    </div>
    <div v-else key="linda" class="flex flex-1 flex-col">
      <div class="mt-6 flex h-16 w-16 items-center justify-center rounded-full" :class="answer === 'yes' ? 'bg-ok-soft' : 'bg-alert-soft'">
        <CircleCheck v-if="answer === 'yes'" :size="34" class="text-ok" aria-hidden="true" />
        <ShieldAlert v-else :size="34" class="text-alert" aria-hidden="true" />
      </div>
      <template v-if="answer === 'no'">
        <h3 class="mt-4 text-[26px]">{{ contact.name }} says this isn’t his account.</h3>
        <p class="mt-3 text-lg"><strong>This may be fraud.</strong> Your {{ formatUsd(p.amount) }} is still paused. Nothing has been sent.</p>
      </template>
      <template v-else-if="answer === 'yes'">
        <h3 class="mt-4 text-[26px]">{{ contact.name }} says this is his account.</h3>
        <p class="mt-3 text-lg">You can send it now. Your {{ formatUsd(p.amount) }} is ready to go.</p>
      </template>
      <template v-else>
        <h3 class="mt-4 text-[26px]">This account isn’t {{ contact.name }}’s.</h3>
        <p class="mt-3 text-lg">Your {{ formatUsd(p.amount) }} is paused. <strong>Nothing has been sent.</strong></p>
        <p class="mt-4 flex items-start gap-3 rounded-2xl bg-page p-4 text-base">
          <Hourglass :size="20" class="mt-0.5 shrink-0 text-accent" aria-hidden="true" />Waiting for {{ contact.name }}’s answer. Switch to {{ contact.name }}’s phone to answer.
        </p>
        <!-- Standalone only: the walkthrough has a Linda | Tommy toggle above the phone. -->
        <button v-if="standalone" type="button" class="proto-chip mt-4 self-start" @click="emit('update:view', 'tommy')">
          <Smartphone :size="18" aria-hidden="true" />Open {{ contact.name }}’s phone
        </button>
      </template>
      <div class="phone-actions mt-auto space-y-3 pt-5">
        <template v-if="answer === 'yes'">
          <button type="button" class="btn btn-phone btn-primary text-lg" @click="lindaScreen = 'sent'">Send {{ formatUsd(p.amount) }}</button>
          <button type="button" class="btn btn-phone btn-secondary text-lg" @click="lindaScreen = 'cancelled'">Cancel payment</button>
        </template>
        <template v-else>
          <button type="button" class="btn btn-phone btn-primary text-lg" @click="lindaScreen = 'cancelled'">Cancel payment</button>
          <button type="button" class="btn btn-phone btn-secondary text-lg" @click="emit('go', 5)">Report fraud</button>
          <button v-if="answer === 'no'" type="button" class="link block w-full py-2 text-center" @click="lindaScreen = 'confirm-send'">Send anyway</button>
        </template>
      </div>
    </div>
  </Transition>
</template>
