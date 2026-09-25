<script setup lang="ts">
import { explore } from '~/data/explore'
import type { Activity, AddressSuggestion, Coordinates, ExploreRequest } from '~/types/explore'

const view = ref<'discover' | 'map'>('discover')
const mapVisited = ref(false)
const origin = ref<AddressSuggestion | null>(null)
const activities = ref<Activity[]>([])
const selectedIndex = ref(0)
const selected = computed(() => activities.value[selectedIndex.value] ?? null)
const loading = ref(false)
const searched = ref(false)
const searchError = ref('')
const direction = ref('next')
const details = useTemplateRef('details')
const mapRegion = ref<HTMLElement>()
let searchVersion = 0

async function search(request: ExploreRequest) {
  const version = ++searchVersion
  loading.value = true
  searchError.value = ''
  try {
    const response = await explore(request)
    if (version !== searchVersion) return
    details.value?.close()
    activities.value = response.activities
    selectedIndex.value = 0
    searched.value = true
  }
  catch {
    if (version === searchVersion) searchError.value = 'Die Aktivitäten konnten nicht geladen werden. Bitte versuche die Suche erneut.'
  }
  finally { if (version === searchVersion) loading.value = false }
}

function changeView(nextView: 'discover' | 'map') {
  view.value = nextView
  if (nextView === 'map') mapVisited.value = true
}

async function showMap() {
  changeView('map')
  await nextTick()
  mapRegion.value?.focus({ preventScroll: true })
  mapRegion.value?.scrollIntoView({ behavior: 'instant', block: 'nearest' })
}

function pickOrigin(location: Coordinates) {
  origin.value = { id: 'map', label: `Kartenpunkt · ${location.lat.toFixed(4)}, ${location.lng.toFixed(4)}`, location }
}

function selectActivity(id: string) {
  const index = activities.value.findIndex(activity => activity.id === id)
  if (index >= 0) selectedIndex.value = index
}

function move(step: number) {
  const next = selectedIndex.value + step
  if (next < 0 || next >= activities.value.length) return
  direction.value = step > 0 ? 'next' : 'previous'
  selectedIndex.value = next
}

function carouselKeydown(event: KeyboardEvent) {
  if (event.altKey || event.ctrlKey || event.metaKey || !['ArrowLeft', 'ArrowRight'].includes(event.key)) return
  event.preventDefault()
  move(event.key === 'ArrowRight' ? 1 : -1)
}

onBeforeUnmount(() => { ++searchVersion })
</script>

