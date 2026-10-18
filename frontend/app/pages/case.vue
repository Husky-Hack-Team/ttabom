<script setup>
useHead({ title: 'ttabom · Employee case', htmlAttrs: { lang: 'en' } })

const apiBase = useApiBase()
const caseData = ref(null)
const error = ref('')

// Demo state. Tommy's answer is simulated ("No, it's not mine" is the truthful
// answer for this replayed scam); the member's choice is recorded locally only.
const contactAnswer = ref('')
const memberChoice = ref('')
const choiceAt = ref(null)

// Hold timer: the hold runs 4 hours from initiation. The demo clock starts the
// countdown when the case is opened so it can be watched live.
const HOLD_SECONDS = 4 * 60 * 60
const openedAt = ref(Date.now())
const now = ref(Date.now())
let tick
onMounted(async () => {
  tick = setInterval(() => (now.value = Date.now()), 1000)
  try {
    const res = await $fetch(`${apiBase}/api/replay/cases`, { query: { limit: 1 } })
    caseData.value = res.cases.find((c) => c.payment_id === res.featured) || res.cases[0] || null
    if (!caseData.value) error.value = 'No held payments in the replay.'
  } catch (err) {
    error.value = errorText(err, 'Could not load the case. Is the API running and the replay loaded?')
  }
})
onBeforeUnmount(() => clearInterval(tick))

const remaining = computed(() => Math.max(0, HOLD_SECONDS - Math.floor((now.value - openedAt.value) / 1000)))
const timerText = computed(() => {
  const s = remaining.value
  const pad = (n) => String(n).padStart(2, '0')
  return `${Math.floor(s / 3600)}:${pad(Math.floor((s % 3600) / 60))}:${pad(s % 60)}`
})
const timerSpoken = computed(() => {
  const m = Math.ceil(remaining.value / 60)
  return `${Math.floor(m / 60)} hours ${m % 60} minutes left on the hold`
})

const c = computed(() => caseData.value)
const asked = computed(() => c.value?.contact_asked)
const memberName = computed(() => ANCHORS[c.value?.synthetic_member_id] || c.value?.synthetic_member_id)
const initiation = computed(() => c.value?.recent_events?.find((e) => e.payment_id === c.value.payment_id))
const before = computed(() => (c.value?.recent_events || []).filter((e) => e.payment_id !== c.value.payment_id).slice(0, 5))

function showAnswer() {
  contactAnswer.value = "No, it's not mine"
}
function record(choice) {
  memberChoice.value = choice
  choiceAt.value = new Date()
}
</script>

