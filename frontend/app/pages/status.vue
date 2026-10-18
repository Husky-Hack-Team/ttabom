<script setup>
import { useApi } from '~/composables/useApi'
useHead({ title: 'ttabom · Status' })

const state = ref('checking') // checking | ok | fail
const ms = ref(null)
const detail = ref('')

async function check() {
  state.value = 'checking'
  detail.value = ''
  const t0 = performance.now()
  try {
    const res = await useApi('/health')
    ms.value = Math.round(performance.now() - t0)
    state.value = res?.ok ? 'ok' : 'fail'
    if (!res?.ok) detail.value = 'Unexpected response from /api/health.'
  } catch (err) {
    ms.value = Math.round(performance.now() - t0)
    state.value = 'fail'
    detail.value = err?.statusCode ? `HTTP ${err.statusCode}` : err?.message || 'Network error'
  }
}
onMounted(check)
</script>

<template>
  <main class="mx-auto max-w-xl px-4 py-16">
    <h1 class="text-[34px]">Backend status</h1>
    <p class="mt-2 text-lg text-muted">GET /api/health through the frontend’s proxy.</p>
    <div class="card mt-8 p-6" aria-live="polite">
      <p class="text-2xl font-bold" :class="state === 'ok' ? 'text-ok' : state === 'fail' ? 'text-alert' : 'text-navy'">
        <span aria-hidden="true">{{ state === 'ok' ? '✓' : state === 'fail' ? '✕' : '…' }} </span>
        {{ state === 'ok' ? 'OK' : state === 'fail' ? 'FAIL' : 'Checking…' }}
      </p>
      <p v-if="ms !== null" class="mt-1 text-lg">{{ ms }} ms</p>
      <p v-if="detail" class="mt-1 text-lg text-alert">{{ detail }}</p>
      <button type="button" class="btn btn-secondary mt-6" @click="check">Check again</button>
    </div>
  </main>
</template>
