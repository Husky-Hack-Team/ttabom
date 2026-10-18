<script setup>
// End-of-story button, shown only in the standalone /prototype app.
defineEmits(['restart'])
</script>

<template>
  <div class="mt-6 w-full">
    <button type="button" class="btn btn-phone btn-primary text-lg" @click="$emit('restart')">Start over</button>
  </div>
</template>
