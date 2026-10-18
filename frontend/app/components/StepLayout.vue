<script setup>
import { ArrowRight, Database } from 'lucide-vue-next'

defineProps({
  number: { type: Number, required: true },
  title: { type: String, required: true },
  data: { type: Array, default: () => [] },
  next: { type: String, default: '' },
  // Wide steps put the explanation above and give the right side the full width.
  wide: { type: Boolean, default: false }
})
defineEmits(['next'])
</script>

<template>
  <section :aria-labelledby="`step-${number}-title`" class="grid items-start gap-10" :class="wide ? '' : 'lg:grid-cols-[minmax(0,1fr)_auto] lg:gap-14'">
    <div :class="wide ? 'max-w-3xl' : 'max-w-xl'">
      <p class="text-base font-semibold uppercase tracking-wider text-accent">Step {{ number }} of 6</p>
      <h2 :id="`step-${number}-title`" tabindex="-1" class="mt-2 text-[34px] focus:outline-none">{{ title }}</h2>
      <div class="mt-5 space-y-4 text-lg text-ink">
        <slot name="explain" />
      </div>
      <div v-if="data.length" class="mt-6">
        <p class="flex items-center gap-2 text-base font-semibold text-muted">
          <Database :size="18" aria-hidden="true" /> Data used
        </p>
        <ul class="mt-2 flex flex-wrap gap-2" aria-label="Data used">
          <li v-for="d in data" :key="d" class="chip font-mono text-[15px]">{{ d }}</li>
        </ul>
      </div>
      <slot name="aside" />
      <button v-if="next" type="button" class="link mt-8 inline-flex items-center gap-2 text-lg" @click="$emit('next')">
        Next: {{ next }} <ArrowRight :size="20" aria-hidden="true" />
      </button>
    </div>
    <div class="flex flex-col items-center gap-8 lg:flex-row lg:items-start" :class="wide ? 'lg:justify-center' : ''">
      <slot />
    </div>
  </section>
</template>
