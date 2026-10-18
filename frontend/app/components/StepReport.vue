<script setup>
import demo from '~/data/demo.json'
import { formatUsd } from '~/utils/format'
import PhoneReport from '~/components/phone/PhoneReport.vue'

const emit = defineEmits(['go'])
const { scam } = demo
const p = scam.payment

const recoveryRequest = scam.without_check.find((e) => e.event_type === 'Recovery Request')
const recoveryResult = scam.without_check.find((e) => e.event_type === 'Recovery Unsuccessful')
</script>

<template>
  <StepLayout
    :number="5"
    title="Report: one tap starts recovery"
    :data="['payment_id', 'recipients_overlay.bank', 'member_channels.phone', 'Recovery Request rows', 'Member Key dollars_recovered']"
    next="Pilot"
    @next="emit('go', 6)"
  >
    <template #explain>
      <p>
        If {{ scam.member_name }} sends anyway and then has second thoughts, the next screen keeps a way back in reach. One tap reports it, protects
        the account, and asks the receiving bank to recall the wire.
      </p>
      <p>
        In the data, recovery was requested on {{ recoveryRequest?.date_label }} at {{ recoveryRequest?.time_label }}, the day after the wire, and came
        back unsuccessful on {{ recoveryResult?.date_label }}. Recovered: {{ formatUsd(scam.key.dollars_recovered) }}. Reporting within the hour gives
        the recall its best chance.
      </p>
    </template>

    <div class="w-full max-w-[390px]">
      <PhoneFrame :label="`${scam.member_name}'s phone: report fraud`" :time="p.time_label.replace(/ [AP]M/, '')">
        <PhoneReport />
      </PhoneFrame>
    </div>
  </StepLayout>
</template>
