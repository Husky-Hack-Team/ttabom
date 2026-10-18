<script setup>
// The standalone /prototype app: only the phone, driven entirely from inside it.
// It reuses the walkthrough's phone screens (components/phone/*) in standalone
// mode and adds a home screen, an in-app header (Back · Home · Help) and a
// Help sheet with the synthetic-data disclaimer.
import { ArrowRight, ChevronLeft, ChevronRight, CircleCheck, CircleHelp, House, ShieldAlert, Smartphone, X } from 'lucide-vue-next'
import demo from '~/data/demo.json'
import { formatUsd } from '~/utils/format'
import PhoneFrame from '~/components/PhoneFrame.vue'
import PhoneSendMoney from '~/components/phone/PhoneSendMoney.vue'
import PhonePaused from '~/components/phone/PhonePaused.vue'
import PhoneTwoViews from '~/components/phone/PhoneTwoViews.vue'
import PhoneReport from '~/components/phone/PhoneReport.vue'
import PhoneLegit from '~/components/phone/PhoneLegit.vue'

const { scam, lookalike } = demo

// Each screen's first sub-screen, so Back can always restore an exact state.
const FIRST_SUB = { home: null, send: 'form', paused: 'paused', views: 'main', report: 'ask', legit: 'paused' }
const STORY_OF = { send: 'linda', paused: 'linda', views: 'linda', report: 'linda', legit: 'uma' }
const START_OF = { linda: 'send', uma: 'legit' }
const PEOPLE = {
  linda: { id: 'linda', name: scam.member_name, color: 'linda' },
  tommy: { id: 'tommy', name: scam.contact.name, color: 'tommy' }
}

const STORIES = [
  {
    id: 'linda',
    name: scam.member_name,
    avatar: scam.member_name,
    line: `A caller says her grandson ${scam.contact.name} needs ${formatUsd(scam.payment.amount)} by ${scam.payment.rail.toLowerCase()}.`,
    tag: 'Scam',
    icon: ShieldAlert,
    tagClass: 'border-alert text-alert'
  },
  {
    id: 'uma',
    name: lookalike.contact.name,
    avatar: lookalike.contact.name,
    line: `A family member sends ${formatUsd(lookalike.payment.amount)} to ${lookalike.contact.name}’s new account.`,
    tag: 'Legit look-alike',
    icon: CircleCheck,
    tagClass: 'border-ok text-ok'
  }
]

const fresh = (screen) => ({ screen, sub: FIRST_SUB[screen], view: 'linda', answer: null })
const state = reactive(fresh('home'))
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
function home() {
  history.length = 0
  canGoBack.value = false
  Object.assign(state, fresh('home'))
  afterNavigate()
}
function startStory(id) {
  history.length = 0
  history.push(fresh('home')) // Back from a story's first screen returns home.
  canGoBack.value = true
  Object.assign(state, fresh(START_OF[id]))
  afterNavigate()
}
const otherStory = () => startStory(STORY_OF[state.screen] === 'linda' ? 'uma' : 'linda')

const currentPhoneKey = computed(() => {
  if (state.screen === 'home' || state.screen === 'legit') return null
  if (state.screen === 'views' && state.view === 'tommy') return 'tommy'
  return 'linda'
})
const currentPhone = computed(() => currentPhoneKey.value ? PEOPLE[currentPhoneKey.value] : null)

// Make the handoff between Linda and Tommy visually explicit. The state changes
// immediately; this short overlay confirms that the prototype moved devices.
const switching = ref(null)
let switchTimer
watch(currentPhoneKey, (next, previous) => {
  if (!next || !previous || next === previous) return
  switching.value = { from: PEOPLE[previous], to: PEOPLE[next] }
  clearTimeout(switchTimer)
  switchTimer = setTimeout(() => { switching.value = null }, 900)
})
onBeforeUnmount(() => clearTimeout(switchTimer))

const frameTime = computed(() =>
  (state.screen === 'legit' ? lookalike.payment.time_label : scam.payment.time_label).replace(/ [AP]M/, '')
)
const frameLabel = computed(() => {
  if (state.screen === 'home') return 'Prototype: choose a story'
  if (state.screen === 'legit') return `Member ${lookalike.member_id}'s phone`
  if (state.screen === 'views' && state.view === 'tommy') return `${scam.contact.name}'s phone`
  return `${scam.member_name}'s phone`
})
const whosePhone = computed(() => {
  if (state.screen === 'home') return 'Stories'
  if (state.screen === 'legit') return 'Family member’s phone'
  if (state.screen === 'views' && state.view === 'tommy') return `${scam.contact.name}’s phone`
  return `${scam.member_name}’s phone`
})

