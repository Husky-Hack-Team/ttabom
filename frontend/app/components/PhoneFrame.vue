<script setup>
// A 390×844 phone, light design, no browser chrome. Scales down on narrow screens.
// `fullscreen` (used by /prototype): on desktop the same frame, centered and
// scaled to fit the window; on phones and short landscape windows no frame at
// all, the app fills the screen with safe-area insets.
const props = defineProps({
  label: { type: String, required: true },
  time: { type: String, default: '' },
  fullscreen: { type: Boolean, default: false }
})

// Frame size including the 10px bezel; the scale keeps it inside the window.
const FRAME_W = 410
const FRAME_H = 864
const MARGIN = 32
const scale = ref(1)
const appHeight = ref(null)

function measure() {
  scale.value = Math.min(1, (window.innerHeight - MARGIN) / FRAME_H, (window.innerWidth - MARGIN) / FRAME_W)
  // Phones: size the app to the visible area so the on-screen keyboard doesn't
  // cover it. Only the SIZE follows the viewport, and only on resize: moving the
  // app to follow visualViewport scroll events fought the user's swipe and made
  // scrolling feel inverted on real devices. Ignore pinch-zoom sizes.
  const vv = window.visualViewport
  appHeight.value = vv && Math.abs(vv.scale - 1) < 0.01 ? vv.height : window.innerHeight
}
onMounted(() => {
  if (!props.fullscreen) return
  measure()
  window.addEventListener('resize', measure)
  window.visualViewport?.addEventListener('resize', measure)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', measure)
  window.visualViewport?.removeEventListener('resize', measure)
})
const shellStyle = computed(() => ({
  '--frame-scale': scale.value,
  '--app-h': appHeight.value ? `${appHeight.value}px` : '100dvh'
}))
</script>

<template>
  <figure
    v-if="!fullscreen"
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

  <div v-else class="phone-shell" :style="shellStyle">
    <div class="phone-shell-box">
      <figure class="phone-shell-device" :aria-label="label">
        <div class="phone-shell-status" aria-hidden="true">
          <span>{{ time }}</span>
          <span class="h-6 w-24 rounded-full bg-[#1b2333]" />
          <span class="flex items-center gap-1">
            <span class="h-2.5 w-4 rounded-sm border-2 border-ink" />
          </span>
        </div>
        <div class="phone-shell-screen">
          <slot />
        </div>
      </figure>
    </div>
  </div>
</template>

<style>
/* Desktop: the same frame as the walkthrough, centered and scaled to fit. */
.phone-shell {
  display: flex;
  min-height: 100dvh;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 16px;
}
.phone-shell-box {
  position: relative;
  width: calc(410px * var(--frame-scale, 1));
  height: calc(864px * var(--frame-scale, 1));
  flex: none;
}
.phone-shell-device {
  position: absolute;
  left: 0;
  top: 0;
  display: flex;
  width: 410px;
  height: 864px;
  flex-direction: column;
  overflow: hidden;
  border: 10px solid #1b2333;
  border-radius: 52px;
  background: white;
  box-shadow: 0 24px 60px rgb(0 32 91 / 0.18), 0 0 0 0 transparent;
  transform: scale(var(--frame-scale, 1));
  transform-origin: top left;
}
.phone-shell-status {
  display: flex;
  height: 44px;
  flex: none;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-ink);
}
.phone-shell-screen {
  display: flex;
  min-height: 0;
  flex: 1;
  flex-direction: column;
}

/* Phones (and short landscape windows): no frame, the app is the screen. */
@media (max-width: 639px), (max-height: 520px) {
  .phone-shell {
    display: block;
    min-height: 0;
    padding: 0;
  }
  .phone-shell-box {
    position: fixed;
    left: 0;
    right: 0;
    top: 0;
    width: auto;
    height: var(--app-h, 100dvh);
  }
  .phone-shell-device {
    position: absolute;
    inset: 0;
    width: auto;
    height: auto;
    border: 0;
    border-radius: 0;
    box-shadow: none;
    transform: none;
    padding: env(safe-area-inset-top) env(safe-area-inset-right) env(safe-area-inset-bottom) env(safe-area-inset-left);
  }
  .phone-shell-status {
    display: none;
  }
}
</style>
