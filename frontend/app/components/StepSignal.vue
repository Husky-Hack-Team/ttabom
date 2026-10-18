<script setup>
import { Clock, Landmark, TrendingUp, UserRound } from 'lucide-vue-next'
import demo from '~/data/demo.json'
import { formatInt, formatUsd } from '~/utils/format'
import PhoneSendMoney from '~/components/phone/PhoneSendMoney.vue'

const emit = defineEmits(['go'])

const { scam } = demo
const p = scam.payment
const contact = scam.contact
const signals = [
  { icon: UserRound, text: `The account doesn’t belong to the person she picked (${contact.name})`, main: true },
  { icon: Clock, text: `New destination, added today at ${p.recipient_added_label}` },
  { icon: Landmark, text: `First ${p.rail.toLowerCase()} in ${p.years_since_last_same_rail}+ years (${formatInt(p.days_since_last_same_rail)} days)` },
  { icon: TrendingUp, text: `Well above her usual amount (${p.amount_vs_member_baseline}, ${p.amount_to_baseline_ratio.toFixed(1)}×)` }
]
</script>

<template>
  <StepLayout
    :number="1"
    title="Signal: the account doesn’t match the person"
    :data="['recipient_status', 'recipient_age_days', 'days_since_last_same_rail', 'amount_vs_member_baseline', 'contacts_overlay', 'recipient_numbers']"
    next="Intervention"
    @next="emit('go', 2)"
  >
    <template #explain>
      <p>
        {{ scam.member_name }} is sending {{ formatUsd(p.amount) }} by {{ p.rail.toLowerCase() }} to her grandson {{ contact.name }}, or so a
        caller told her. As she selects demo account details, we check them against the accounts {{ contact.name }} has already been paid at.
      </p>
      <p>The check compares the full routing and account numbers. It says only “verified” or “not verified”.</p>
      <ul class="space-y-2 pt-1" aria-label="Signals">
        <li v-for="s in signals" :key="s.text" class="flex items-start gap-3">
          <component :is="s.icon" :size="22" class="mt-0.5 shrink-0" :class="s.main ? 'text-navy' : 'text-muted'" aria-hidden="true" />
          <span :class="s.main ? 'font-semibold text-navy' : ''">
            {{ s.text }}<span v-if="s.main" class="ml-2 rounded-full bg-navy px-2 py-0.5 text-sm font-semibold text-white">Main signal</span>
          </span>
        </li>
      </ul>
      <p class="font-semibold text-navy">
        No single flag stops {{ scam.member_name }}. The mismatch between who she thinks she’s paying and who owns the account does.
      </p>
      <p class="rounded-2xl bg-accent-soft p-4 text-base text-ink">{{ demo.source_note }}</p>
    </template>

    <div class="w-full max-w-[390px]">
      <PhoneFrame :label="`${scam.member_name}'s phone: Send money`" :time="p.time_label.replace(/ [AP]M/, '')">
        <PhoneSendMoney @go="emit('go', $event)" />
      </PhoneFrame>

      <p class="mt-4 text-center text-base text-muted">Use either demo-fill option inside the phone.</p>
    </div>
  </StepLayout>
</template>
