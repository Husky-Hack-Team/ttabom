<script setup>
const props = defineProps({
  name: { type: String, required: true },
  size: { type: Number, default: 48 }
})

const photos = {
  linda: '/avatars/linda.jpg',
  tommy: '/avatars/tommy.jpg',
  uma: '/avatars/uma.jpg'
}

const src = computed(() => photos[props.name.toLowerCase()])
const avatarStyle = computed(() => ({ width: `${props.size}px`, height: `${props.size}px` }))
</script>

<template>
  <img
    v-if="src"
    :src="src"
    alt=""
    :style="avatarStyle"
    class="person-avatar shrink-0 rounded-full object-cover"
    aria-hidden="true"
  >
  <span
    v-else
    :style="avatarStyle"
    class="person-avatar flex shrink-0 items-center justify-center rounded-full bg-accent-soft font-bold text-navy"
    aria-hidden="true"
  >
    {{ name[0] }}
  </span>
</template>

<style scoped>
.person-avatar {
  box-shadow: 0 0 0 2px white, 0 0 0 4px rgb(43 97 153 / 0.2);
}
</style>
