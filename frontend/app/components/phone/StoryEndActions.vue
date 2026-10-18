<script setup>
// End-of-story buttons, shown only in the standalone /prototype app.
defineEmits(['other', 'home'])
</script>

<template>
  <div class="mt-6 w-full space-y-3">
    <button type="button" class="btn btn-phone btn-primary text-lg" @click="$emit('other')">Try the other story</button>
    <button type="button" class="btn btn-phone btn-secondary text-lg" @click="$emit('home')">Back to start</button>
  </div>
</template>
