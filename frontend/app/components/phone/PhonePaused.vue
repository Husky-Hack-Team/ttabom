<script setup>
// Step 2 phone: the payment is paused while Tommy is asked.
// Shared by the walkthrough (StepIntervention) and the standalone /prototype app.
import { ArrowRight, CircleCheck, Hourglass, Phone, ShieldAlert } from 'lucide-vue-next'
import demo from '~/data/demo.json'
import { formatUsd } from '~/utils/format'
import StoryEndActions from '~/components/phone/StoryEndActions.vue'

const props = defineProps({
  screen: { type: String, default: undefined }, // paused | calling | cancelled (bound only by /prototype)
  standalone: { type: Boolean, default: false }
})
const emit = defineEmits(['next', 'update:screen', 'other-story', 'home'])

const { scam } = demo
const p = scam.payment
const contact = scam.contact
const state = ref(props.screen ?? 'paused') // paused | calling | cancelled
watch(() => props.screen, (v) => { if (v !== undefined) state.value = v })
watch(state, (v) => emit('update:screen', v))
</script>

<template>
  <Transition name="fade-slide" mode="out-in">
    <div v-if="state === 'cancelled'" key="c" class="flex flex-1 flex-col items-center justify-center text-center">
      <CircleCheck :size="64" class="text-ok" aria-hidden="true" />
      <p class="mt-4 text-2xl font-bold text-navy" data-screen-title>Payment cancelled</p>
      <p class="mt-2 text-lg text-muted">Nothing was sent. Your {{ formatUsd(p.amount) }} stays in your account.</p>
      <button type="button" class="link mt-6" @click="state = 'paused'">Show the paused screen again</button>
      <StoryEndActions v-if="standalone" @other="emit('other-story')" @home="emit('home')" />
    </div>
    <div v-else key="p" class="flex flex-1 flex-col">
      <div class="mt-6 flex h-16 w-16 items-center justify-center rounded-full bg-alert-soft">
        <ShieldAlert :size="34" class="text-alert" aria-hidden="true" />
      </div>
      <h3 class="mt-4 text-[26px]">This account isn’t {{ contact.name }}’s.</h3>
      <p class="mt-3 text-lg">Your {{ formatUsd(p.amount) }} is paused. <strong>Nothing has been sent.</strong></p>
      <div class="mt-5 space-y-3 rounded-2xl bg-page p-4 text-base">
        <p class="flex items-start gap-3"><Hourglass :size="20" class="mt-0.5 shrink-0 text-accent" aria-hidden="true" />Paused up to {{ scam.hold_hours }} hours</p>
        <p class="flex items-center gap-3">
          <PersonAvatar :name="contact.name" :size="36" />
          <span>We’ve asked {{ contact.name }} on his phone on file since {{ contact.phone_on_file_since_label }}.</span>
        </p>
      </div>
      <p v-if="state === 'calling'" class="mt-4 flex items-center gap-2 rounded-2xl bg-accent-soft p-4 text-base" role="status">
        <Phone :size="20" class="text-accent" aria-hidden="true" />Calling {{ contact.name }} at {{ contact.phone_masked }}, the number already on file.
      </p>
      <!-- Standalone only: the walkthrough moves on with its step bar. -->
      <button v-if="standalone" type="button" class="proto-chip mt-4 self-start" @click="emit('next')">
        {{ contact.name }} replied: see {{ contact.name }}’s phone <ArrowRight :size="18" aria-hidden="true" />
      </button>
      <div class="phone-actions mt-auto space-y-3 pt-5">
        <button type="button" class="btn btn-phone btn-primary text-lg" @click="state = 'calling'">
          <Phone :size="20" aria-hidden="true" />Call {{ contact.name }}
        </button>
        <button type="button" class="btn btn-phone btn-secondary text-lg" @click="state = 'cancelled'">Cancel payment</button>
      </div>
    </div>
  </Transition>
</template>
