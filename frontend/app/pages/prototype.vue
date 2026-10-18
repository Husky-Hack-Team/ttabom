<script setup>
// Standalone clickable prototype: only the phone, driven from inside it.
import PrototypeApp from '~/components/phone/PrototypeApp.vue'

useHead({
  // Locks the page itself so the app's content area is the only thing that scrolls.
  htmlAttrs: { class: 'proto-page' },
  bodyAttrs: { class: 'proto-page' },
  title: 'Prototype · Stop the scam before the money moves',
  meta: [
    // Only this page goes edge to edge on notched phones (safe areas handled in PhoneFrame).
    { name: 'viewport', content: 'width=device-width, initial-scale=1, viewport-fit=cover, interactive-widget=resizes-content' },
    { name: 'theme-color', content: '#ffffff' }
  ]
})
</script>

<template>
  <PrototypeApp />
</template>
