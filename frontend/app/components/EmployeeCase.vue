<script setup>
import { Headset, Landmark, Phone, Undo2, UserRound } from 'lucide-vue-next'
import demo from '~/data/demo.json'
import { formatInt, formatUsd } from '~/utils/format'

const props = defineProps({
  answer: { type: String, default: null } // null | 'yes' | 'no'
})

const { scam } = demo
const p = scam.payment
const contact = scam.contact

// Demo clock: the employee opens the case 48 minutes into the hold.
const HOLD_MINUTES = scam.hold_hours * 60
const left = HOLD_MINUTES - 48
const leftLabel = `${Math.floor(left / 60)}h ${left % 60}m left`
const R = 34
const C = 2 * Math.PI * R
const dash = `${(left / HOLD_MINUTES) * C} ${C}`

const action = ref('')
const answerText = computed(() =>
  props.answer === 'no' ? 'No, it’s not mine' : props.answer === 'yes' ? 'Yes, it’s my account' : 'Waiting for an answer'
)
</script>

<template>
  <article class="card w-full max-w-[400px] p-6" aria-labelledby="case-title">
    <div class="flex items-start justify-between gap-4">
      <div>
        <p class="flex items-center gap-2 text-base font-semibold text-accent"><Headset :size="18" aria-hidden="true" />Employee view</p>
        <h3 id="case-title" class="mt-1 text-2xl">Case {{ scam.case_number }}</h3>
        <p class="text-base text-muted">{{ formatUsd(p.amount) }} {{ p.rail.toLowerCase() }} · {{ p.channel }} · {{ p.time_label }}</p>
      </div>
      <div class="relative h-[84px] w-[84px] shrink-0" role="timer" :aria-label="`Hold: ${leftLabel} of ${scam.hold_hours} hours`">
        <svg viewBox="0 0 84 84" class="h-full w-full -rotate-90" aria-hidden="true">
          <circle cx="42" cy="42" :r="R" fill="none" stroke="var(--color-line)" stroke-width="8" />
          <circle cx="42" cy="42" :r="R" fill="none" stroke="var(--color-accent)" stroke-width="8" stroke-linecap="round" :stroke-dasharray="dash" />
        </svg>
        <span class="absolute inset-0 flex flex-col items-center justify-center text-center text-sm font-bold leading-tight text-navy" aria-hidden="true">
          {{ leftLabel.replace(' left', '') }}<span class="font-medium text-muted">left</span>
        </span>
      </div>
    </div>

    <dl class="mt-5 grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-base">
      <dt class="text-muted">Member</dt><dd class="font-semibold">{{ scam.member_name }}</dd>
      <dt class="text-muted">Intended recipient</dt><dd class="font-semibold">{{ contact.name }} (verified contact)</dd>
      <dt class="text-muted">Destination</dt><dd class="font-semibold">{{ p.recipient.bank }} {{ p.recipient.account_masked }}, owner: not {{ contact.name }}</dd>
      <dt class="text-muted">{{ contact.name }}’s answer</dt>
      <dd class="font-semibold" :class="answer === 'no' ? 'text-alert' : answer === 'yes' ? 'text-ok' : ''" aria-live="polite">{{ answerText }}</dd>
      <dt class="text-muted">Rail</dt><dd class="font-semibold">{{ p.rail }}</dd>
      <dt class="text-muted">Signal</dt><dd class="font-semibold">First {{ p.rail.toLowerCase() }} in {{ p.years_since_last_same_rail }}+ years ({{ formatInt(p.days_since_last_same_rail) }} days)</dd>
    </dl>

    <div class="mt-5 rounded-2xl bg-accent-soft p-4 text-base">
      <p class="font-semibold text-navy">Suggested opening</p>
      <p class="mt-1">“Hi {{ scam.member_name }}, you’re not in trouble. We just want to make sure it reaches {{ contact.name }}.”</p>
    </div>

    <p v-if="action" class="mt-4 rounded-xl bg-page p-3 text-base" role="status">{{ action }}</p>

    <div class="mt-5 flex flex-col gap-3">
      <button type="button" class="btn btn-primary" @click="action = `Calling ${scam.member_name} at ${scam.member_phone_masked}, the number on file.`">
        <Phone :size="18" aria-hidden="true" />Call {{ scam.member_name }}
      </button>
      <button type="button" class="btn btn-secondary" @click="action = `Wire recall requested from ${p.recipient.bank}.`">
        <Undo2 :size="18" aria-hidden="true" />Request wire recall
      </button>
      <button type="button" class="btn btn-secondary" @click="action = 'Case closed with notes. The member’s decision is logged.'">
        <Landmark :size="18" aria-hidden="true" />Close case
      </button>
    </div>
    <p class="mt-4 flex items-start gap-2 text-base text-muted">
      <UserRound :size="18" class="mt-1 shrink-0" aria-hidden="true" />
      {{ scam.member_name }} makes the final decision. Sound can pause and advise, never block permanently.
    </p>
  </article>
</template>
