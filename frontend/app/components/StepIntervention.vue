<script setup>
import { CircleCheck, CircleX, Clock, Hourglass, Phone, ShieldAlert } from 'lucide-vue-next'
import demo from '~/data/demo.json'
import { formatUsd } from '~/utils/format'

const emit = defineEmits(['go'])
const { scam } = demo
const p = scam.payment
const contact = scam.contact
const state = ref('paused') // paused | calling | cancelled

// Friendly labels for the dataset's own event types.
const LABELS = {
  'Payment Initiated': 'Wire started at the branch',
  'Confirmation Requested': 'Asked to confirm',
  'Payment Held': 'Held by the back office',
  'Employee Outreach': 'Employee called',
  'Payment Released': `Released: ${formatUsd(p.amount)} sent`,
  'Recovery Request': 'Recovery requested',
  'Recovery Unsuccessful': 'Recovery unsuccessful'
}
const firstDay = scam.without_check[0].date_label
const without = scam.without_check.map((e) => ({
  when: e.date_label === firstDay ? e.time_label : `${e.date_label.replace(/, \d{4}$/, '')}, ${e.time_label}`,
  label: LABELS[e.event_type] || e.event_type,
  detail:
    e.event_type === 'Confirmation Requested'
      ? `She insisted: ${e.note?.replace(/^Member insisted; /, '')}`
      : e.event_type === 'Employee Outreach' && e.member_response === 'Confirmed Intended'
        ? 'She confirmed it again'
        : null,
  bad: ['Payment Released', 'Recovery Unsuccessful'].includes(e.event_type)
}))
</script>

<template>
  <StepLayout
    :number="2"
    title="Intervention: pause before anything leaves"
    :data="['payment_rail', 'event_timestamp', 'contacts_overlay.phone_added_at', 'payment lifecycle rows', 'Member Key dollars']"
    next="Two views"
    @next="emit('go', 3)"
  >
    <template #explain>
      <p>
        <strong class="text-navy">Why now:</strong> a wire can be held for up to {{ scam.hold_hours }} hours before it leaves, and once it’s sent
        it’s hard to get back. P2P is checked before she taps Send, because P2P can’t be recalled.
      </p>
      <p>
        Sound asks the real {{ contact.name }} on the phone on file for at least 7 days (since {{ contact.phone_on_file_since_label }}), never a
        number the caller gave.
      </p>
    </template>
    <template #aside>
      <div class="mt-8 grid gap-4 sm:grid-cols-2">
        <div class="card p-5">
          <h3 class="flex items-center gap-2 text-lg"><CircleX :size="20" class="text-alert" aria-hidden="true" />Without our check</h3>
          <p class="text-base text-muted">What happened in the data, {{ p.date_label }}</p>
          <ol class="mt-3 space-y-3 border-l-2 border-line pl-4 text-base">
            <li v-for="(e, i) in without" :key="i">
              <span class="font-semibold tabular-nums">{{ e.when }}</span> · <span :class="e.bad ? 'font-semibold text-alert' : ''">{{ e.label }}</span>
              <span v-if="e.detail" class="block text-muted">{{ e.detail }}</span>
            </li>
          </ol>
          <p class="mt-3 rounded-xl bg-alert-soft p-3 text-base">
            Member Key: <strong>{{ formatUsd(scam.key.dollars_sent) }} lost</strong>; the next day’s
            {{ formatUsd(scam.key.dollars_prevented) }} cash request was stopped.
          </p>
        </div>
        <div class="card p-5">
          <h3 class="flex items-center gap-2 text-lg"><CircleCheck :size="20" class="text-ok" aria-hidden="true" />With our check</h3>
          <p class="text-base text-muted">Same day, same signals</p>
          <ol class="mt-3 space-y-3 border-l-2 border-line pl-4 text-base">
            <li><span class="font-semibold tabular-nums">{{ p.time_label }}</span> · Paused, before anything left</li>
            <li><span class="font-semibold tabular-nums">{{ p.time_label }}</span> · {{ contact.name }} asked on the phone on file since {{ contact.phone_on_file_since_label }}</li>
            <li>{{ scam.member_name }} decides, with {{ contact.name }}’s answer in hand</li>
          </ol>
        </div>
      </div>
    </template>

    <div class="w-full max-w-[390px]">
      <PhoneFrame :label="`${scam.member_name}'s phone: payment paused`" :time="p.time_label.replace(/ [AP]M/, '')">
        <Transition name="fade-slide" mode="out-in">
          <div v-if="state === 'cancelled'" key="c" class="flex flex-1 flex-col items-center justify-center text-center">
            <CircleCheck :size="64" class="text-ok" aria-hidden="true" />
            <p class="mt-4 text-2xl font-bold text-navy">Payment cancelled</p>
            <p class="mt-2 text-lg text-muted">Nothing was sent. Your {{ formatUsd(p.amount) }} stays in your account.</p>
            <button type="button" class="link mt-6" @click="state = 'paused'">Show the paused screen again</button>
          </div>
          <div v-else key="p" class="flex flex-1 flex-col">
            <div class="mt-6 flex h-16 w-16 items-center justify-center rounded-full bg-alert-soft">
              <ShieldAlert :size="34" class="text-alert" aria-hidden="true" />
            </div>
            <h3 class="mt-4 text-[26px]">This account isn’t {{ contact.name }}’s.</h3>
            <p class="mt-3 text-lg">Your {{ formatUsd(p.amount) }} is paused. <strong>Nothing has been sent.</strong></p>
            <div class="mt-5 space-y-3 rounded-2xl bg-page p-4 text-base">
              <p class="flex items-start gap-3"><Hourglass :size="20" class="mt-0.5 shrink-0 text-accent" aria-hidden="true" />Paused up to {{ scam.hold_hours }} hours</p>
              <p class="flex items-start gap-3">
                <Clock :size="20" class="mt-0.5 shrink-0 text-accent" aria-hidden="true" />
                We’ve asked {{ contact.name }} on his phone on file since {{ contact.phone_on_file_since_label }}.
              </p>
            </div>
            <p v-if="state === 'calling'" class="mt-4 flex items-center gap-2 rounded-2xl bg-accent-soft p-4 text-base" role="status">
              <Phone :size="20" class="text-accent" aria-hidden="true" />Calling {{ contact.name }} at {{ contact.phone_masked }}, the number already on file.
            </p>
            <div class="mt-auto space-y-3 pt-5">
              <button type="button" class="btn btn-phone btn-primary text-lg" @click="state = 'calling'">
                <Phone :size="20" aria-hidden="true" />Call {{ contact.name }}
              </button>
              <button type="button" class="btn btn-phone btn-secondary text-lg" @click="state = 'cancelled'">Cancel payment</button>
            </div>
          </div>
        </Transition>
      </PhoneFrame>
    </div>
  </StepLayout>
</template>
