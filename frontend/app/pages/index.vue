<script setup>
const config = useRuntimeConfig()
const apiBase = config.public.apiBase.replace(/\/+$/, '')

useHead({ title: 'ttabom · Dashboard', htmlAttrs: { lang: 'en' } })

const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })
const dateFormat = new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeStyle: 'short' })
const formatUsd = (value) => usd.format(Number(value))
const formatDate = (value) => dateFormat.format(new Date(value))

const balance = ref(null)
const transactions = ref([])
const loading = ref(true)
const loadError = ref('')

async function loadData() {
  loading.value = true
  loadError.value = ''
  try {
    const [balanceRes, txRes] = await Promise.all([
      $fetch(`${apiBase}/api/balance`),
      $fetch(`${apiBase}/api/transactions`)
    ])
    balance.value = balanceRes.balance
    transactions.value = txRes
  } catch (err) {
    loadError.value = err?.data?.detail || 'Could not load your account. Is the API running?'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)

const form = reactive({ description: '', amount: '', direction: 'out' })
const errors = reactive({ description: '', amount: '' })
const submitError = ref('')
const submitStatus = ref('')
const submitting = ref(false)

function validate() {
  errors.description = form.description.trim() ? '' : 'Enter a description.'
  const amount = Number(form.amount)
  if (form.amount === '' || Number.isNaN(amount)) {
    errors.amount = 'Enter an amount.'
  } else if (amount <= 0) {
    errors.amount = 'Amount must be greater than zero.'
  } else if (!/^\d+(\.\d{1,2})?$/.test(String(form.amount))) {
    errors.amount = 'Use at most two decimal places.'
  } else {
    errors.amount = ''
  }
  return !errors.description && !errors.amount
}

async function submit() {
  submitError.value = ''
  submitStatus.value = ''
  if (!validate()) return

  const amount = Number(form.amount) * (form.direction === 'out' ? -1 : 1)
  submitting.value = true
  try {
    await $fetch(`${apiBase}/api/transactions`, {
      method: 'POST',
      body: { description: form.description.trim(), amount }
    })
    form.description = ''
    form.amount = ''
    submitStatus.value = 'Transaction added.'
    await loadData()
  } catch (err) {
    const detail = err?.data?.detail
    submitError.value = Array.isArray(detail)
      ? detail.map((d) => d.msg).join(' ')
      : detail || 'Could not add the transaction. Please try again.'
  } finally {
    submitting.value = false
  }
}

const inputClass =
  'mt-1 block w-full rounded-lg border border-slate-400 bg-white px-3 py-2 text-base text-slate-900 ' +
  'focus:outline-none focus-visible:ring-4 focus-visible:ring-blue-600/40 focus-visible:border-blue-700 ' +
  'aria-[invalid=true]:border-red-700'
</script>

<template>
  <div class="min-h-screen bg-slate-100 text-slate-900">
    <header class="bg-blue-900 text-white">
      <div class="mx-auto flex max-w-3xl items-center justify-between px-4 py-4">
        <p class="text-lg font-semibold">ttabom</p>
        <NuxtLink to="/demo" class="rounded font-medium underline underline-offset-4 focus:outline-none focus-visible:ring-4 focus-visible:ring-white/60">
          Demo mode
        </NuxtLink>
      </div>
    </header>

    <main class="mx-auto max-w-3xl space-y-6 px-4 py-6">
      <h1 class="sr-only">Account dashboard</h1>

      <p v-if="loadError" role="alert" class="rounded-lg border border-red-700 bg-red-50 p-4 text-red-800">
        {{ loadError }}
        <button
          type="button"
          class="ml-2 font-semibold underline focus:outline-none focus-visible:ring-4 focus-visible:ring-red-600/40 rounded"
          @click="loadData"
        >
          Retry
        </button>
      </p>

      <section aria-labelledby="balance-heading" class="rounded-2xl bg-blue-800 p-6 text-white shadow">
        <h2 id="balance-heading" class="text-sm font-medium text-blue-100">Available balance</h2>
        <p class="mt-2 text-4xl font-bold tabular-nums" aria-live="polite">
          <span v-if="balance !== null">{{ formatUsd(balance) }}</span>
          <span v-else-if="loading">Loading…</span>
          <span v-else>—</span>
        </p>
      </section>

      <div class="grid gap-6 md:grid-cols-2">
        <section aria-labelledby="add-heading" class="rounded-2xl bg-white p-6 shadow">
          <h2 id="add-heading" class="text-lg font-semibold">Add transaction</h2>

          <form class="mt-4 space-y-4" novalidate @submit.prevent="submit">
            <div>
              <label for="description" class="block text-sm font-medium">Description</label>
              <input
                id="description"
                v-model="form.description"
                type="text"
                maxlength="200"
                autocomplete="off"
                :aria-invalid="errors.description ? 'true' : 'false'"
                :aria-describedby="errors.description ? 'description-error' : undefined"
                :class="inputClass"
              >
              <p v-if="errors.description" id="description-error" role="alert" class="mt-1 text-sm text-red-700">
                {{ errors.description }}
              </p>
            </div>

            <div>
              <label for="amount" class="block text-sm font-medium">Amount (USD)</label>
              <input
                id="amount"
                v-model="form.amount"
                type="text"
                inputmode="decimal"
                placeholder="0.00"
                :aria-invalid="errors.amount ? 'true' : 'false'"
                :aria-describedby="errors.amount ? 'amount-error' : undefined"
                :class="inputClass"
              >
              <p v-if="errors.amount" id="amount-error" role="alert" class="mt-1 text-sm text-red-700">
                {{ errors.amount }}
              </p>
            </div>

            <fieldset>
              <legend class="text-sm font-medium">Type</legend>
              <div class="mt-1 flex gap-6">
                <label class="flex items-center gap-2">
                  <input v-model="form.direction" type="radio" value="out" class="h-4 w-4 accent-blue-700 focus:outline-none focus-visible:ring-4 focus-visible:ring-blue-600/40">
                  Money out
                </label>
                <label class="flex items-center gap-2">
                  <input v-model="form.direction" type="radio" value="in" class="h-4 w-4 accent-blue-700 focus:outline-none focus-visible:ring-4 focus-visible:ring-blue-600/40">
                  Money in
                </label>
              </div>
            </fieldset>

            <p v-if="submitError" role="alert" class="rounded-lg border border-red-700 bg-red-50 p-3 text-sm text-red-800">
              {{ submitError }}
            </p>
            <p v-if="submitStatus" role="status" class="text-sm text-green-800">{{ submitStatus }}</p>

            <button
              type="submit"
              :disabled="submitting"
              class="w-full rounded-lg bg-blue-700 px-4 py-2 font-semibold text-white hover:bg-blue-800 disabled:opacity-60 focus:outline-none focus-visible:ring-4 focus-visible:ring-blue-600/40 focus-visible:ring-offset-2"
            >
              {{ submitting ? 'Adding…' : 'Add transaction' }}
            </button>
          </form>
        </section>

        <section aria-labelledby="activity-heading" class="rounded-2xl bg-white p-6 shadow">
          <h2 id="activity-heading" class="text-lg font-semibold">Recent activity</h2>

          <p v-if="loading && !transactions.length" class="mt-4 text-slate-700">Loading…</p>
          <p v-else-if="!transactions.length" class="mt-4 text-slate-700">No transactions yet.</p>

          <ul v-else class="mt-4 divide-y divide-slate-200">
            <li v-for="tx in transactions" :key="tx.id" class="flex items-start justify-between gap-4 py-3">
              <div class="min-w-0">
                <p class="truncate font-medium">{{ tx.description }}</p>
                <p class="text-sm text-slate-700">
                  <time :datetime="tx.created_at">{{ formatDate(tx.created_at) }}</time>
                </p>
              </div>
              <p
                class="shrink-0 font-semibold tabular-nums"
                :class="Number(tx.amount) < 0 ? 'text-slate-900' : 'text-green-800'"
              >
                <span class="sr-only">{{ Number(tx.amount) < 0 ? 'Debit' : 'Credit' }}:</span>
                {{ Number(tx.amount) < 0 ? '−' : '+' }}{{ formatUsd(Math.abs(Number(tx.amount))) }}
              </p>
            </li>
          </ul>
        </section>
      </div>
    </main>
  </div>
</template>