<template>
  <div class="demo-surface min-h-screen bg-neutral-50 text-neutral-900">
    <main class="mx-auto max-w-4xl px-6 py-10">
      <NuxtLink to="/demo" class="rounded text-lg text-blue-700 underline-offset-4 hover:underline focus:outline-none focus-visible:ring-4 focus-visible:ring-blue-600/40">
        ← Demo mode
      </NuxtLink>

      <p v-if="error" role="alert" class="mt-6 rounded-2xl border-2 border-red-700 bg-red-50 p-5 text-lg text-red-900">
        <strong>Problem:</strong> {{ error }}
      </p>
      <p v-else-if="!c" class="mt-6 text-lg">Loading…</p>

      <template v-if="c">
        <header class="mt-4">
          <p class="text-lg text-neutral-600">Case {{ c.payment_id }} · {{ c.channel }} · {{ formatDate(c.event_timestamp) }}</p>
          <h1 class="mt-1 text-5xl font-semibold tracking-tight">{{ memberName }}’s {{ formatUsd(c.amount) }} {{ c.payment_rail.toLowerCase() }}</h1>
          <p class="mt-3 text-xl">
            <span aria-hidden="true">⏸ </span><strong>On hold</strong> {{ c.hold_window }}. {{ memberName }} makes the final decision.
          </p>
        </header>

        <section aria-labelledby="timer-heading" class="mt-8 flex flex-wrap items-center justify-between gap-6 rounded-3xl bg-white p-7 shadow-sm ring-1 ring-neutral-200">
          <div>
            <h2 id="timer-heading" class="text-lg text-neutral-600">Hold time left</h2>
            <p class="text-6xl font-semibold tabular-nums" role="timer" :aria-label="timerSpoken">{{ timerText }}</p>
            <p class="mt-1 text-lg text-neutral-700">
              The hold ends at {{ formatTime(c.hold_expires_at) }} on {{ formatDate(c.hold_expires_at).split(',').slice(0, 2).join(',') }}.
              The demo clock starts when you open the case.
            </p>
          </div>
        </section>

        <div class="mt-8 grid gap-6 md:grid-cols-2">
          <section aria-labelledby="pay-heading" class="rounded-3xl bg-white p-7 shadow-sm ring-1 ring-neutral-200">
            <h2 id="pay-heading" class="text-2xl font-semibold">The payment</h2>
            <dl class="mt-4 space-y-3 text-lg">
              <div><dt class="text-neutral-600">Amount</dt><dd class="text-2xl font-semibold">{{ formatUsd(c.amount) }}</dd></div>
              <div v-if="asked?.shows"><dt class="text-neutral-600">To</dt><dd>{{ asked.shows.bank }} {{ asked.shows.account_masked }} ({{ c.recipient_id }}, {{ c.recipient_status }} recipient)</dd></div>
              <div v-if="initiation"><dt class="text-neutral-600">History</dt><dd>First {{ c.payment_rail.toLowerCase() }} in {{ Number(initiation.days_since_last_same_rail).toLocaleString('en-US') }} days · {{ initiation.amount_vs_member_baseline }}</dd></div>
            </dl>
          </section>

          <section aria-labelledby="why-heading" class="rounded-3xl bg-white p-7 shadow-sm ring-1 ring-neutral-200">
            <h2 id="why-heading" class="text-2xl font-semibold">Why it’s paused</h2>
            <ul class="mt-4 list-disc space-y-2 pl-5 text-lg">
              <li v-for="(r, i) in c.reasons" :key="i">{{ r }}</li>
            </ul>
          </section>
        </div>

        <section v-if="asked" aria-labelledby="contact-heading" class="mt-6 rounded-3xl bg-white p-7 shadow-sm ring-1 ring-neutral-200" aria-live="polite">
          <h2 id="contact-heading" class="text-2xl font-semibold">{{ asked.name }}’s question</h2>
          <p class="mt-2 text-lg text-neutral-700">
            Sent by text to {{ asked.masked }}, on file for {{ asked.on_file_days }} days. {{ asked.name }} can answer yes or no, and can’t approve or cancel anything.
          </p>
          <div class="mt-4 rounded-2xl bg-neutral-100 p-5 text-lg">
            <p>What {{ asked.name }} sees: <strong>{{ asked.shows.amount }}</strong> to <strong>{{ asked.shows.bank }}</strong> account <strong>{{ asked.shows.account_masked }}</strong>. Is this your account?</p>
            <p class="mt-1 text-neutral-700">Choices: “{{ asked.answers[0] }}” or “{{ asked.answers[1] }}”</p>
          </div>
          <p class="mt-4 text-xl">
            <strong>Answer:</strong>
            <span v-if="contactAnswer"><span aria-hidden="true">✕ </span>{{ contactAnswer }}</span>
            <span v-else>Waiting for {{ asked.name }}</span>
          </p>
        </section>

        <section aria-labelledby="next-heading" class="mt-6 rounded-3xl bg-white p-7 shadow-sm ring-1 ring-neutral-200" aria-live="polite">
          <h2 id="next-heading" class="text-2xl font-semibold">What to say to {{ memberName }}</h2>
          <ul class="mt-3 list-disc space-y-2 pl-5 text-lg">
            <li>“Has anyone asked you to keep this payment secret, or told you it’s urgent?”</li>
            <li>“Let’s call {{ asked?.name || 'them' }} together on a number you already know, not one from the caller.”</li>
            <li>“It’s your money and your decision. If you send it, we’ll help you right away if anything goes wrong.”</li>
          </ul>

          <p v-if="memberChoice === 'cancel'" class="mt-5 rounded-2xl bg-neutral-100 p-5 text-xl">
            <span aria-hidden="true">✓ </span><strong>Wire cancelled</strong> at {{ formatTime(choiceAt) }}. No money left Sound.
          </p>
          <p v-else-if="memberChoice === 'send'" class="mt-5 rounded-2xl bg-neutral-100 p-5 text-xl">
            <span aria-hidden="true">● </span><strong>Sent anyway</strong> at {{ formatTime(choiceAt) }}, at {{ memberName }}’s request. Logged.
            Recovery path: a recall request goes to {{ asked?.shows?.bank || 'the receiving bank' }} now, and we’ll call {{ memberName }} tomorrow.
          </p>

          <!-- At most three buttons on this screen. -->
          <div v-if="!memberChoice" class="mt-6 flex flex-wrap gap-4">
            <button
              v-if="asked && !contactAnswer"
              type="button"
              class="rounded-full bg-white px-6 py-3 text-lg font-semibold ring-2 ring-neutral-900 focus:outline-none focus-visible:ring-4 focus-visible:ring-blue-600/50"
              @click="showAnswer"
            >
              Show {{ asked.name }}’s answer (demo)
            </button>
            <button
              type="button"
              class="rounded-full bg-neutral-900 px-6 py-3 text-lg font-semibold text-white focus:outline-none focus-visible:ring-4 focus-visible:ring-blue-600/50 focus-visible:ring-offset-2"
              @click="record('cancel')"
            >
              {{ memberName }} cancels the wire
            </button>
            <button
              type="button"
              class="rounded-full bg-white px-6 py-3 text-lg font-semibold ring-2 ring-neutral-400 focus:outline-none focus-visible:ring-4 focus-visible:ring-blue-600/50"
              @click="record('send')"
            >
              {{ memberName }} sends anyway
            </button>
          </div>
        </section>

        <section v-if="before.length" aria-labelledby="before-heading" class="mt-6 rounded-3xl bg-white p-7 shadow-sm ring-1 ring-neutral-200">
          <h2 id="before-heading" class="text-2xl font-semibold">Before this payment</h2>
          <ol class="mt-3 space-y-2 text-lg">
            <li v-for="e in before" :key="e.event_id">
              <time :datetime="e.event_timestamp" class="text-neutral-600">{{ formatDate(e.event_timestamp) }}</time> · {{ e.event_type }} · {{ e.channel }}
            </li>
          </ol>
        </section>

        <p class="mt-8 text-lg text-neutral-600"><strong>Synthetic data.</strong> {{ DISCLAIMER }}</p>
      </template>
    </main>
  </div>
</template>