<template>
  <div class="app-shell">
    <a class="skip-link" href="#main-content">Zum Inhalt springen</a>
    <header class="site-header">
      <div class="brand" aria-label="rauszeit Münster"><span class="brand-mark"><AppIcon name="arrow" :size="28" /></span><span>rauszeit<span class="brand-dot">.</span></span><span class="brand-city">MÜNSTER</span></div>
      <span class="demo-badge"><span></span>Demo · Beispieldaten</span>
    </header>
    <main id="main-content">
      <section class="intro" aria-labelledby="page-title">
        <div><p class="eyebrow">Weniger suchen. Mehr erleben.</p><h1 id="page-title">Dein Münster.<br class="mobile-break"> <em>Deine Auszeit.</em></h1><p class="intro-copy">Ein bisschen Zeit. Eine neue Idee. Und los.</p></div>
        <div class="intro-stamp" aria-hidden="true"><AppIcon name="sun" :size="32" /><span>Gute Zeit<br>liegt so nah.</span></div>
      </section>
      <div class="workspace">
        <aside class="search-sidebar" aria-label="Aktivitäten suchen">
          <SearchForm v-model:origin="origin" :loading="loading" @search="search" @pick-on-map="showMap" />
          <div class="sidebar-note"><AppIcon name="leaf" :size="21" /><p>Manchmal ist die nächste<br>Auszeit gleich um die Ecke.</p></div>
        </aside>
        <section class="results-section" aria-labelledby="results-heading" :aria-busy="loading">
          <div class="results-toolbar">
            <div class="result-summary"><h2 id="results-heading">{{ searched ? 'Deine Entdeckungen' : 'Hier beginnt deine Auszeit' }}</h2><span v-if="searched">{{ activities.length }} {{ activities.length === 1 ? 'Aktivität' : 'Aktivitäten' }} · Beispieldaten</span><span v-else>Münster wartet auf dich</span></div>
            <div class="view-switch" role="group" aria-label="Ansicht wählen">
              <button type="button" :aria-pressed="view === 'discover'" :class="{ active: view === 'discover' }" @click="changeView('discover')"><AppIcon name="discover" :size="17" />Entdecken</button>
              <button type="button" :aria-pressed="view === 'map'" :class="{ active: view === 'map' }" @click="changeView('map')"><AppIcon name="map" :size="17" />Karte</button>
            </div>
          </div>
          <div class="sr-only" role="status" aria-atomic="true">{{ loading ? 'Aktivitäten werden geladen.' : searched ? `${activities.length} Aktivitäten. ${selected ? `${selectedIndex + 1} von ${activities.length}: ${selected.title}` : 'Keine Aktivitäten gefunden.'}` : '' }}</div>
          <p v-if="searchError" class="result-error" role="alert">{{ searchError }}</p>
          <div v-if="searched && !activities.length" class="empty-result" role="status"><AppIcon name="discover" :size="28" /><h3>Gerade keine Aktivitäten gefunden</h3><p>Ändere deine Suchangaben und suche erneut.</p></div>
          <div v-show="view === 'discover'" class="discover-view" @keydown="carouselKeydown">
            <template v-if="selected">
              <div class="card-transition-frame">
                <Transition :name="direction === 'next' ? 'slide-next' : 'slide-previous'" mode="out-in"><ActivityCard :key="selected.id" :activity="selected" @details="details?.open()" /></Transition>
              </div>
              <nav class="carousel-controls" aria-label="Aktivitäten durchblättern">
                <button class="secondary-button" type="button" :disabled="selectedIndex === 0" @click="move(-1)"><AppIcon name="back" :size="17" />Zurück</button>
                <span class="carousel-position"><strong>{{ selectedIndex + 1 }}</strong><span>von {{ activities.length }}</span></span>
                <button class="secondary-button" type="button" :disabled="selectedIndex >= activities.length - 1" @click="move(1)">Weiter<AppIcon name="arrow" :size="17" /></button>
              </nav>
            </template>
            <div v-else-if="!searched" class="welcome-card">
              <img src="/images/aasee.svg" alt="Illustration einer grünen Uferlandschaft mit Segelboot auf dem Aasee" class="welcome-landscape">
              <div class="welcome-content"><span class="welcome-label"><AppIcon name="pin" :size="15" />MÜNSTER, DEINE STADT</span><h3>Mal kurz<br><em>rauskommen.</em></h3><p>Wie viel Zeit bringst du mit?<br>Wähle deinen Start – wir zeigen dir die Ideen.</p><span class="welcome-footnote"><span></span>Natur, Kultur und kleine Abenteuer</span></div>
            </div>
          </div>
          <div v-show="view === 'map'" ref="mapRegion" class="map-region" tabindex="-1" aria-label="Kartenansicht">
            <p class="map-instruction"><AppIcon name="pin" :size="16" />Klicke auf die Karte, um deinen Startort zu wählen.</p>
            <div class="map-layout" :class="{ 'has-selection': selected }">
              <ClientOnly><LazyActivityMap v-if="mapVisited" :activities="activities" :selected-id="selected?.id" :origin="origin?.location ?? null" :active="view === 'map'" @select="selectActivity" @pick-origin="pickOrigin" /><template #fallback><div class="map-placeholder">Karte wird geladen …</div></template></ClientOnly>
              <ActivityCard v-if="selected" :key="selected.id" :activity="selected" compact @details="details?.open()" />
            </div>
          </div>
          <p class="results-footnote"><span class="tiny-star" aria-hidden="true">✳</span>Dein nächster Lieblingsmoment könnte ganz nah sein.</p>
        </section>
      </div>
    </main>
    <footer class="site-footer"><span>Mit Neugier durch Münster.</span><p>Demo mit Beispieldaten. Veranstaltungen und Zeitangaben sind keine verifizierten aktuellen Informationen.</p></footer>
    <ActivityDetails ref="details" :activity="selected" @show-map="showMap" />
  </div>
</template>
