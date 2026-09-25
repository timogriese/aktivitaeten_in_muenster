<script setup lang="ts">
import { Temporal } from '@js-temporal/polyfill'
import { geocode } from '~/data/explore'
import type { AddressSuggestion, ExploreRequest } from '~/types/explore'

defineProps<{ loading: boolean }>()
const origin = defineModel<AddressSuggestion | null>('origin', { required: true })
const emit = defineEmits<{ search: [request: ExploreRequest]; pickOnMap: [] }>()
const hours = ref<number | string>('')
const minutes = ref<number | string>('')
const startMode = ref('now')
const dateTime = ref('')
const addressText = ref('')
const suggestions = ref<AddressSuggestion[]>([])
const suggestionsOpen = ref(false)
const addressLoading = ref(false)
const activeSuggestion = ref(-1)
const addressError = ref('')
const geoError = ref('')
const locating = ref(false)
const formError = ref('')
const errorField = ref('')
let addressVersion = 0
let locationVersion = 0

watch(origin, (value) => {
  ++locationVersion
  ++addressVersion
  locating.value = false
  addressLoading.value = false
  if (value) {
    addressText.value = value.label
    suggestionsOpen.value = false
    suggestions.value = []
    geoError.value = ''
    addressError.value = ''
    if (errorField.value === 'address') { formError.value = ''; errorField.value = '' }
  }
}, { flush: 'sync', immediate: true })

async function searchAddresses() {
  origin.value = null
  ++locationVersion
  locating.value = false
  geoError.value = ''
  const version = ++addressVersion
  activeSuggestion.value = -1
  suggestions.value = []
  addressError.value = ''
  suggestionsOpen.value = Boolean(addressText.value.trim())
  if (!addressText.value.trim()) { addressLoading.value = false; return }
  addressLoading.value = true
  try {
    const response = await geocode(addressText.value)
    if (version === addressVersion) suggestions.value = response
  }
  catch {
    if (version === addressVersion) addressError.value = 'Die Adresssuche ist gerade nicht verfügbar. Wähle einen Punkt auf der Karte oder versuche es erneut.'
  }
  finally { if (version === addressVersion) addressLoading.value = false }
}

function chooseAddress(address: AddressSuggestion) {
  origin.value = address
  suggestionsOpen.value = false
  document.getElementById('address')?.focus()
}

function addressKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') { suggestionsOpen.value = false; return }
  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    event.preventDefault()
    if (!suggestions.value.length) return
    suggestionsOpen.value = true
    const step = event.key === 'ArrowDown' ? 1 : -1
    activeSuggestion.value = Math.max(0, Math.min(suggestions.value.length - 1, activeSuggestion.value + step))
  }
  if (event.key === 'Enter' && suggestionsOpen.value) {
    event.preventDefault()
    const address = suggestions.value[activeSuggestion.value]
    if (address) chooseAddress(address)
  }
}

function leaveAddress(event: FocusEvent) {
  if (!(event.currentTarget as HTMLElement).contains(event.relatedTarget as Node | null)) suggestionsOpen.value = false
}

function locate() {
  geoError.value = ''
  if (!navigator.geolocation) { geoError.value = 'Dein Browser unterstützt die Standortabfrage nicht. Nutze die Adresssuche oder die Karte.'; return }
  const version = ++locationVersion
  ++addressVersion
  suggestionsOpen.value = false
  addressLoading.value = false
  locating.value = true
  navigator.geolocation.getCurrentPosition(
    (position) => {
      if (version !== locationVersion) return
      origin.value = { id: 'device', label: 'Mein Standort', location: { lat: position.coords.latitude, lng: position.coords.longitude } }
      locating.value = false
    },
    (error) => {
      if (version !== locationVersion) return
      locating.value = false
      geoError.value = error.code === 1
        ? 'Standortfreigabe verweigert. Du kannst eine Adresse oder einen Punkt auf der Karte wählen.'
        : 'Dein Standort konnte nicht ermittelt werden. Nutze die Adresssuche oder die Karte.'
    },
    { enableHighAccuracy: false, timeout: 15000, maximumAge: 0 },
  )
}

function invalid(field: string, message: string) {
  errorField.value = field
  formError.value = message
  document.getElementById(field)?.focus()
}

function submit() {
  formError.value = ''
  errorField.value = ''
  const h = Number(hours.value)
  const m = Number(minutes.value)
  const availableMinutes = h * 60 + m
  const hourInput = document.getElementById('duration-hours') as HTMLInputElement
  const minuteInput = document.getElementById('duration-minutes') as HTMLInputElement
  if (!hourInput.validity.valid || !minuteInput.validity.valid || !Number.isSafeInteger(h) || h < 0 || !Number.isSafeInteger(m) || m < 0 || !Number.isSafeInteger(availableMinutes) || availableMinutes <= 0) {
    invalid('duration-hours', 'Bitte gib eine positive Dauer in ganzen Stunden und Minuten ein.')
    return
  }
  let startsAt: string
  if (startMode.value === 'now') startsAt = Temporal.Now.zonedDateTimeISO('Europe/Berlin').toString({ timeZoneName: 'never', calendarName: 'never', smallestUnit: 'second' })
  else {
    if (!dateTime.value) { invalid('start-date', 'Bitte wähle Datum und Uhrzeit für deinen Start.'); return }
    try {
      const berlinDate = Temporal.PlainDateTime.from(dateTime.value).toZonedDateTime('Europe/Berlin', { disambiguation: 'reject' })
      startsAt = berlinDate.toString({ timeZoneName: 'never', calendarName: 'never', smallestUnit: 'second' })
    }
    catch {
      invalid('start-date', 'Diese Uhrzeit ist in Europe/Berlin ungültig oder durch die Zeitumstellung doppeldeutig. Bitte wähle einen eindeutigen Zeitpunkt.')
      return
    }
  }
  if (!origin.value || !Number.isFinite(origin.value.location.lat) || Math.abs(origin.value.location.lat) > 90 || !Number.isFinite(origin.value.location.lng) || Math.abs(origin.value.location.lng) > 180) {
    invalid('address', 'Bitte wähle einen Adressvorschlag, deinen Standort oder einen Punkt auf der Karte.')
    return
  }
  emit('search', { origin: { ...origin.value.location }, startsAt, availableMinutes })
}

