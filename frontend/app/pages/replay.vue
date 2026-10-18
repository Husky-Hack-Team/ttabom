<script setup>
import { useApi } from '~/composables/useApi'
import { ANCHORS, DECISIONS, DISCLAIMER, errorText } from '~/utils/replay'
import { formatDate, formatTime, formatUsd } from '~/utils/format'
useHead({ title: 'ttabom · Data Replay', htmlAttrs: { lang: 'en' } })

const route = useRoute()
const router = useRouter()

const FILTERS = [
  { value: 'all', label: 'All members' },
  { value: 'anchor', label: 'Anchors' },
  { value: 'lookalike', label: 'Look-alikes' },
  { value: 'scam', label: 'Scam journeys' },
  { value: 'routine', label: 'Routine' }
]
const GROUP_LABEL = { anchor: 'Anchor', lookalike: 'Look-alike', scam: 'Scam journey', routine: 'Routine' }
// Non-payment events worth a line on the timeline.
const CONTEXT_EVENTS = new Set([
  'Password Reset', 'Phone Change', 'Email Change', 'Address Change', 'Recipient Added', 'Branch Visit',
  'Contact Center Call', 'Scam Reported', 'Case Created', 'Recovery Request', 'Funds Recovered', 'Trusted Contact Enrolled'
])

const filter = ref(FILTERS.some((f) => f.value === route.query.filter) ? route.query.filter : 'all')
const memberId = ref(typeof route.query.member === 'string' ? route.query.member : 'M1001')
const metrics = ref(null)
const members = ref([])
const detail = ref(null)
const error = ref('')
const loadingMember = ref(false)

async function loadMetrics() {
  try {
    metrics.value = (await useApi('/replay/metrics')).metrics
  } catch (err) {
    error.value = errorText(err, 'Could not load the replay. Is the API running and the replay loaded?')
  }
}

async function loadMembers() {
  try {
    members.value = (await useApi('/replay/members', { query: { filter: filter.value } })).members
    if (members.value.length && !members.value.some((m) => m.synthetic_member_id === memberId.value)) {
      memberId.value = members.value[0].synthetic_member_id
    }
  } catch (err) {
    error.value = errorText(err, 'Could not load members.')
  }
}

async function loadMember() {
  if (!memberId.value) return
  loadingMember.value = true
  try {
    detail.value = await useApi(`/replay/members/${memberId.value}`)
  } catch (err) {
    error.value = errorText(err, `Could not load ${memberId.value}.`)
  } finally {
    loadingMember.value = false
  }
}

watch(filter, loadMembers)
watch(memberId, loadMember)
watch([filter, memberId], () => router.replace({ query: { filter: filter.value, member: memberId.value } }))
onMounted(async () => {
  await Promise.all([loadMetrics(), loadMembers()])
  await loadMember()
})

// Timeline: each payment's initiation row joined to our decision, plus context events.
const timeline = computed(() => {
  if (!detail.value) return []
  const byPayment = Object.fromEntries(detail.value.decisions.map((d) => [d.payment_id, d]))
  return detail.value.events
    .filter((e) => e.event_type === 'Payment Initiated' || CONTEXT_EVENTS.has(e.event_type))
    .map((e) => ({ ...e, decision: e.event_type === 'Payment Initiated' ? byPayment[e.payment_id] : null }))
})

const summary = computed(() => detail.value?.summary)
const memberName = (m) => (m.anchor_persona ? `${m.synthetic_member_id} · ${m.anchor_persona}` : m.synthetic_member_id)
const actualText = (d) => {
  const parts = [d.actual_final_status]
  if (d.actual_member_response) parts.push(`member: ${d.actual_member_response}`)
  parts.push(d.actual_intervened ? 'Sound intervened' : 'no intervention')
  return parts.join(' · ')
}
</script>