// Announce screen changes, and move focus to the new screen's heading when it changed.
const content = ref(null)
const announcement = ref('')
let lastHeading = ''
function afterNavigate() {
  setTimeout(() => {
    const el = content.value?.querySelector('h3, [data-screen-title]')
    if (!el) return
    const text = el.textContent.trim()
    if (text === lastHeading) return
    lastHeading = text
    announcement.value = `${whosePhone.value}: ${text}`
    if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '-1')
    el.focus({ preventScroll: true })
    content.value.scrollTop = 0
  }, 450)
}

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
      <header class="flex h-14 shrink-0 items-center justify-between gap-2 border-b border-line px-2" :inert="helpOpen || undefined">
        <button v-if="state.screen !== 'home'" type="button" class="proto-icon-btn" :disabled="!canGoBack" @click="back">
          <ChevronLeft :size="24" aria-hidden="true" /><span>Back</span>
        </button>
        <span v-else class="proto-app-title">Demo Prototype</span>
        <p class="sr-only">{{ whosePhone }}</p>
        <div class="flex items-center gap-1">
          <button v-if="state.screen !== 'home'" type="button" class="proto-icon-btn" @click="home">
            <House :size="20" aria-hidden="true" /><span>Home</span>
          </button>
          <button ref="helpButton" type="button" class="proto-icon-btn" aria-haspopup="dialog" @click="openHelp">
            <CircleHelp :size="20" aria-hidden="true" /><span>Help</span>
          </button>
        </div>
      </header>

      <Transition name="owner-swap" mode="out-in">
        <div
          v-if="currentPhone"
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
        <div v-else-if="state.screen === 'legit'" key="family" class="phone-owner-strip is-family">
          <span class="flex h-[42px] w-[42px] shrink-0 items-center justify-center rounded-full bg-white/80">
            <Smartphone :size="23" aria-hidden="true" />
          </span>
          <span class="min-w-0 flex-1 leading-tight">
            <span class="block text-xs font-bold uppercase tracking-[0.12em] opacity-70">You’re using</span>
            <strong class="block text-lg">Family member’s phone</strong>
          </span>
        </div>
      </Transition>

      <div ref="content" class="proto-scroll flex min-h-0 flex-1 flex-col overflow-y-auto px-5 pb-6" :inert="helpOpen || undefined">
        <Transition name="fade-slide" mode="out-in">
          <div v-if="state.screen === 'home'" key="home" class="flex flex-1 flex-col">
            <h3 class="mt-6 text-[26px]">Choose a story</h3>
            <p class="mt-2 text-lg text-muted">Two moments from the HuskyHack data. See how the account check handles each one.</p>
            <ul class="mt-6 space-y-4">
              <li v-for="s in STORIES" :key="s.id">
                <button type="button" class="proto-story" @click="startStory(s.id)">
                  <PersonAvatar :name="s.avatar" :size="48" />
                  <span class="min-w-0 flex-1 text-left">
                    <span class="flex flex-wrap items-center gap-2">
                      <span class="text-xl font-bold text-navy">{{ s.name }}</span>
                      <span class="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-sm font-semibold" :class="s.tagClass">
                        <component :is="s.icon" :size="14" aria-hidden="true" />{{ s.tag }}
                      </span>
                    </span>
                    <span class="mt-1 block text-base text-ink">{{ s.line }}</span>
                  </span>
                  <ChevronRight :size="22" class="shrink-0 text-accent" aria-hidden="true" />
                </button>
              </li>
            </ul>
            <div class="mt-auto pt-6">
              <p class="text-sm text-muted">{{ demo.disclaimer }}</p>
              <button type="button" class="link text-base" @click="openHelp">About this data</button>
            </div>
          </div>
          <div v-else-if="state.screen === 'send'" key="send" class="flex flex-1 flex-col">
            <PhoneSendMoney standalone :screen="state.sub" @update:screen="onSub" @go="go('paused')" @other-story="otherStory" @home="home" />
          </div>
          <div v-else-if="state.screen === 'paused'" key="paused" class="flex flex-1 flex-col">
            <PhonePaused standalone :screen="state.sub" @update:screen="onSub" @next="navigate({ ...fresh('views'), view: 'tommy' })" @other-story="otherStory" @home="home" />
          </div>
          <div v-else-if="state.screen === 'views'" key="views" class="flex flex-1 flex-col">
            <PhoneTwoViews
              standalone
              :view="state.view"
              :answer="state.answer"
              :screen="state.sub"
              @update:view="onView"
              @update:answer="onAnswer"
              @update:screen="onSub"
              @go="go('report')"
              @other-story="otherStory"
              @home="home"
            />
          </div>
          <div v-else-if="state.screen === 'report'" key="report" class="flex flex-1 flex-col">
            <PhoneReport standalone :screen="state.sub" @update:screen="onSub" @other-story="otherStory" @home="home" />
          </div>
          <div v-else-if="state.screen === 'legit'" key="legit" class="flex flex-1 flex-col">
            <PhoneLegit standalone :stage="state.sub" @update:stage="onSub" @other-story="otherStory" @home="home" />
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
            <p class="mt-3 text-base text-muted">
              Pick a story, then use the buttons on each screen. Back steps through your path; Home returns to the stories.
            </p>
            <p class="mt-3 text-base text-muted">Concept prototype for HuskyHack 2026. Not an official Sound Credit Union product.</p>
            <button type="button" class="btn btn-phone btn-secondary mt-5 text-lg" @click="closeHelp(); home()">Back to start</button>
          </div>
        </div>
      </Transition>
    </div>
  </PhoneFrame>
</template>
