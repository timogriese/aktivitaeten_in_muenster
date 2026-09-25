<script setup lang="ts">
import type { Activity } from '~/types/explore'

const props = defineProps<{ src?: string; title: string; alt?: string; position?: string; credit?: Activity['imageCredit'] }>()
const failed = ref(false)
watch(() => props.src, () => { failed.value = false })
</script>

<template>
  <div class="activity-image">
    <img v-if="src && !failed" :src="src" :alt="alt || title" :style="{ objectPosition: position }" decoding="async" @error="failed = true">
    <div v-else class="image-fallback" role="img" :aria-label="`Ersatzmotiv für ${title}`">
      <span class="fallback-orbit"></span>
      <AppIcon name="sun" :size="72" />
      <span class="fallback-caption">Ein guter Moment, rauszugehen.</span>
    </div>
    <p v-if="src && !failed && credit" class="photo-credit">Foto: <a :href="credit.sourceUrl" target="_blank" rel="noopener noreferrer">{{ credit.author }}</a> · <a :href="credit.licenseUrl" target="_blank" rel="noopener noreferrer">{{ credit.license }}</a> · Ausschnitt</p>
  </div>
</template>
