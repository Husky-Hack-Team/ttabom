<script setup>
// "Payment cancelled — $X was not sent · Fraud report filed": the outcome of
// "Cancel payment & report fraud" in Linda's contact mismatch flow (PhoneTwoViews).
import { CircleCheck, FileText, Phone, PhoneOff, ShieldCheck } from 'lucide-vue-next'
import { formatUsd } from '~/utils/format'
import StoryEndActions from '~/components/phone/StoryEndActions.vue'

defineProps({
  amount: { type: Number, required: true },
  reportRef: { type: String, required: true },
  memberPhone: { type: String, required: true },
  // e.g. "Tommy’s real account (Cascade Federal Bank ••••3658) was not affected." Omitted for a new recipient.
  realAccountLine: { type: String, default: '' },
  standalone: { type: Boolean, default: false }
})
const emit = defineEmits(['restart', 'reset'])
</script>

<template>
  <div class="flex flex-1 flex-col">
    <div class="mt-6 flex h-16 w-16 items-center justify-center rounded-full bg-ok-soft">
      <CircleCheck :size="34" class="text-ok" aria-hidden="true" />
    </div>
    <h3 class="mt-4 text-[26px]">Payment cancelled — {{ formatUsd(amount) }} was not sent</h3>
    <p class="mt-3 flex items-center gap-2 text-lg font-semibold text-navy">
      <FileText :size="20" class="shrink-0 text-ok" aria-hidden="true" />Fraud report filed · Ref. {{ reportRef }}
    </p>
    <h4 class="mt-5 text-base font-semibold uppercase tracking-wider text-muted">What happens next</h4>
    <ul class="mt-2 space-y-3 text-base" aria-label="What happens next">
      <li class="flex items-start gap-3">
        <Phone :size="20" class="mt-0.5 shrink-0 text-accent" aria-hidden="true" />
        <span>A Sound fraud specialist will call you at {{ memberPhone }}, the number already on file. Never through the caller.</span>
      </li>
      <li class="flex items-start gap-3">
        <PhoneOff :size="20" class="mt-0.5 shrink-0 text-accent" aria-hidden="true" />
        <span>If the caller calls back, hang up. Don’t share codes, passwords or account numbers.</span>
      </li>
      <li v-if="realAccountLine" class="flex items-start gap-3">
        <ShieldCheck :size="20" class="mt-0.5 shrink-0 text-ok" aria-hidden="true" />
        <span>{{ realAccountLine }}</span>
      </li>
    </ul>
    <button v-if="!standalone" type="button" class="link mt-auto pt-4 text-center" @click="emit('reset')">Start over</button>
    <StoryEndActions v-else @restart="emit('restart')" />
  </div>
</template>
