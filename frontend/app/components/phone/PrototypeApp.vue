<script setup>
// The standalone /prototype app: Linda's story only, on one phone, driven
// entirely from inside it. It reuses the walkthrough's phone screens
// (components/phone/*) in standalone mode and adds an in-app header
// (Back · Start over · Help) and a Help sheet with the synthetic-data disclaimer.
// "Send money" has a recipient picker: Tommy (default), Margaret, Daniel, or a
// custom recipient, which goes through a "Do you know this person?" question
// and a deterministic risk check instead of an ownership check.
import { ArrowRight, Check, ChevronLeft, CircleHelp, Headset, Plus, RotateCcw, Smartphone, X } from 'lucide-vue-next'
import demo from '~/data/demo.json'
import { formatUsd } from '~/utils/format'
import PhoneFrame from '~/components/PhoneFrame.vue'
import PhoneSendMoney from '~/components/phone/PhoneSendMoney.vue'
import PhonePaused from '~/components/phone/PhonePaused.vue'
import PhoneTwoViews from '~/components/phone/PhoneTwoViews.vue'
import PhoneCustomPayment from '~/components/phone/PhoneCustomPayment.vue'
import { RECIPIENTS, recipientById } from '~/data/prototypeRecipients'
import { KNOW_ANSWERS } from '~/utils/riskCheck'

const { scam } = demo

// Each screen's first sub-screen, so Back can always restore an exact state.
const FIRST_SUB = { send: 'form', paused: 'paused', views: 'main', custom: 'form' }
const FIRST_SCREEN = 'send'

// fresh() resets a screen; who Linda is paying (recipient), her answer to
// "Do you know this person?" (knows) and where the money would go (dest) carry over.
const fresh = (screen) => ({ screen, sub: FIRST_SUB[screen], view: 'linda', answer: null })
const START = () => ({ ...fresh(FIRST_SCREEN), recipient: 'tommy', knows: null, dest: null })
const state = reactive(START())
const person = computed(() => recipientById(state.recipient))
const PEOPLE = computed(() => ({
  linda: { id: 'linda', name: scam.member_name, color: 'linda' },
  // The contact's phone (Tommy, Margaret or Daniel) uses the contact colors.
  contact: { id: person.value.id, name: person.value.name, color: 'tommy' }
}))
const history = []
const canGoBack = ref(false)

// Several v-model updates can arrive in one click (Tommy's answer sets answer,
// screen and view); they become one history entry.
let pending = false
function navigate(patch) {
  if (!pending) {
    history.push({ ...state })
    pending = true
    queueMicrotask(() => {
      pending = false
      afterNavigate()
    })
  }
  Object.assign(state, patch)
  canGoBack.value = history.length > 0
}
const go = (screen) => navigate({ ...fresh(screen) })
const onSub = (v) => { if (v !== state.sub) navigate({ sub: v }) }
const onView = (v) => { if (v !== state.view) navigate({ view: v }) }
const onAnswer = (v) => { if (v !== state.answer) navigate({ answer: v }) }

function back() {
  if (!history.length) return
  Object.assign(state, history.pop())
  canGoBack.value = history.length > 0
  afterNavigate()
}
// Start over: back to Linda's first screen with an empty history.
function restart() {
  history.length = 0
  canGoBack.value = false
  Object.assign(state, START())
  afterNavigate()
}

const currentPhoneKey = computed(() => {
  if (state.screen === 'views' && state.view === 'tommy') return 'contact'
  return 'linda'
})
const currentPhone = computed(() => PEOPLE.value[currentPhoneKey.value])

// Make the handoff between Linda and Tommy visually explicit. The state changes
// immediately; this short overlay confirms that the prototype moved devices.
const switching = ref(null)
let switchTimer
watch(currentPhoneKey, (next, previous) => {
  if (!next || !previous || next === previous) return
  switching.value = { from: PEOPLE.value[previous], to: PEOPLE.value[next] }
  clearTimeout(switchTimer)
  switchTimer = setTimeout(() => { switching.value = null }, 900)
})
onBeforeUnmount(() => clearTimeout(switchTimer))

