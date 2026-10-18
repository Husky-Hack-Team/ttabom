<script setup>
// Step 5 phone: report fraud after "Send anyway", and the recovery checklist.
// Used by the walkthrough (StepReport).
import { CircleCheck, FileText, Lock, Phone, ShieldAlert, Undo2 } from 'lucide-vue-next'
import demo from '~/data/demo.json'
import { formatUsd } from '~/utils/format'

const props = defineProps({
  screen: { type: String, default: undefined } // ask | done
})
const emit = defineEmits(['update:screen'])

const { scam } = demo
const p = scam.payment
const reported = ref(props.screen === 'done')
watch(() => props.screen, (v) => { if (v !== undefined) reported.value = v === 'done' })
watch(reported, (v) => emit('update:screen', v ? 'done' : 'ask'))
</script>

<template>
  <div class="mt-3 rounded-2xl border-2 border-accent bg-accent-soft p-4 text-base" role="note">
    <strong class="text-navy">Changed your mind?</strong> Report within the hour for the best chance to recover it.
  </div>
  <Transition name="fade-slide" mode="out-in">
    <div v-if="!reported" key="ask" class="flex flex-1 flex-col">
      <h3 class="mt-6 text-[26px]">{{ formatUsd(p.amount) }} sent</h3>
      <p class="mt-2 text-lg text-muted">{{ p.date_label }}, {{ p.time_label }} · to {{ p.recipient.bank }} {{ p.recipient.account_masked }}</p>
      <div class="phone-actions mt-auto pt-5">
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
</template>