<template>
  <div class="demo-surface min-h-screen bg-neutral-50 text-neutral-900">
    <main class="mx-auto max-w-5xl px-6 py-10">
      <NuxtLink to="/demo" class="rounded text-lg text-blue-700 underline-offset-4 hover:underline focus:outline-none focus-visible:ring-4 focus-visible:ring-blue-600/40">
        ← Demo mode
      </NuxtLink>
      <h1 class="mt-4 text-5xl font-semibold tracking-tight">Data Replay</h1>
      <p class="mt-3 text-xl text-neutral-700">
        Our check, computed only from what Sound could see when each payment started, next to what actually happened.
      </p>

      <p v-if="error" role="alert" class="mt-6 rounded-2xl border-2 border-red-700 bg-red-50 p-5 text-lg text-red-900">
        <strong>Problem:</strong> {{ error }}
      </p>

      <!-- Metrics panel -->
      <section aria-labelledby="metrics-heading" class="mt-8 rounded-3xl bg-white p-7 shadow-sm ring-1 ring-neutral-200">
        <h2 id="metrics-heading" class="text-2xl font-semibold">Replay results</h2>
        <p class="mt-2 rounded-xl bg-amber-50 p-4 text-lg ring-1 ring-amber-300">
          <strong>⚠ Synthetic data.</strong> {{ DISCLAIMER }}
        </p>
        <dl v-if="metrics" class="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <dt class="text-lg text-neutral-600">Scam payments paused before money moved</dt>
            <dd class="text-4xl font-semibold tabular-nums">
              {{ metrics.scam.payments_paused_before_money_moved }} of {{ metrics.scam.payments }}
            </dd>
          </div>
          <div>
            <dt class="text-lg text-neutral-600">Expected scam dollars stopped (80% cancel after “not mine”)</dt>
            <dd class="text-4xl font-semibold tabular-nums">{{ formatUsd(metrics.scam.expected_dollars_stopped) }}</dd>
            <dd class="text-lg text-neutral-700">
              At 50%: {{ formatUsd(metrics.scam.expected_dollars_stopped_by_cancel_rate['0.5']) }} ·
              at 100%: {{ formatUsd(metrics.scam.expected_dollars_stopped_by_cancel_rate['1.0']) }}
            </dd>
          </div>
          <div>
            <dt class="text-lg text-neutral-600">Scam dollars actually sent (Member Key)</dt>
            <dd class="text-4xl font-semibold tabular-nums">{{ formatUsd(metrics.key.dollars_sent) }}</dd>
            <dd class="text-lg text-neutral-700">of {{ formatUsd(metrics.key.dollars_attempted) }} attempted</dd>
          </div>
          <div>
            <dt class="text-lg text-neutral-600">Median minutes, incident to intervention</dt>
            <dd class="text-4xl font-semibold tabular-nums">{{ metrics.time_to_intervention_minutes.median_ours }}</dd>
            <dd class="text-lg text-neutral-700">
              Data: {{ metrics.time_to_intervention_minutes.median_key }} min; {{ metrics.time_to_intervention_minutes.scam_members_key_never_intervened }} scam members never reached
            </dd>
          </div>
          <div>
            <dt class="text-lg text-neutral-600">Look-alike friction</dt>
            <dd class="text-4xl font-semibold tabular-nums">{{ metrics.lookalikes.friction_minutes_per_member }} min</dd>
            <dd class="text-lg text-neutral-700">per legitimate look-alike member ({{ metrics.lookalikes.members }} members)</dd>
          </div>
          <div>
            <dt class="text-lg text-neutral-600">Routine members interrupted</dt>
            <dd class="text-4xl font-semibold tabular-nums">{{ metrics.routine.members_flagged }} of {{ metrics.routine.members }}</dd>
            <dd class="text-lg text-neutral-700">{{ metrics.routine.friction_minutes }} min in total</dd>
          </div>
        </dl>
        <p v-else-if="!error" class="mt-6 text-lg">Loading…</p>
      </section>

      <!-- Pickers -->
      <section aria-labelledby="pick-heading" class="mt-8">
        <h2 id="pick-heading" class="sr-only">Choose a member</h2>
        <fieldset>
          <legend class="text-lg font-medium">Show</legend>
          <div class="mt-3 flex flex-wrap gap-3">
            <label
              v-for="f in FILTERS"
              :key="f.value"
              class="cursor-pointer rounded-full px-5 py-2.5 text-lg ring-1 has-[:focus-visible]:ring-4 has-[:focus-visible]:ring-blue-600/50"
              :class="filter === f.value ? 'bg-neutral-900 text-white ring-neutral-900 font-semibold' : 'bg-white ring-neutral-300'"
            >
              <input v-model="filter" type="radio" name="filter" :value="f.value" class="sr-only">
              <span aria-hidden="true">{{ filter === f.value ? '✓ ' : '' }}</span>{{ f.label }}
            </label>
          </div>
        </fieldset>
        <label for="member" class="mt-6 block text-lg font-medium">Member</label>
        <select
          id="member"
          v-model="memberId"
          class="mt-2 block w-full max-w-md rounded-xl border border-neutral-400 bg-white px-4 py-3 text-lg focus:outline-none focus-visible:ring-4 focus-visible:ring-blue-600/40"
        >
          <option v-for="m in members" :key="m.synthetic_member_id" :value="m.synthetic_member_id">
            {{ memberName(m) }} · {{ GROUP_LABEL[m.member_group] }} · {{ m.scenario_subtype }}
          </option>
        </select>
      </section>

      <!-- Member summary -->
      <section v-if="summary" aria-labelledby="member-heading" class="mt-8 rounded-3xl bg-white p-7 shadow-sm ring-1 ring-neutral-200" aria-live="polite">
        <h2 id="member-heading" class="text-3xl font-semibold">
          {{ summary.synthetic_member_id }}<span v-if="summary.anchor_persona"> · {{ summary.anchor_persona }}</span>
        </h2>
        <p class="mt-1 text-lg text-neutral-700">
          {{ GROUP_LABEL[summary.member_group] }} · {{ summary.scenario_type }} · {{ summary.scenario_subtype }}
          <span class="text-neutral-500">(labels from the Member Key; the check never sees them)</span>
        </p>
        <dl class="mt-5 grid gap-5 sm:grid-cols-3">
          <div>
            <dt class="text-lg text-neutral-600">Scam payments paused</dt>
            <dd class="text-2xl font-semibold tabular-nums">{{ summary.scam_payments_paused }} of {{ summary.scam_payments }}</dd>
          </div>
          <div>
            <dt class="text-lg text-neutral-600">Dollars paused vs. sent in the data</dt>
            <dd class="text-2xl font-semibold tabular-nums">{{ formatUsd(summary.scam_dollars_paused) }} / {{ formatUsd(summary.key_dollars_sent) }}</dd>
          </div>
          <div>
            <dt class="text-lg text-neutral-600">Friction added</dt>
            <dd class="text-2xl font-semibold tabular-nums">{{ summary.friction_minutes }} min</dd>
          </div>
          <div v-if="summary.incident_start">
            <dt class="text-lg text-neutral-600">Minutes to intervention: ours / data</dt>
            <dd class="text-2xl font-semibold tabular-nums">
              {{ summary.our_minutes_to_intervention ?? 'none' }} / {{ summary.key_minutes_to_intervention ?? 'never' }}
            </dd>
          </div>
          <div>
            <dt class="text-lg text-neutral-600">Outcome in the data</dt>
            <dd class="text-2xl font-semibold">{{ summary.key_journey_outcome }}</dd>
          </div>
        </dl>
      </section>

      <!-- Timeline -->
      <section v-if="detail" aria-labelledby="timeline-heading" class="mt-8">
        <h2 id="timeline-heading" class="text-3xl font-semibold">Timeline</h2>
        <p v-if="loadingMember" class="mt-3 text-lg">Loading…</p>
        <ol class="mt-6 border-l-2 border-neutral-300 pl-6">
          <li v-for="e in timeline" :key="e.event_id" class="relative pb-8">
            <span class="absolute -left-[33px] top-2 h-4 w-4 rounded-full border-2 border-neutral-500 bg-white" aria-hidden="true" />
            <p class="text-lg text-neutral-600"><time :datetime="e.event_timestamp">{{ formatDate(e.event_timestamp) }}</time> · {{ e.channel }}</p>
            <template v-if="e.decision">
              <h3 class="text-xl font-semibold">
                {{ formatUsd(e.amount) }} {{ e.payment_rail }} to {{ e.recipient_id || 'cash' }}
                <span class="font-normal text-neutral-600">({{ e.recipient_status }}, {{ e.payment_id }})</span>
              </h3>
              <p v-if="e.decision.is_scam_payment" class="mt-1 inline-block rounded-md bg-neutral-900 px-2 py-0.5 text-base font-semibold text-white">
                Scam payment (Member Key)
              </p>
              <div class="mt-3 grid gap-4 md:grid-cols-2">
                <div class="rounded-2xl bg-white p-5 ring-1 ring-neutral-200">
                  <p class="text-base font-semibold uppercase tracking-wide text-neutral-500">Our check</p>
                  <p class="mt-1 text-xl font-semibold">
                    <span aria-hidden="true">{{ DECISIONS[e.decision.decision].symbol }} </span>{{ DECISIONS[e.decision.decision].label }}
                  </p>
                  <ul class="mt-2 list-disc space-y-1 pl-5 text-lg">
                    <li v-for="(r, i) in e.decision.reasons" :key="i">{{ r }}</li>
                  </ul>
                  <p v-if="e.decision.contact_asked" class="mt-2 text-lg">
                    <strong>Asked:</strong> {{ e.decision.contact_asked.name || 'the member' }} by {{ e.decision.contact_asked.channel }}
                    {{ e.decision.contact_asked.masked }}<span v-if="e.decision.simulated_answer">, simulated answer “{{ e.decision.simulated_answer }}”</span>
                  </p>
                  <p class="mt-2 text-lg text-neutral-700">
                    Pause: {{ e.decision.hold_window || 'none' }} · Friction: {{ e.decision.friction_minutes }} min
                  </p>
                </div>
                <div class="rounded-2xl bg-neutral-100 p-5">
                  <p class="text-base font-semibold uppercase tracking-wide text-neutral-500">What actually happened</p>
                  <p class="mt-1 text-xl font-semibold">{{ actualText(e.decision) }}</p>
                </div>
              </div>
            </template>
            <p v-else class="text-xl">{{ e.event_type }}<span v-if="e.recipient_id"> · {{ e.recipient_id }}</span></p>
          </li>
        </ol>
      </section>
    </main>
  </div>
</template>
