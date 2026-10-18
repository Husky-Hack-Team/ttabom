<script setup>
import { CircleCheck, FileText, Lock, Phone, ShieldAlert, Undo2 } from 'lucide-vue-next'
import demo from '~/data/demo.json'
import { formatUsd } from '~/utils/format'

const emit = defineEmits(['go'])
const { scam } = demo
const p = scam.payment
const reported = ref(false)

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
        <div class="mt-3 rounded-2xl border-2 border-accent bg-accent-soft p-4 text-base" role="note">
          <strong class="text-navy">Changed your mind?</strong> Report within the hour for the best chance to recover it.
        </div>
        <Transition name="fade-slide" mode="out-in">
          <div v-if="!reported" key="ask" class="flex flex-1 flex-col">
            <h3 class="mt-6 text-[26px]">{{ formatUsd(p.amount) }} sent</h3>
            <p class="mt-2 text-lg text-muted">{{ p.date_label }}, {{ p.time_label }} · to {{ p.recipient.bank }} {{ p.recipient.account_masked }}</p>
            <div class="mt-auto pt-5">
              <button type="button" class="btn btn-phone btn-danger text-lg" @click="reported = true">
                <ShieldAlert :size="22" aria-hidden="true" />I think this was fraud
              </button>
            </div>
          </div>
          <div v-else key="done" class="flex flex-1 flex-col">
            <h3 class="mt-6 text-[26px]">We’re on it.</h3>
            <ul class="mt-4 space-y-4 text-lg" aria-label="What happens now">
              <li class="flex items-start gap-3"><Lock :size="22" class="mt-1 shrink-0 text-ok" aria-hidden="true" /><span><strong>Account protected.</strong> New payments to {{ p.recipient.account_masked }} are blocked.</span></li>
              <li class="flex items-start gap-3"><Undo2 :size="22" class="mt-1 shrink-0 text-ok" aria-hidden="true" /><span><strong>Wire recall requested</strong> from {{ p.recipient.bank }}.</span></li>
              <li class="flex items-start gap-3"><FileText :size="22" class="mt-1 shrink-0 text-ok" aria-hidden="true" /><span><strong>Case number</strong> {{ scam.case_number }}</span></li>
              <li class="flex items-start gap-3"><Phone :size="22" class="mt-1 shrink-0 text-accent" aria-hidden="true" /><span><strong>Next:</strong> A Sound specialist calls you today at {{ scam.member_phone_masked }}.</span></li>
            </ul>
            <p class="mt-5 flex items-start gap-2 rounded-2xl bg-page p-4 text-base">
              <CircleCheck :size="20" class="mt-0.5 shrink-0 text-accent" aria-hidden="true" />Recovery isn’t guaranteed; reporting fast helps.
            </p>
            <button type="button" class="link mt-auto pt-4 text-center" @click="reported = false">Start over</button>
          </div>
        </Transition>
      </PhoneFrame>
    </div>
  </StepLayout>
</template>
