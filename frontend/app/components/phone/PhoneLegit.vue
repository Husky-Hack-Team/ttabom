<script setup>
// Step 4 phone: the legitimate look-alike (M1037 paying Uma's new account).
// Used by the walkthrough (StepLegit).
// `stage` is owned by the parent: the walkthrough's "Show Uma's answer" button sets it.
import { CircleCheck, Send } from 'lucide-vue-next'
import demo from '~/data/demo.json'
import { capitalize, formatUsd } from '~/utils/format'

defineProps({
  stage: { type: String, default: 'paused' } // paused | answered | sent
})
const emit = defineEmits(['update:stage'])

const { lookalike: l } = demo
const p = l.payment
const contact = l.contact
</script>

<template>
  <Transition name="fade-slide" mode="out-in">
    <div v-if="stage === 'paused'" key="paused" class="flex flex-1 flex-col">
      <div class="mt-6 flex items-center gap-4">
        <PersonAvatar :name="contact.name" :size="64" />
        <div>
          <p class="text-sm font-semibold uppercase tracking-wider text-muted">Checking with</p>
          <p class="text-xl font-bold text-navy">{{ contact.name }}</p>
        </div>
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
      <div class="mt-6 flex items-center gap-4">
        <PersonAvatar :name="contact.name" :size="64" />
        <span class="flex h-10 w-10 items-center justify-center rounded-full bg-ok-soft">
          <CircleCheck :size="26" class="text-ok" aria-hidden="true" />
        </span>
      </div>
      <h3 class="mt-4 text-[26px]">{{ contact.name }} confirmed this account.</h3>
      <p class="mt-3 text-lg">You’re all set. It took about 2 minutes.</p>
      <div class="phone-actions mt-auto pt-5">
        <button type="button" class="btn btn-phone btn-primary text-lg" @click="emit('update:stage', 'sent')">
          <Send :size="20" aria-hidden="true" />Send {{ formatUsd(p.amount) }}
        </button>
      </div>
    </div>
    <div v-else key="sent" class="flex flex-1 flex-col items-center justify-center text-center">
      <CircleCheck :size="64" class="text-ok" aria-hidden="true" />
      <p class="mt-4 text-2xl font-bold text-navy" data-screen-title>Sent to {{ contact.name }}</p>
      <p class="mt-2 text-lg text-muted">About 3 minutes from start to finish.</p>
      <button type="button" class="link mt-6" @click="emit('update:stage', 'paused')">Start over</button>
    </div>
  </Transition>
</template>
