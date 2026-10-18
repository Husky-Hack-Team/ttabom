<script setup>
import { ArrowLeft, ArrowRight, ShieldCheck } from 'lucide-vue-next'

const STEPS = [
  { n: 1, label: 'Signal', component: resolveComponent('StepSignal') },
  { n: 2, label: 'Intervention', component: resolveComponent('StepIntervention') },
  { n: 3, label: 'Two views', component: resolveComponent('StepTwoViews') },
  { n: 4, label: 'Legit path', component: resolveComponent('StepLegit') },
  { n: 5, label: 'Report', component: resolveComponent('StepReport') },
  { n: 6, label: 'Pilot', component: resolveComponent('StepPilot') }
]

const step = ref(1)
const walkthrough = ref(null)
const current = computed(() => STEPS[step.value - 1])

function go(n, { scroll = true } = {}) {
  step.value = Math.min(6, Math.max(1, n))
  if (import.meta.client) history.replaceState(null, '', `#step-${step.value}`)
  if (!scroll) return
  nextTick(() => {
    walkthrough.value?.scrollIntoView({ block: 'start' })
    // Move focus to the new step's heading for keyboard and screen-reader users.
    setTimeout(() => document.getElementById(`step-${step.value}-title`)?.focus({ preventScroll: true }), 220)
  })
}

function onKey(e) {
  if (e.altKey || e.ctrlKey || e.metaKey || e.shiftKey) return
  const t = e.target
  if (t instanceof HTMLElement && (t.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(t.tagName))) return
  if (e.key === 'ArrowRight' && step.value < 6) go(step.value + 1)
  if (e.key === 'ArrowLeft' && step.value > 1) go(step.value - 1)
}

onMounted(() => {
  const m = location.hash.match(/^#step-([1-6])$/)
  if (m) go(Number(m[1]))
  window.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <div class="min-h-screen bg-page">
    <a href="#walkthrough" class="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2">
      Skip to the walkthrough
    </a>

    <header class="bg-navy text-white">
      <div class="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-x-4 gap-y-2 px-4 py-3 sm:px-8">
        <p class="flex items-center gap-2 whitespace-nowrap font-display text-2xl tracking-wide">
          <ShieldCheck :size="26" aria-hidden="true" />Demo Prototype
        </p>
        <p class="whitespace-nowrap rounded-full border border-white/40 px-3 py-1 text-sm font-semibold sm:text-base">Demo prototype · synthetic data</p>
      </div>
    </header>

    <main>
      <section class="relative overflow-hidden">
        <!-- Soft shapes, decorative only. -->
        <div class="pointer-events-none absolute -right-24 -top-24 h-80 w-80 rounded-full bg-accent-soft" aria-hidden="true" />
        <div class="pointer-events-none absolute -bottom-20 right-40 h-48 w-48 rounded-full bg-white" aria-hidden="true" />
        <div class="relative mx-auto max-w-7xl px-4 py-16 sm:px-8 sm:py-24">
          <h1 class="max-w-3xl text-[40px] sm:text-[56px]">Stop the scam before the money moves</h1>
          <p class="mt-5 max-w-2xl text-xl text-muted">
            We check that the account you’re paying really belongs to the person you think you’re paying.
          </p>
          <div class="mt-8 flex flex-wrap gap-4">
            <button type="button" class="btn btn-primary text-lg" @click="go(1)">Start the walkthrough</button>
            <button type="button" class="btn btn-secondary text-lg" @click="go(6)">See the pilot plan</button>
          </div>
        </div>
      </section>

      <div id="walkthrough" ref="walkthrough" class="scroll-mt-0">
        <nav class="sticky top-0 z-30 border-y border-line bg-white/95 backdrop-blur" aria-label="Walkthrough steps">
          <div class="mx-auto flex max-w-7xl items-center gap-2 px-4 py-3 sm:gap-3 sm:px-8">
            <button type="button" class="btn btn-secondary w-12 shrink-0 px-0 sm:w-auto sm:px-4" :disabled="step === 1" :class="step === 1 ? 'opacity-40' : ''" @click="go(step - 1)">
              <ArrowLeft :size="20" aria-hidden="true" /><span class="sr-only sm:not-sr-only">Back</span>
            </button>
            <ol class="flex flex-1 items-center justify-between gap-0.5 sm:justify-center sm:gap-2">
              <li v-for="s in STEPS" :key="s.n">
                <button
                  type="button"
                  class="flex min-h-[44px] min-w-[36px] items-center justify-center gap-2 rounded-full px-1 text-base font-semibold sm:px-3"
                  :class="step === s.n ? 'bg-accent text-white' : 'text-muted hover:text-navy'"
                  :aria-current="step === s.n ? 'step' : undefined"
                  @click="go(s.n)"
                >
                  <span
                    class="flex h-7 w-7 items-center justify-center rounded-full border-2 text-sm"
                    :class="step === s.n ? 'border-white' : 'border-line'"
                  >{{ s.n }}</span>
                  <span :class="step === s.n ? 'hidden sm:inline' : 'hidden xl:inline'">{{ s.label }}</span>
                </button>
              </li>
            </ol>
            <button type="button" class="btn btn-primary w-12 shrink-0 px-0 sm:w-auto sm:px-4" :disabled="step === 6" :class="step === 6 ? 'opacity-40' : ''" @click="go(step + 1)">
              <span class="sr-only sm:not-sr-only">Next</span><ArrowRight :size="20" aria-hidden="true" />
            </button>
          </div>
        </nav>

        <div class="mx-auto max-w-7xl px-4 py-12 sm:px-8 sm:py-16">
          <p class="sr-only" aria-live="polite">Step {{ step }} of 6: {{ current.label }}</p>
          <Transition name="fade-slide" mode="out-in">
            <component :is="current.component" :key="step" @go="go" />
          </Transition>
          <p class="mt-12 text-base text-muted">Use the arrow keys or the step bar to move between steps.</p>
        </div>
      </div>
    </main>

    <footer class="border-t border-line bg-white">
      <div class="mx-auto max-w-7xl px-4 py-8 text-base text-muted sm:px-8">
        Concept prototype for HuskyHack 2026. Not an official Sound Credit Union product.
      </div>
    </footer>
  </div>
</template>
