<script setup lang="ts">
import { Map as LibreMap, Marker, NavigationControl, AttributionControl, LngLatBounds } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { Activity, Coordinates } from '~/types/explore'

const props = defineProps<{ activities: Activity[]; selectedId?: string; origin: Coordinates | null; active: boolean }>()
const emit = defineEmits<{ select: [id: string]; pickOrigin: [location: Coordinates] }>()
const container = ref<HTMLDivElement>()
const mapError = ref('')
let map: LibreMap | undefined
let observer: ResizeObserver | undefined
let originMarker: Marker | undefined
const activityMarkers = new Map<string, Marker>()

function fitLocations() {
  if (!map || !props.active) return
  const locations = props.activities.map(activity => activity.location)
  if (props.origin) locations.push(props.origin)
  if (!locations.length) return
  const bounds = new LngLatBounds()
  for (const location of locations) bounds.extend([location.lng, location.lat])
  map.fitBounds(bounds, { padding: 55, maxZoom: 14, duration: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 350 })
}

function updateSelection(focus = true) {
  for (const [id, marker] of activityMarkers) {
    marker.getElement().classList.toggle('is-selected', id === props.selectedId)
    marker.getElement().setAttribute('aria-pressed', String(id === props.selectedId))
  }
  const selected = props.activities.find(activity => activity.id === props.selectedId)
  if (focus && selected && map && props.active) {
    map.easeTo({ center: [selected.location.lng, selected.location.lat], duration: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 350 })
  }
}

function updateActivities() {
  if (!map) return
  for (const marker of activityMarkers.values()) marker.remove()
  activityMarkers.clear()
  props.activities.forEach((activity, index) => {
    const button = document.createElement('button')
    button.type = 'button'
    button.className = 'activity-marker'
    button.textContent = String(index + 1)
    button.title = activity.title
    button.setAttribute('aria-label', `${index + 1}. ${activity.title}`)
    button.addEventListener('click', (event) => {
      event.stopPropagation()
      emit('select', activity.id)
    })
    button.addEventListener('dblclick', event => event.stopPropagation())
    activityMarkers.set(activity.id, new Marker({ element: button, anchor: 'center' }).setLngLat([activity.location.lng, activity.location.lat]).addTo(map!))
  })
  updateSelection(false)
  fitLocations()
}

function updateOrigin() {
  originMarker?.remove()
  originMarker = undefined
  if (!props.origin || !map) return
  const dot = document.createElement('div')
  dot.className = 'origin-marker'
  dot.setAttribute('role', 'img')
  dot.setAttribute('aria-label', 'Dein Startort')
  dot.title = 'Dein Startort'
  originMarker = new Marker({ element: dot }).setLngLat([props.origin.lng, props.origin.lat]).addTo(map)
  fitLocations()
}

function disposeMap() {
  observer?.disconnect()
  for (const marker of activityMarkers.values()) marker.remove()
  activityMarkers.clear()
  originMarker?.remove()
  originMarker = undefined
  map?.remove()
  map = undefined
}

function initialize() {
  if (!container.value) return
  disposeMap()
  mapError.value = ''
  try {
    map = new LibreMap({
      container: container.value,
      center: [7.6252, 51.9625],
      zoom: 12.7,
      attributionControl: false,
      style: {
        version: 8,
        sources: {
          osm: {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            maxzoom: 19,
            attribution: '© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a>',
          },
        },
        layers: [{ id: 'base', type: 'raster', source: 'osm', paint: { 'raster-saturation': -0.65 } }],
      },
      locale: {
        'NavigationControl.ZoomIn': 'Vergrößern',
        'NavigationControl.ZoomOut': 'Verkleinern',
        'NavigationControl.ResetBearing': 'Nach Norden ausrichten',
        'AttributionControl.ToggleAttribution': 'Quellenangaben anzeigen',
        'Map.Title': 'Aktivitäten und Startort in Münster',
      },
    })
    map.addControl(new NavigationControl({ showCompass: false }), 'top-right')
    map.addControl(new AttributionControl({ compact: false }), 'bottom-left')
    map.getCanvas().setAttribute('aria-label', 'Karte von Münster. Mit Pfeiltasten bewegen, mit Plus und Minus zoomen. Startort alternativ über die Adresssuche wählen.')
    map.on('click', (event) => {
      if ((event.originalEvent.target as HTMLElement)?.closest('.activity-marker, .maplibregl-control-container')) return
      emit('pickOrigin', { lat: event.lngLat.lat, lng: event.lngLat.wrap().lng })
    })
    map.on('error', () => { mapError.value = 'Die Karte konnte nicht vollständig geladen werden. Prüfe deine Internetverbindung.' })
    updateActivities()
    updateOrigin()
    observer = new ResizeObserver(() => map?.resize())
    observer.observe(container.value)
  }
  catch {
    mapError.value = 'Die Karte ist in diesem Browser nicht verfügbar. Du kannst weiterhin die Adresssuche und „Entdecken“ verwenden.'
  }
}

watch(() => props.activities, updateActivities)
watch(() => props.selectedId, () => updateSelection())
watch(() => props.origin, updateOrigin)
watch(() => props.active, async (active) => {
  if (active) { await nextTick(); map?.resize(); updateSelection() }
})
onMounted(initialize)
onBeforeUnmount(disposeMap)
</script>

<template>
  <div class="map-surface">
    <div ref="container" class="map-canvas"></div>
    <div v-if="mapError" class="map-error" role="alert"><p>{{ mapError }}</p><button class="text-button" type="button" @click="initialize">Erneut laden</button></div>
    <div class="map-key"><span class="origin-key"></span>Dein Startort<span class="activity-key"></span>Aktivität</div>
  </div>
</template>
