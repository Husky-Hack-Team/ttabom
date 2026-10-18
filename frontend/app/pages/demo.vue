<script setup>
import { ANCHORS, DECISIONS, DISCLAIMER, errorText } from '~/utils/replay'
import { formatDate, formatTime, formatUsd } from '~/utils/format'
useHead({ title: 'ttabom · Demo mode', htmlAttrs: { lang: 'en' } })

const links = [
  {
    to: '/case',
    title: 'Employee case: Linda’s $8,500 wire',
    body: 'The case screen a branch employee sees while the wire is held and Tommy is asked.'
  },
  {
    to: '/replay',
    title: 'Data Replay',
    body: 'Our check run over every synthetic payment, side by side with what actually happened.'
  }
]
</script>

<template>
  <div class="demo-surface min-h-screen bg-neutral-50 text-neutral-900">
    <main class="mx-auto max-w-3xl px-6 py-12">
      <NuxtLink to="/" class="text-lg text-blue-700 underline-offset-4 hover:underline focus:outline-none focus-visible:ring-4 focus-visible:ring-blue-600/40 rounded">
        ← Dashboard
      </NuxtLink>
      <h1 class="mt-6 text-5xl font-semibold tracking-tight">Demo mode</h1>
      <p class="mt-4 text-xl text-neutral-700">Employee-facing screens for the Verified Contact Payment check.</p>
      <p class="mt-6 rounded-2xl border border-neutral-300 bg-white p-5 text-lg">
        <strong>Synthetic data.</strong> {{ DISCLAIMER }}
      </p>

      <ul class="mt-10 space-y-5">
        <li v-for="link in links" :key="link.to">
          <NuxtLink
            :to="link.to"
            class="block rounded-3xl bg-white p-7 shadow-sm ring-1 ring-neutral-200 transition hover:shadow-md focus:outline-none focus-visible:ring-4 focus-visible:ring-blue-600/50"
          >
            <span class="block text-2xl font-semibold">{{ link.title }} →</span>
            <span class="mt-2 block text-lg text-neutral-700">{{ link.body }}</span>
          </NuxtLink>
        </li>
      </ul>
    </main>
  </div>
</template>
