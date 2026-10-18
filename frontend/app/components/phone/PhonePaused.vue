<script setup>
// Step 2 phone: the payment is paused while Tommy is asked.
// Shared by the walkthrough (StepIntervention) and the standalone /prototype app.
// In /prototype (standalone) Linda doesn't call Tommy herself: Sound's automated
// assistant calls Tommy's number on file, and this screen shows that call live.
import { ArrowRight, Check, CircleCheck, Headset, Hourglass, Phone, PhoneCall, ShieldAlert, ShieldCheck, UserRound } from 'lucide-vue-next'
import demo from '~/data/demo.json'
import { formatUsd } from '~/utils/format'

const props = defineProps({
  screen: { type: String, default: undefined }, // paused | calling | cancelled (bound only by /prototype)
  // /prototype: the person Linda meant to pay. Defaults to the walkthrough's Tommy.
  person: { type: Object, default: null },
  standalone: { type: Boolean, default: false }
})
const emit = defineEmits(['next', 'cancel-report', 'specialist', 'update:screen'])

const { scam } = demo
const p = scam.payment
const contact = computed(() => props.person ?? scam.contact)
const who = computed(() => contact.value.firstName ?? contact.value.name)
const poss = computed(() => contact.value.possessive ?? 'his')
const subj = computed(() => contact.value.subject ?? 'he')
const state = ref(props.screen ?? 'paused') // paused | calling | cancelled
watch(() => props.screen, (v) => { if (v !== undefined) state.value = v })
watch(state, (v) => emit('update:screen', v))

// Standalone: Sound's assistant calls Tommy. calling → connected → answered.
const CALL_STEPS = ['calling', 'connected', 'answered']
const callStage = ref('calling')
const callTimers = []
onMounted(() => {
  if (!props.standalone) return
  callTimers.push(setTimeout(() => { callStage.value = 'connected' }, 1600))
  callTimers.push(setTimeout(() => { callStage.value = 'answered' }, 3200))
})
onBeforeUnmount(() => callTimers.forEach(clearTimeout))
const callTitle = computed(() => ({
  calling: `Calling ${who.value}…`,
  connected: 'Connected',
  answered: `${who.value} answered`
})[callStage.value])
const callDetail = computed(() => ({
  calling: `Sound’s assistant is calling ${who.value} on ${poss.value} number on file (since ${contact.value.phone_on_file_since_label})…`,
  connected: `Sound’s assistant is asking ${who.value} one question.`,
  answered: `${who.value} answered the call. See what ${subj.value} said.`
})[callStage.value])
// Small screens: bring the new "see the call" chip into view when Tommy answers.
const answeredChip = ref(null)
const reveal = (el) => el?.scrollIntoView({ block: 'center', behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })
watch(callStage, (v) => { if (v === 'answered') nextTick(() => reveal(answeredChip.value)) })
const stepDone = (step) => CALL_STEPS.indexOf(callStage.value) >= CALL_STEPS.indexOf(step)
</script>

<template>
  <Transition name="fade-slide" mode="out-in">
    <div v-if="state === 'cancelled'" key="c" class="flex flex-1 flex-col items-center justify-center text-center">
      <CircleCheck :size="64" class="text-ok" aria-hidden="true" />
      <p class="mt-4 text-2xl font-bold text-navy" data-screen-title>Payment cancelled</p>
      <p class="mt-2 text-lg text-muted">Nothing was sent. Your {{ formatUsd(p.amount) }} stays in your account.</p>
      <button type="button" class="link mt-6" @click="state = 'paused'">Show the paused screen again</button>
    </div>
    <!-- Standalone: the automated call to Tommy, live. -->
    <div v-else-if="standalone" key="ai" class="flex flex-1 flex-col">
      <div class="mt-6 flex h-16 w-16 items-center justify-center rounded-full bg-alert-soft">
        <ShieldAlert :size="34" class="text-alert" aria-hidden="true" />
      </div>
      <h3 class="mt-4 text-[26px]">This account isn’t {{ who }}’s.</h3>
      <p class="mt-3 flex items-start gap-2 text-lg">
        <Hourglass :size="20" class="mt-1 shrink-0 text-accent" aria-hidden="true" />
        <span>Paused up to {{ scam.hold_hours }} hours. <strong>Nothing has been sent.</strong></span>
      </p>
      <div class="mt-5 rounded-2xl border-2 border-accent bg-accent-soft p-4">
        <div class="flex items-center gap-3">
          <span class="relative shrink-0">
            <span v-if="callStage === 'calling'" class="absolute inset-0 rounded-full bg-accent/30 motion-safe:animate-ping" aria-hidden="true" />
            <PersonAvatar :name="contact.name" :size="44" />
          </span>
          <div class="min-w-0" role="status" aria-live="polite">
            <p class="flex items-center gap-1 text-sm font-semibold uppercase tracking-wider text-accent">
              <PhoneCall :size="14" aria-hidden="true" />Sound’s assistant · automated call
            </p>
            <p class="text-xl font-bold text-navy">{{ callTitle }}</p>
          </div>
        </div>
        <p class="mt-2 text-base">{{ callDetail }}</p>
        <ol class="mt-3 flex flex-wrap gap-2 text-sm font-semibold" aria-label="Call progress">
          <li
            v-for="step in CALL_STEPS"
            :key="step"
            class="inline-flex items-center gap-1 rounded-full border px-2.5 py-1"
            :class="stepDone(step) ? 'border-navy bg-white text-navy' : 'border-line bg-white/60 text-muted'"
          >
            <Check v-if="stepDone(step)" :size="14" aria-hidden="true" />
            <span>{{ step === 'calling' ? 'Calling' : step === 'connected' ? 'Connected' : `${who} answered` }}</span>
            <span class="sr-only">{{ stepDone(step) ? '(done)' : '(waiting)' }}</span>
          </li>
        </ol>
      </div>
      <p class="mt-3 flex items-start gap-2 text-base text-muted">
        <ShieldCheck :size="18" class="mt-1 shrink-0 text-ok" aria-hidden="true" />We never use the number the caller gave you.
      </p>
      <p class="mt-1 flex items-start gap-2 text-base text-muted">
        <UserRound :size="18" class="mt-1 shrink-0" aria-hidden="true" />If {{ who }} doesn’t answer, a Sound fraud specialist follows up, and your payment stays paused.
      </p>
      <button v-if="callStage === 'answered'" ref="answeredChip" type="button" class="proto-chip mt-4 self-start" @click="emit('next')">
        {{ who }} answered: see the call <ArrowRight :size="18" aria-hidden="true" />
      </button>
      <div class="phone-actions mt-auto space-y-3 pt-5">
        <button type="button" class="btn btn-phone btn-primary text-lg" @click="emit('cancel-report')">Cancel payment &amp; report fraud</button>
        <button type="button" class="btn btn-phone btn-secondary text-lg" @click="emit('specialist')">
          <Headset :size="20" aria-hidden="true" />Talk to a Sound specialist
        </button>
      </div>
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
      <div class="phone-actions mt-auto space-y-3 pt-5">
        <button type="button" class="btn btn-phone btn-primary text-lg" @click="state = 'calling'">
          <Phone :size="20" aria-hidden="true" />Call {{ contact.name }}
        </button>
        <button type="button" class="btn btn-phone btn-secondary text-lg" @click="state = 'cancelled'">Cancel payment</button>
      </div>
    </div>
  </Transition>
</template>
