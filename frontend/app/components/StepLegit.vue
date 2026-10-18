<script setup>
import { CircleCheck, Hourglass, Send, TriangleAlert, Zap } from 'lucide-vue-next'
import demo from '~/data/demo.json'
import { capitalize, formatUsd } from '~/utils/format'

const emit = defineEmits(['go'])
const { lookalike: l } = demo
const p = l.payment
const contact = l.contact

const stage = ref('paused') // paused | answered | sent

// Target timings for the legit path (assumptions, not measurements).
const timeline = [
  { at: '0:00', label: 'Paused, question sent' },
  { at: '~2 min', label: `${contact.name} answers “Yes, it’s my account”` },
  { at: '~3 min', label: 'Sent' }
]
</script>

<template>
  <StepLayout
    :number="4"
    title="Legit path: a quick yes, then it’s sent"
    :data="['Member Key: is_legitimate_lookalike', 'recipient_status', 'payment lifecycle rows', 'contacts_overlay', 'recipients_overlay']"
    next="Report"
    @next="emit('go', 5)"
  >
    <template #explain>
      <p>
        Member {{ l.member_id }} is a legitimate look-alike: {{ formatUsd(p.amount) }} by {{ p.rail }} to a family member’s new account
        ({{ p.recipient.bank }} {{ p.recipient.account_masked }}), {{ p.date_label }} at {{ p.time_label }}. Same shape as a family-emergency scam.
      </p>
      <p>
        {{ contact.name }} ({{ contact.relationship }}) taps “Yes, it’s my account”, the member taps Send, and it’s done.
        <strong class="text-navy">Target: under 10 minutes.</strong>
      </p>
      <ol class="space-y-2 border-l-2 border-line pl-4" aria-label="Legit path timing (assumed targets)">
        <li v-for="t in timeline" :key="t.at"><span class="font-semibold tabular-nums text-navy">{{ t.at }}</span> · {{ t.label }}</li>
      </ol>
      <p class="rounded-2xl bg-accent-soft p-4 text-base">
        From the data: this payment completed at {{ l.actual.completed_label }}, {{ l.actual.minutes_to_complete }} minutes after a generic warning.
        Our check adds only a quick yes.
      </p>
      <p class="flex items-start gap-3">
        <Zap :size="22" class="mt-0.5 shrink-0 text-accent" aria-hidden="true" />
        Payments to accounts already verified as the contact’s pass instantly, with no extra step.
      </p>
    </template>
    <template #aside>
      <div class="card mt-8 max-w-sm p-5" aria-label="Send anyway screen">
        <p class="text-base font-semibold text-accent">“Send anyway” screen</p>
        <p class="mt-2 flex items-start gap-2 text-lg font-semibold text-navy">
          <TriangleAlert :size="22" class="mt-0.5 shrink-0 text-alert" aria-hidden="true" />You can still send this.
        </p>
        <p class="mt-1 text-base">Money sent by wire is hard to get back.</p>
        <div class="mt-4 flex gap-3" aria-hidden="true">
          <span class="btn btn-primary flex-1 text-base">Go back</span>
          <span class="btn btn-secondary flex-1 text-base">Send anyway</span>
        </div>
        <p class="mt-3 text-base text-muted">The member can always send. It takes one confirmation screen.</p>
      </div>
    </template>

    <div class="w-full max-w-[390px]">
      <PhoneFrame :label="`Member ${l.member_id}'s phone`" :time="p.time_label.replace(/ [AP]M/, '')">
        <Transition name="fade-slide" mode="out-in">
          <div v-if="stage === 'paused'" key="paused" class="flex flex-1 flex-col">
            <div class="mt-6 flex h-16 w-16 items-center justify-center rounded-full bg-accent-soft">
              <Hourglass :size="32" class="text-accent" aria-hidden="true" />
            </div>
            <h3 class="mt-4 text-[26px]">Quick check with {{ contact.name }}</h3>
            <p class="mt-3 text-lg">
              This is a new account for {{ contact.name }}, so we’ve asked on the phone on file since {{ contact.phone_on_file_since_label }}.
              Nothing has been sent yet.
            </p>
            <dl class="mt-5 space-y-2 rounded-2xl bg-page p-4 text-lg">
              <div class="flex justify-between"><dt class="text-muted">To</dt><dd class="font-bold">{{ contact.name }} · {{ capitalize(contact.relationship) }}</dd></div>
              <div class="flex justify-between"><dt class="text-muted">Amount</dt><dd class="font-bold">{{ formatUsd(p.amount) }}</dd></div>
              <div class="flex justify-between"><dt class="text-muted">Account</dt><dd class="font-bold">{{ p.recipient.account_masked }}</dd></div>
            </dl>
          </div>
          <div v-else-if="stage === 'answered'" key="answered" class="flex flex-1 flex-col">
            <div class="mt-6 flex h-16 w-16 items-center justify-center rounded-full bg-ok-soft">
              <CircleCheck :size="34" class="text-ok" aria-hidden="true" />
            </div>
            <h3 class="mt-4 text-[26px]">{{ contact.name }} confirmed this account.</h3>
            <p class="mt-3 text-lg">You’re all set. It took about 2 minutes.</p>
            <div class="mt-auto pt-5">
              <button type="button" class="btn btn-phone btn-primary text-lg" @click="stage = 'sent'">
                <Send :size="20" aria-hidden="true" />Send {{ formatUsd(p.amount) }}
              </button>
            </div>
          </div>
          <div v-else key="sent" class="flex flex-1 flex-col items-center justify-center text-center">
            <CircleCheck :size="64" class="text-ok" aria-hidden="true" />
            <p class="mt-4 text-2xl font-bold text-navy">Sent to {{ contact.name }}</p>
            <p class="mt-2 text-lg text-muted">About 3 minutes from start to finish.</p>
            <button type="button" class="link mt-6" @click="stage = 'paused'">Start over</button>
          </div>
        </Transition>
      </PhoneFrame>
      <div class="mt-6 text-center">
        <button v-if="stage === 'paused'" type="button" class="btn btn-secondary text-base" @click="stage = 'answered'">
          Show {{ contact.name }}’s answer: “Yes, it’s my account”
        </button>
      </div>
    </div>
  </StepLayout>
</template>