onBeforeUnmount(() => { ++addressVersion; ++locationVersion })
</script>

<template>
  <form class="search-form" novalidate @submit.prevent="submit">
    <div class="form-heading"><span class="eyebrow">Deine kleine Auszeit</span><h2>Was passt in deinen Tag?</h2></div>
    <fieldset class="search-field">
      <legend><span class="field-number">01</span> Wie viel Zeit hast du?</legend>
      <div class="duration-inputs">
        <label class="number-field"><input id="duration-hours" v-model="hours" type="number" min="0" step="1" inputmode="numeric" placeholder="–" :aria-invalid="errorField === 'duration-hours'" :aria-describedby="errorField === 'duration-hours' ? 'search-form-error' : undefined"><span>Stunden</span></label>
        <span class="duration-divider">:</span>
        <label class="number-field"><input id="duration-minutes" v-model="minutes" type="number" min="0" step="1" inputmode="numeric" placeholder="–" :aria-invalid="errorField === 'duration-hours'" :aria-describedby="errorField === 'duration-hours' ? 'search-form-error' : undefined"><span>Minuten</span></label>
      </div>
    </fieldset>
    <fieldset class="search-field">
      <legend><span class="field-number">02</span> Wann geht’s los?</legend>
      <div class="start-options">
        <label :class="{ checked: startMode === 'now' }"><input v-model="startMode" type="radio" name="start-mode" value="now"><AppIcon name="sun" :size="16" />Jetzt</label>
        <label :class="{ checked: startMode === 'planned' }"><input v-model="startMode" type="radio" name="start-mode" value="planned"><AppIcon name="calendar" :size="16" />Später</label>
      </div>
      <div v-if="startMode === 'planned'" class="scheduled-input">
        <label for="start-date">Datum und Uhrzeit</label>
        <input id="start-date" v-model="dateTime" type="datetime-local" :aria-invalid="errorField === 'start-date'" aria-describedby="timezone-label">
        <small id="timezone-label">Ortszeit Münster · Europe/Berlin</small>
      </div>
    </fieldset>
    <fieldset class="search-field location-field">
      <legend><span class="field-number">03</span> Wo startest du?</legend>
      <div class="address-combobox" @focusout="leaveAddress">
        <label class="sr-only" for="address">Adresse in Münster suchen</label>
        <div class="address-input"><AppIcon name="search" :size="18" /><input id="address" v-model="addressText" type="text" role="combobox" autocomplete="off" placeholder="Adresse in Münster" aria-autocomplete="list" aria-controls="address-suggestions" :aria-expanded="suggestionsOpen" :aria-activedescendant="suggestionsOpen && activeSuggestion >= 0 ? `address-option-${activeSuggestion}` : undefined" :aria-invalid="errorField === 'address'" aria-describedby="address-hint" @input="searchAddresses" @keydown="addressKeydown" @focus="suggestionsOpen = !origin && Boolean(addressText.trim())"><AppIcon v-if="origin" name="check" :size="17" /></div>
        <div v-if="suggestionsOpen" class="suggestions-popover">
          <ul id="address-suggestions" role="listbox" aria-label="Beispieladressen in Münster">
            <li v-for="(address, index) in suggestions" :id="`address-option-${index}`" :key="address.id" role="option" :aria-selected="index === activeSuggestion" @pointerdown.prevent="chooseAddress(address)"><AppIcon name="pin" :size="16" />{{ address.label }}</li>
          </ul>
          <p v-if="!suggestions.length" role="status">{{ addressLoading ? 'Adressen werden gesucht …' : addressError || 'Keine Beispieladresse gefunden. Versuche „Domplatz“, „Hafen“ oder „Bahnhof“.' }}</p>
        </div>
      </div>
      <small id="address-hint">Lokale Beispieladressen in Münster</small>
      <div class="location-actions">
        <button class="text-button" type="button" :disabled="locating" @click="locate"><AppIcon name="locate" :size="16" />{{ locating ? 'Standort wird ermittelt …' : 'Mein Standort' }}</button>
        <button class="text-button" type="button" @click="emit('pickOnMap')"><AppIcon name="map" :size="16" />Auf Karte wählen</button>
      </div>
      <p v-if="geoError" class="inline-error" role="alert">{{ geoError }}</p>
    </fieldset>
    <p v-if="formError" id="search-form-error" class="inline-error" role="alert">{{ formError }}</p>
    <button class="primary-button search-submit" type="submit" :aria-busy="loading">{{ loading ? 'Aktivitäten werden geladen …' : 'Aktivitäten zeigen' }}<AppIcon name="arrow" :size="18" /></button>
  </form>
</template>
