<script setup lang="ts">
const props = defineProps<{ src?: string; title: string }>()
const failed = ref(false)
watch(() => props.src, () => { failed.value = false })
</script>

<template>
  <div class="activity-image">
    <img v-if="src && !failed" :src="src" :alt="`Illustration: ${title}`" decoding="async" @error="failed = true">
    <div v-else class="image-fallback" role="img" :aria-label="`Ersatzmotiv für ${title}`">
      <span class="fallback-orbit"></span>
      <AppIcon name="sun" :size="72" />
      <span class="fallback-caption">Ein guter Moment, rauszugehen.</span>
    </div>
  </div>
</template>
