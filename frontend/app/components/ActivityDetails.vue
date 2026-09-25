<script setup lang="ts">
import type { Activity } from '~/types/explore'
defineProps<{ activity: Activity | null }>()
const emit = defineEmits<{ close: [] }>()
const dialog = ref<HTMLDialogElement>()
const closeButton = ref<HTMLButtonElement>()
let previouslyFocused: HTMLElement | null = null

function open() {
  previouslyFocused = document.activeElement instanceof HTMLElement ? document.activeElement : null
  dialog.value?.showModal()
  document.body.classList.add('dialog-open')
  closeButton.value?.focus()
}
function close() { dialog.value?.close() }
function onClose() {
  document.body.classList.remove('dialog-open')
  previouslyFocused?.focus()
  emit('close')
}
function formatDate(value: string) {
  const date = new Date(value)
  if (!Number.isFinite(date.getTime())) return value
  return new Intl.DateTimeFormat('de-DE', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Europe/Berlin' }).format(date)
}
function safeWebsite(value?: string) {
  if (!value) return undefined
  try {
    const url = new URL(value)
    return ['https:', 'http:'].includes(url.protocol) ? url.href : undefined
  }
  catch { return undefined }
}
onBeforeUnmount(() => document.body.classList.remove('dialog-open'))
defineExpose({ open, close })
</script>

<template>
  <dialog ref="dialog" class="detail-dialog" aria-labelledby="detail-title" @close="onClose" @click="event => { if (event.target === dialog) close() }">
    <div v-if="activity" class="detail-inner">
      <button ref="closeButton" class="icon-button dialog-close" type="button" aria-label="Details schließen" @click="close"><AppIcon name="close" /></button>
      <ActivityImage :src="activity.imageUrl" :title="activity.title" />
      <div class="detail-content">
        <span class="eyebrow">{{ activity.category }}<template v-if="activity.kind === 'event'"> · Fiktives Event</template></span>
        <h2 id="detail-title">{{ activity.title }}</h2>
        <p>{{ activity.detailedDescription || activity.description }}</p>
        <dl class="detail-facts">
          <div v-if="activity.address"><dt><AppIcon name="pin" />Adresse</dt><dd>{{ activity.address }}</dd></div>
          <div v-if="activity.startsAt"><dt><AppIcon name="calendar" />Beginn</dt><dd>{{ formatDate(activity.startsAt) }} Uhr (Europe/Berlin)</dd></div>
          <div v-if="activity.endsAt"><dt><AppIcon name="calendar" />Ende</dt><dd>{{ formatDate(activity.endsAt) }} Uhr (Europe/Berlin)</dd></div>
          <div v-if="activity.openingHoursText"><dt><AppIcon name="clock" />Öffnungszeiten</dt><dd>{{ activity.openingHoursText }}</dd></div>
          <div v-if="activity.timingLabel"><dt><AppIcon name="clock" />Zeitlicher Hinweis</dt><dd>{{ activity.timingLabel }}</dd></div>
          <div v-if="activity.travelTimeMinutes != null"><dt><AppIcon name="arrow" />Anreise</dt><dd>{{ activity.travelTimeMinutes }} Minuten (Beispiel)</dd></div>
        </dl>
        <p class="detail-demo">Beispieldaten: Veranstaltungen, Öffnungs- und Reisezeiten sind nicht als aktuelle Angaben verifiziert.</p>
        <div v-if="safeWebsite(activity.websiteUrl)" class="detail-actions">
          <a class="text-link" :href="safeWebsite(activity.websiteUrl)" target="_blank" rel="noopener noreferrer">Website öffnen<AppIcon name="external" :size="16" /><span class="sr-only"> (neuer Tab)</span></a>
        </div>
      </div>
    </div>
  </dialog>
</template>