const frameTime = scam.payment.time_label.replace(/ [AP]M/, '')
const frameLabel = computed(() => {
  if (state.screen === 'views' && state.view === 'tommy') return `${person.value.firstName}'s phone`
  return `${scam.member_name}'s phone`
})
const whosePhone = computed(() => {
  if (state.screen === 'views' && state.view === 'tommy') return `${person.value.firstName}’s phone`
  return `${scam.member_name}’s phone`
})

// Announce screen changes, and move focus to the new screen's heading when it changed.
const content = ref(null)
const announcement = ref('')
let lastHeading = ''
function afterNavigate() {
  setTimeout(() => {
    const el = content.value?.querySelector('h3, [data-screen-title]')
    if (!el || sheetOpen.value) return // a sheet or modal has focus
    const text = el.textContent.trim()
    if (text === lastHeading) return
    lastHeading = text
    announcement.value = `${whosePhone.value}: ${text}`
    if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '-1')
    el.focus({ preventScroll: true })
    content.value.scrollTop = 0
  }, 450)
}

// "Talk to a Sound specialist" (Linda) / "Talk to a person" (Tommy): a real person calls back.
const specialist = ref(null) // null | 'linda' | 'tommy'
const specialistAmount = ref(scam.payment.amount)
const specialistSheet = ref(null)
const specialistClose = ref(null)
let specialistReturn = null
function openSpecialist(who, amount = scam.payment.amount) {
  specialistAmount.value = amount
  specialistReturn = document.activeElement
  specialist.value = who
  nextTick(() => specialistClose.value?.focus())
}
function closeSpecialist() {
  specialist.value = null
  nextTick(() => specialistReturn?.focus?.())
}
function specialistKeydown(e) {
  if (e.key === 'Escape') return closeSpecialist()
  if (e.key === 'Tab') { e.preventDefault(); specialistClose.value?.focus() }
}
// Keep Tab inside an open sheet or modal.
function trapTab(e, el) {
  if (e.key !== 'Tab' || !el) return
  const items = [...el.querySelectorAll('button:not([disabled])')]
  const first = items[0]
  const last = items[items.length - 1]
  if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus() }
  else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus() }
}

// Recipient picker (bottom sheet): rows show only avatar, name and relationship.
const pickerOpen = ref(false)
const pickerSheet = ref(null)
let pickerReturn = null
function openPicker() {
  pickerReturn = document.activeElement
  pickerOpen.value = true
  nextTick(() => (pickerSheet.value?.querySelector('[aria-checked="true"]') ?? pickerSheet.value?.querySelector('button'))?.focus())
}
function closePicker(restoreFocus = true) {
  pickerOpen.value = false
  if (restoreFocus) nextTick(() => pickerReturn?.focus?.())
}
function pickerKeydown(e) {
  if (e.key === 'Escape') return closePicker()
  trapTab(e, pickerSheet.value)
}
function chooseRecipient(id) {
  closePicker(false)
  if (state.screen === 'send' && state.recipient === id) return nextTick(() => pickerReturn?.focus?.())
  navigate({ ...fresh('send'), recipient: id, dest: null })
}
function chooseCustom() {
  closePicker(false)
  navigate({ ...fresh('custom'), sub: 'ask', knows: null, dest: null })
}

// "Do you know this person?": a step of its own (sub 'ask'), so Back returns to
// it and a different answer recomputes the risk on the next Review.
const knowOpen = computed(() => state.screen === 'custom' && state.sub === 'ask')
const knowModal = ref(null)
watch(knowOpen, (open) => {
  if (open) nextTick(() => (knowModal.value?.querySelector('[aria-pressed="true"]') ?? knowModal.value?.querySelector('button'))?.focus())
})
function answerKnow(id) {
  navigate({ sub: 'form', knows: id })
}
function closeKnow() {
  // Esc / Close: back out of this step and reopen the picker.
  back()
  nextTick(openPicker)
}
function knowKeydown(e) {
  if (e.key === 'Escape') return closeKnow()
  trapTab(e, knowModal.value)
}

const sheetOpen = computed(() => helpOpen.value || !!specialist.value || pickerOpen.value || knowOpen.value)

