<script setup>
// A 390×844 phone, light design, no browser chrome. Scales down on narrow screens.
defineProps({
  label: { type: String, required: true },
  time: { type: String, default: '' }
})
</script>

<template>
  <figure
    class="mx-auto w-full max-w-[390px] rounded-[52px] border-[10px] border-[#1b2333] bg-[#1b2333] shadow-[0_24px_60px_rgb(0_32_91/0.18)]"
    :aria-label="label"
  >
    <div class="relative flex aspect-[390/844] max-h-[844px] flex-col overflow-hidden rounded-[42px] bg-white">
      <div class="flex h-11 shrink-0 items-center justify-between px-7 text-[15px] font-semibold text-ink" aria-hidden="true">
        <span>{{ time }}</span>
        <span class="h-6 w-24 rounded-full bg-[#1b2333]" />
        <span class="flex items-center gap-1">
          <span class="h-2.5 w-4 rounded-sm border-2 border-ink" />
        </span>
      </div>
      <div class="flex min-h-0 flex-1 flex-col overflow-y-auto px-5 pb-6">
        <slot />
      </div>
    </div>
  </figure>
</template>
