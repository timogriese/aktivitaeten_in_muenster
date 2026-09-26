<script setup lang="ts">
import { Temporal } from '@js-temporal/polyfill'
import type { ExploreRequest } from '~/types/explore'

const props = defineProps<{ loading: boolean }>()
const emit = defineEmits<{ search: [request: ExploreRequest] }>()
const durationChoice = ref<number | 'custom' | null>(null)
const durationPresets = [
  { minutes: 30, label: '30 Min.' },
  { minutes: 60, label: '1 Stunde' },
  { minutes: 120, label: '2 Stunden' },
  { minutes: 180, label: '3 Stunden' },
]
const hours = ref<number | string>(6)
const minutes = ref<number | string>('')
const locating = ref(false)
const formError = ref('')
const errorField = ref('')
const preferredTags = ref<string[]>([])
const quickInterests = ['entspannt', 'sportlich', 'kreativ', 'kulturell', 'gesellig', 'draußen']
let locationVersion = 0

function interestLabel(tag: string) {
  const label = tag.replaceAll('-', ' ')
  return label.charAt(0).toLocaleUpperCase('de') + label.slice(1)
}

function toggleInterest(tag: string) {
  preferredTags.value = preferredTags.value.includes(tag)
    ? preferredTags.value.filter(selected => selected !== tag)
    : [...preferredTags.value, tag]
}

watch(durationChoice, () => {
  if (errorField.value.startsWith('duration-')) { formError.value = ''; errorField.value = '' }
})

function invalid(field: string, message: string) {
  errorField.value = field
  formError.value = message
  nextTick(() => document.getElementById(field)?.focus())
}

function submit() {
  if (locating.value || props.loading) return
  formError.value = ''
  errorField.value = ''
  if (durationChoice.value === null) {
    invalid('duration-preset-30', 'Bitte wähle eine Dauer oder gib eine eigene Dauer ein.')
    return
  }
  let availableMinutes: number
  if (durationChoice.value === 'custom') {
    const h = Number(hours.value)
    const m = Number(minutes.value)
    availableMinutes = h * 60 + m
    const hourInput = document.getElementById('duration-hours') as HTMLInputElement
    const minuteInput = document.getElementById('duration-minutes') as HTMLInputElement
    if (!hourInput.validity.valid || !minuteInput.validity.valid || !Number.isSafeInteger(h) || h < 0 || !Number.isSafeInteger(m) || m < 0 || !Number.isSafeInteger(availableMinutes) || availableMinutes <= 0) {
      invalid('duration-hours', 'Bitte gib eine positive Dauer in ganzen Stunden und Minuten ein.')
      return
    }
  }
  else availableMinutes = durationChoice.value
  if (!navigator.geolocation) {
    invalid('search-submit', 'Dein Browser unterstützt die Standortabfrage nicht.')
    return
  }
  const version = ++locationVersion
  locating.value = true
  navigator.geolocation.getCurrentPosition(
    (position) => {
      if (version !== locationVersion) return
      locating.value = false
      const origin = { lat: position.coords.latitude, lng: position.coords.longitude }
      if (!Number.isFinite(origin.lat) || Math.abs(origin.lat) > 90 || !Number.isFinite(origin.lng) || Math.abs(origin.lng) > 180) {
        invalid('search-submit', 'Dein Standort konnte nicht ermittelt werden. Bitte versuche es erneut.')
        return
      }
      const startsAt = Temporal.Now.zonedDateTimeISO('Europe/Berlin').toString({ timeZoneName: 'never', calendarName: 'never', smallestUnit: 'second' })
      emit('search', { origin, startsAt, availableMinutes, preferredTags: [...preferredTags.value] })
    },
    (error) => {
      if (version !== locationVersion) return
      locating.value = false
      invalid('search-submit', error.code === 1
        ? 'Standortfreigabe verweigert. Bitte erlaube den Standortzugriff, um Aktivitäten zu finden.'
        : 'Dein Standort konnte nicht ermittelt werden. Bitte versuche es erneut.')
    },
    { enableHighAccuracy: false, timeout: 15000, maximumAge: 0 },
  )
}

onBeforeUnmount(() => { ++locationVersion })
</script>

<template>
  <form class="search-form" novalidate @submit.prevent="submit">
    <div class="form-heading"><span class="eyebrow">Deine kleine Auszeit</span><h2>Was passt in deinen Tag?</h2></div>
    <fieldset class="search-field" :aria-describedby="errorField.startsWith('duration-') ? 'search-form-error' : undefined">
      <legend>Wie viel Zeit hast du?</legend>
      <div class="duration-options">
        <label v-for="preset in durationPresets" :key="preset.minutes" :class="{ checked: durationChoice === preset.minutes }">
          <input :id="`duration-preset-${preset.minutes}`" v-model="durationChoice" type="radio" name="duration" :value="preset.minutes" :aria-invalid="errorField === 'duration-preset-30'" :aria-describedby="errorField === 'duration-preset-30' ? 'search-form-error' : undefined">
          {{ preset.label }}
        </label>
        <label class="duration-custom-option" :class="{ checked: durationChoice === 'custom' }">
          <input v-model="durationChoice" type="radio" name="duration" value="custom" :aria-invalid="errorField === 'duration-preset-30'" :aria-describedby="errorField === 'duration-preset-30' ? 'search-form-error' : undefined">
          Eigene Dauer
        </label>
      </div>
      <div v-if="durationChoice === 'custom'" class="duration-inputs">
        <label class="number-field"><span>Stunden</span><input id="duration-hours" v-model="hours" type="number" min="0" step="1" inputmode="numeric" placeholder="0" :aria-invalid="errorField === 'duration-hours'" :aria-describedby="errorField === 'duration-hours' ? 'search-form-error' : undefined"></label>
        <label class="number-field"><span>Minuten</span><input id="duration-minutes" v-model="minutes" type="number" min="0" step="1" inputmode="numeric" placeholder="0" :aria-invalid="errorField === 'duration-hours'" :aria-describedby="errorField === 'duration-hours' ? 'search-form-error' : undefined"></label>
      </div>
    </fieldset>
    <fieldset class="search-field interest-field">
      <legend>Worauf hast du Lust? <span class="interest-optional">Optional</span></legend>
      <div class="interest-chips">
        <button v-for="tag in quickInterests" :key="tag" type="button" class="interest-chip" :aria-pressed="preferredTags.includes(tag)" @click="toggleInterest(tag)">
          {{ interestLabel(tag) }}<span v-if="preferredTags.includes(tag)" aria-hidden="true">✓</span>
        </button>
      </div>
      <div v-if="preferredTags.length" class="selected-interests">
        <p>Ausgewählt:</p>
        <div class="interest-chips">
          <button v-for="tag in preferredTags" :key="tag" type="button" class="interest-chip interest-chip--selected" :aria-label="`${interestLabel(tag)} entfernen`" @click="toggleInterest(tag)">
            {{ interestLabel(tag) }}<span aria-hidden="true">×</span>
          </button>
        </div>
      </div>
    </fieldset>
    <p v-if="formError" id="search-form-error" class="inline-error" role="alert">{{ formError }}</p>
    <button id="search-submit" class="primary-button search-submit" type="submit" :disabled="locating || loading" :aria-busy="locating || loading" :aria-describedby="errorField === 'search-submit' ? 'search-form-error' : undefined">{{ locating ? 'Standort wird ermittelt …' : loading ? 'Aktivitäten werden geladen …' : 'Aktivitäten zeigen' }}<AppIcon name="arrow" :size="18" /></button>
  </form>
</template>
