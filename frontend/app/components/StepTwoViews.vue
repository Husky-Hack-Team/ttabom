<script setup>
import { CircleCheck, Hourglass, Info, ShieldAlert, TriangleAlert } from 'lucide-vue-next'
import demo from '~/data/demo.json'
import { formatUsd } from '~/utils/format'

const emit = defineEmits(['go'])
const { scam } = demo
const p = scam.payment
const contact = scam.contact

const view = ref('linda') // linda | tommy
const answer = ref(null) // null | yes | no
const lindaScreen = ref('main') // main | confirm-send | sent | cancelled

function answerAs(a) {
  answer.value = a
  lindaScreen.value = 'main'
  view.value = 'linda'
}
function reset() {
  answer.value = null
  lindaScreen.value = 'main'
}
</script>

<template>
  <StepLayout
    :number="3"
    wide
    title="Two views: the member and the employee"
    :data="['contacts_overlay', 'recipients_overlay', 'recipient_numbers', 'payment_rail', 'days_since_last_same_rail']"
    next="Legit path"
    @next="emit('go', 4)"
  >
    <template #explain>
      <p>
        {{ contact.name }} sees only the amount, the bank and the last 4 digits, and answers one question: is this your account? The answer goes
        to {{ scam.member_name }}. {{ contact.name }} can’t approve or cancel anything.
      </p>
      <p>
        At the same time a Sound employee gets a case with the hold timer, the mismatch, and a calm, non-judgmental way to open the conversation.
      </p>
      <p class="text-base text-muted">Switch phones below, tap {{ contact.name }}’s answer, and watch both screens update.</p>
    </template>

    <div class="w-full max-w-[390px]">
      <div class="mb-4 flex justify-center">
        <div class="inline-flex rounded-full border-2 border-line bg-white p-1" role="group" aria-label="Whose phone">
          <button
            v-for="v in [{ id: 'linda', label: scam.member_name }, { id: 'tommy', label: contact.name }]"
            :key="v.id"
            type="button"
            class="min-h-[44px] rounded-full px-6 text-lg font-semibold"
            :class="view === v.id ? 'bg-navy text-white' : 'text-accent'"
            :aria-pressed="view === v.id ? 'true' : 'false'"
            @click="view = v.id"
          >
            {{ v.label }}
          </button>
        </div>
      </div>

      <PhoneFrame :label="view === 'tommy' ? `${contact.name}'s phone` : `${scam.member_name}'s phone`" :time="p.time_label.replace(/ [AP]M/, '')">
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
            <div class="mt-auto space-y-3 pt-5">
              <button type="button" class="btn btn-phone btn-secondary text-lg" @click="answerAs('yes')">Yes, it’s my account</button>
              <button type="button" class="btn btn-phone btn-primary text-lg" @click="answerAs('no')">No, it’s not mine</button>
            </div>
          </div>

          <!-- Linda -->
          <div v-else-if="lindaScreen === 'confirm-send'" key="confirm" class="flex flex-1 flex-col">
            <TriangleAlert :size="40" class="mt-6 text-alert" aria-hidden="true" />
            <h3 class="mt-4 text-[26px]">You can still send this.</h3>
            <p class="mt-3 text-lg">Money sent by wire is hard to get back.</p>
            <div class="mt-auto space-y-3 pt-5">
              <button type="button" class="btn btn-phone btn-primary text-lg" @click="lindaScreen = 'main'">Go back</button>
              <button type="button" class="btn btn-phone btn-secondary text-lg" @click="lindaScreen = 'sent'">Send anyway</button>
            </div>
          </div>
          <div v-else-if="lindaScreen === 'sent' || lindaScreen === 'cancelled'" key="end" class="flex flex-1 flex-col items-center justify-center text-center">
            <CircleCheck :size="60" class="text-ok" aria-hidden="true" />
            <p class="mt-4 text-2xl font-bold text-navy">{{ lindaScreen === 'sent' ? 'Sent at your request' : 'Payment cancelled' }}</p>
            <p class="mt-2 text-lg text-muted">
              {{ lindaScreen === 'sent' ? 'Your choice is logged. If you change your mind, report it within the hour.' : 'Nothing was sent.' }}
            </p>
            <button v-if="lindaScreen === 'sent'" type="button" class="btn btn-phone btn-primary mt-6 text-lg" @click="emit('go', 5)">Report fraud</button>
            <button type="button" class="link mt-4" @click="reset">Start over</button>
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
            </template>
            <div class="mt-auto space-y-3 pt-5">
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
      </PhoneFrame>
    </div>
    <EmployeeCase :answer="answer" />
  </StepLayout>
</template>
