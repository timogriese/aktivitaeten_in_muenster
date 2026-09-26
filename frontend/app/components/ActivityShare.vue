<script setup lang="ts">
import type { Activity } from '~/types/explore'

const props = defineProps<{ activity: Activity }>()
const sharing = ref(false)
const copied = ref(false)
const manualUrl = ref('')
const linkInput = ref<HTMLInputElement>()

async function share() {
  if (sharing.value) return
  const url = new URL(window.location.pathname, window.location.origin)
  url.searchParams.set('activity', props.activity.id)
  sharing.value = true
  copied.value = false
  manualUrl.value = ''
  try {
    if (navigator.share) {
      try {
        await navigator.share({ title: props.activity.title, url: url.href })
        return
      }
      catch (error) {
        if (error instanceof Error && error.name === 'AbortError') return
      }
    }
    try {
      await navigator.clipboard.writeText(url.href)
      copied.value = true
    }
    catch {
      manualUrl.value = url.href
      await nextTick()
      linkInput.value?.focus()
      linkInput.value?.select()
    }
  }
  finally { sharing.value = false }
}
</script>

<template>
  <div class="activity-share">
    <button class="share-button" type="button" :disabled="sharing" @click="share">
      <span aria-live="polite">{{ copied ? 'Link kopiert' : 'Teilen' }}</span>
      <AppIcon :name="copied ? 'check' : 'share'" :size="18" />
    </button>
    <input v-if="manualUrl" ref="linkInput" class="share-link" :value="manualUrl" readonly aria-label="Link zur Aktivität kopieren" @focus="linkInput?.select()" @click="linkInput?.select()">
  </div>
</template>
