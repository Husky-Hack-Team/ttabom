<script setup>
import { ChartColumn, Users, UserRound } from 'lucide-vue-next'
import demo from '~/data/demo.json'

const phases = [
  { icon: Users, weeks: 'Weeks 1–4', text: 'Volunteer members enroll trusted contacts. Wires and external transfers only.' },
  { icon: UserRound, weeks: 'Weeks 5–8', text: 'Add P2P pre-send checks. Train branch and Contact Center staff.' },
  { icon: ChartColumn, weeks: 'Weeks 9–12', text: 'Measure and decide: expand, adjust, or stop.' }
]

// Every baseline and target is an assumption to replace with Sound's numbers in week 1.
const metrics = [
  { name: '% of mismatches where the contact answers within 10 min', baseline: 'None today', target: '70%' },
  { name: 'Median minutes a legitimate payment is delayed', baseline: '60 min (held wire)', target: '10 min or less' },
  { name: '% of paused payments cancelled after a “not mine”', baseline: 'None today', target: '75%' },
  { name: '% of members who rate it fair or easy', baseline: 'Not measured', target: '85%' },
  { name: '% of scam reports made within 1 hour', baseline: '20%', target: '50%' }
]
</script>

<template>
  <section aria-labelledby="step-6-title">
    <p class="text-base font-semibold uppercase tracking-wider text-accent">Step 6 of 6</p>
    <h2 id="step-6-title" tabindex="-1" class="mt-2 text-[34px] focus:outline-none">Pilot: test it in 90 days</h2>
    <p class="mt-4 max-w-3xl text-lg">
      Start small with volunteers and the rails that can be held, then add P2P once staff are ready. Decide at week 12 using measures members and
      employees can both feel.
    </p>

    <ol class="mt-8 grid gap-5 md:grid-cols-3">
      <li v-for="(ph, i) in phases" :key="ph.weeks" class="card p-6">
        <component :is="ph.icon" :size="28" class="text-accent" aria-hidden="true" />
        <p class="mt-3 text-base font-semibold text-muted">Phase {{ i + 1 }}</p>
        <h3 class="text-2xl">{{ ph.weeks }}</h3>
        <p class="mt-2 text-lg">{{ ph.text }}</p>
      </li>
    </ol>

    <div class="card mt-8 overflow-x-auto p-2 sm:p-6">
      <table class="w-full min-w-[560px] text-left text-lg">
        <caption class="px-4 pb-3 pt-2 text-left text-xl font-bold text-navy sm:px-0">What we measure</caption>
        <thead>
          <tr class="border-b-2 border-line text-base text-muted">
            <th scope="col" class="px-4 py-3 font-semibold sm:pl-0">Metric</th>
            <th scope="col" class="px-4 py-3 font-semibold">Baseline</th>
            <th scope="col" class="px-4 py-3 font-semibold">Target</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in metrics" :key="m.name" class="border-b border-line last:border-0">
            <th scope="row" class="px-4 py-4 font-semibold sm:pl-0">{{ m.name }}</th>
            <td class="px-4 py-4">{{ m.baseline }} <span class="ml-1 rounded-full bg-page px-2 py-0.5 text-sm text-muted">assumption</span></td>
            <td class="px-4 py-4 font-semibold text-navy">{{ m.target }} <span class="ml-1 rounded-full bg-page px-2 py-0.5 text-sm font-medium text-muted">assumption</span></td>
          </tr>
        </tbody>
      </table>
    </div>
    <p class="mt-6 text-base text-muted">{{ demo.disclaimer }}</p>
  </section>
</template>