// Help sheet
const helpOpen = ref(false)
const helpButton = ref(null)
const helpClose = ref(null)
const helpSheet = ref(null)
function openHelp() {
  helpOpen.value = true
  nextTick(() => helpClose.value?.focus())
}
function closeHelp() {
  helpOpen.value = false
  nextTick(() => helpButton.value?.focus())
}
function helpKeydown(e) {
  if (e.key === 'Escape') return closeHelp()
  if (e.key !== 'Tab') return
  const items = [...helpSheet.value.querySelectorAll('button')]
  const first = items[0]
  const last = items[items.length - 1]
  if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus() }
  else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus() }
}
</script>

<template>
  <PhoneFrame :label="frameLabel" :time="frameTime" fullscreen>
    <div class="proto-app relative flex min-h-0 flex-1 flex-col bg-white">
      <header class="flex h-14 shrink-0 items-center justify-between gap-2 border-b border-line px-2" :inert="sheetOpen || undefined">
        <!-- Nothing comes before the first screen, so Back appears only once you've moved on. -->
        <button v-if="canGoBack" type="button" class="proto-icon-btn" @click="back">
          <ChevronLeft :size="24" aria-hidden="true" /><span>Back</span>
        </button>
        <span v-else class="proto-app-title">Demo Prototype</span>
        <p class="sr-only">{{ whosePhone }}</p>
        <div class="flex items-center gap-1">
          <button v-if="canGoBack" type="button" class="proto-icon-btn" @click="restart">
            <RotateCcw :size="20" aria-hidden="true" /><span>Start over</span>
          </button>
          <button ref="helpButton" type="button" class="proto-icon-btn" aria-haspopup="dialog" @click="openHelp">
            <CircleHelp :size="20" aria-hidden="true" /><span>Help</span>
          </button>
        </div>
      </header>

      <Transition name="owner-swap" mode="out-in">
        <div
          :key="currentPhone.id"
          class="phone-owner-strip"
          :class="`is-${currentPhone.color}`"
        >
          <PersonAvatar :name="currentPhone.name" :size="42" />
          <span class="min-w-0 flex-1 leading-tight">
            <span class="block text-xs font-bold uppercase tracking-[0.12em] opacity-70">You’re using</span>
            <strong class="block text-lg">{{ currentPhone.name }}’s phone</strong>
          </span>
          <Smartphone :size="24" class="shrink-0 opacity-70" aria-hidden="true" />
        </div>
      </Transition>

      <div ref="content" class="proto-scroll flex min-h-0 flex-1 flex-col overflow-y-auto px-5 pb-6" :inert="sheetOpen || undefined">
        <Transition name="fade-slide" mode="out-in">
          <div v-if="state.screen === 'send'" key="send" class="flex flex-1 flex-col">
            <PhoneSendMoney
              standalone
              :person="person"
              :screen="state.sub"
              @update:screen="onSub"
              @go="(_, dest) => navigate({ ...fresh('paused'), dest })"
              @pick="openPicker"
              @restart="restart"
            />
          </div>
          <div v-else-if="state.screen === 'paused'" key="paused" class="flex flex-1 flex-col">
            <PhonePaused
              standalone
              :person="person"
              :screen="state.sub"
              @update:screen="onSub"
              @next="navigate({ ...fresh('views'), view: 'tommy' })"
              @cancel-report="navigate({ ...fresh('views'), sub: 'reported' })"
              @specialist="openSpecialist('linda')"
              @restart="restart"
            />
          </div>
          <div v-else-if="state.screen === 'views'" key="views" class="flex flex-1 flex-col">
            <PhoneTwoViews
              standalone
              :person="person"
              :dest="state.dest"
              :view="state.view"
              :answer="state.answer"
              :screen="state.sub"
              @update:view="onView"
              @update:answer="onAnswer"
              @update:screen="onSub"
              @specialist="openSpecialist('tommy')"
              @restart="restart"
            />
          </div>
          <div v-else-if="state.screen === 'custom'" key="custom" class="flex flex-1 flex-col">
            <PhoneCustomPayment
              :answer="state.knows"
              :screen="state.sub === 'ask' ? 'form' : state.sub"
              @update:screen="(v) => { if (state.sub !== 'ask' || v !== 'form') onSub(v) }"
              @change-answer="navigate({ sub: 'ask' })"
              @pick="openPicker"
              @specialist="(amount) => openSpecialist('linda', amount)"
              @restart="restart"
            />
          </div>
        </Transition>
      </div>

      <Transition name="phone-switch">
        <div v-if="switching" class="phone-switch-overlay" role="status" aria-live="assertive">
          <p class="text-sm font-bold uppercase tracking-[0.16em] text-muted">Switching phones</p>
          <div class="mt-5 flex items-center justify-center gap-4" aria-hidden="true">
            <div class="phone-switch-person is-from">
              <PersonAvatar :name="switching.from.name" :size="58" />
              <span>{{ switching.from.name }}</span>
            </div>
            <ArrowRight :size="30" class="phone-switch-arrow text-accent" />
            <div class="phone-switch-person is-to">
              <PersonAvatar :name="switching.to.name" :size="74" />
              <span>{{ switching.to.name }}</span>
            </div>
          </div>
          <p class="mt-5 text-2xl font-bold text-navy">Now on {{ switching.to.name }}’s phone</p>
        </div>
      </Transition>

      <p class="sr-only" aria-live="polite">{{ announcement }}</p>

      <Transition name="fade-slide">
        <div v-if="pickerOpen" class="absolute inset-0 z-20 flex flex-col justify-end bg-[rgb(15_27_45/0.45)]" @click.self="closePicker()">
          <div
            ref="pickerSheet"
            class="max-h-[90%] overflow-y-auto rounded-t-[28px] bg-white px-5 pb-6 pt-5 shadow-[0_-8px_30px_rgb(0_32_91/0.15)]"
            role="dialog"
            aria-modal="true"
            aria-labelledby="picker-title"
            @keydown="pickerKeydown"
          >
            <div class="flex items-start justify-between gap-3">
              <h2 id="picker-title" class="text-2xl">Send to</h2>
              <button type="button" class="proto-icon-btn -mr-2" @click="closePicker()">
                <X :size="22" aria-hidden="true" /><span>Close</span>
              </button>
            </div>
            <ul class="mt-3 space-y-2" role="radiogroup" aria-labelledby="picker-title">
              <li v-for="r in RECIPIENTS" :key="r.id">
                <button
                  type="button"
                  role="radio"
                  class="proto-pick-row"
                  :aria-checked="state.screen !== 'custom' && state.recipient === r.id ? 'true' : 'false'"
                  @click="chooseRecipient(r.id)"
                >
                  <PersonAvatar :name="r.name" :size="44" />
                  <span class="min-w-0 flex-1 text-left">
                    <strong class="block text-lg text-navy">{{ r.name }}</strong>
                    <span class="block text-base text-muted">{{ r.relationship }}</span>
                  </span>
                  <span v-if="state.screen !== 'custom' && state.recipient === r.id" class="inline-flex items-center gap-1 text-sm font-semibold text-accent">
                    <Check :size="18" aria-hidden="true" />Selected
                  </span>
                </button>
              </li>
              <li>
                <button
                  type="button"
                  role="radio"
                  class="proto-pick-row"
                  :aria-checked="state.screen === 'custom' ? 'true' : 'false'"
                  @click="chooseCustom"
                >
                  <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full border-2 border-dashed border-accent text-accent" aria-hidden="true">
                    <Plus :size="22" />
                  </span>
                  <span class="min-w-0 flex-1 text-left">
                    <strong class="block text-lg text-navy">Custom recipient</strong>
                    <span class="block text-base text-muted">Someone not in your list</span>
                  </span>
                </button>
              </li>
            </ul>
          </div>
        </div>
      </Transition>

      <Transition name="fade-slide">
        <div v-if="knowOpen" class="absolute inset-0 z-20 flex flex-col justify-end bg-[rgb(15_27_45/0.45)]" @click.self="closeKnow">
          <div
            ref="knowModal"
            class="max-h-[90%] overflow-y-auto rounded-t-[28px] bg-white px-5 pb-6 pt-5 shadow-[0_-8px_30px_rgb(0_32_91/0.15)]"
            role="dialog"
            aria-modal="true"
            aria-labelledby="know-title"
            aria-describedby="know-note"
            @keydown="knowKeydown"
          >
            <div class="flex items-start justify-between gap-3">
              <h2 id="know-title" class="text-2xl">Do you know this person?</h2>
              <button type="button" class="proto-icon-btn -mr-2" @click="closeKnow">
                <X :size="22" aria-hidden="true" /><span>Close</span>
              </button>
            </div>
            <div class="mt-4 space-y-3">
              <button
                v-for="a in KNOW_ANSWERS"
                :key="a.id"
                type="button"
                class="btn btn-phone text-lg"
                :class="state.knows === a.id ? 'btn-primary' : 'btn-secondary'"
                :aria-pressed="state.knows === a.id ? 'true' : 'false'"
                @click="answerKnow(a.id)"
              >
                <Check v-if="state.knows === a.id" :size="20" aria-hidden="true" />{{ a.label }}
              </button>
            </div>
            <p id="know-note" class="mt-4 text-base text-muted">Sound will never ask you to move money to protect it.</p>
          </div>
        </div>
      </Transition>

      <Transition name="fade-slide">
        <div v-if="specialist" class="absolute inset-0 z-20 flex flex-col justify-end bg-[rgb(15_27_45/0.45)]" @click.self="closeSpecialist">
          <div
            ref="specialistSheet"
            class="max-h-[90%] overflow-y-auto rounded-t-[28px] bg-white px-5 pb-6 pt-5 shadow-[0_-8px_30px_rgb(0_32_91/0.15)]"
            role="dialog"
            aria-modal="true"
            aria-labelledby="specialist-title"
            @keydown="specialistKeydown"
          >
            <span class="flex h-12 w-12 items-center justify-center rounded-full bg-accent-soft"><Headset :size="26" class="text-accent" aria-hidden="true" /></span>
            <h2 id="specialist-title" class="mt-3 text-2xl">{{ specialist === 'linda' ? 'A Sound specialist will call you' : 'A person will call you back' }}</h2>
            <p v-if="specialist === 'linda'" class="mt-3 text-base">
              A Sound fraud specialist, a real person, will call you back at {{ scam.member_phone_masked }}, your number on file. Your
              {{ formatUsd(specialistAmount) }} stays paused while you wait.
            </p>
            <p v-else class="mt-3 text-base">
              A Sound fraud specialist, a real person, will call you back on this number. You don’t need to do anything else right now.
            </p>
            <p class="mt-3 text-base text-muted">Sound will never ask for codes, passwords or account numbers.</p>
            <button ref="specialistClose" type="button" class="btn btn-phone btn-primary mt-5 text-lg" @click="closeSpecialist">OK</button>
          </div>
        </div>
      </Transition>

      <Transition name="fade-slide">
        <div v-if="helpOpen" class="absolute inset-0 z-20 flex flex-col justify-end bg-[rgb(15_27_45/0.45)]" @click.self="closeHelp">
          <div
            ref="helpSheet"
            class="max-h-[90%] overflow-y-auto rounded-t-[28px] bg-white px-5 pb-6 pt-5 shadow-[0_-8px_30px_rgb(0_32_91/0.15)]"
            role="dialog"
            aria-modal="true"
            aria-labelledby="help-title"
            @keydown="helpKeydown"
          >
            <div class="flex items-start justify-between gap-3">
              <h2 id="help-title" class="text-2xl">About this prototype</h2>
              <button ref="helpClose" type="button" class="proto-icon-btn -mr-2" @click="closeHelp">
                <X :size="22" aria-hidden="true" /><span>Close</span>
              </button>
            </div>
            <p class="mt-3 rounded-2xl bg-accent-soft p-4 text-base font-semibold text-navy">{{ demo.disclaimer }}</p>
            <p class="mt-3 text-base">{{ demo.source_note }}</p>
            <p class="mt-3 text-base">Margaret and Daniel are fictional contacts made up for this prototype.</p>
            <p class="mt-3 text-base text-muted">
              Follow Linda’s payment using the buttons on each screen. Back steps through your path; Start over returns to the first screen.
            </p>
            <p class="mt-3 text-base text-muted">Concept prototype for HuskyHack 2026. Not an official Sound Credit Union product.</p>
            <button type="button" class="btn btn-phone btn-secondary mt-5 text-lg" @click="closeHelp(); restart()">Start over</button>
          </div>
        </div>
      </Transition>
    </div>
  </PhoneFrame>
</template>
