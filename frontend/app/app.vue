<script setup lang="ts">
import { explore } from '~/data/explore'
import type { Activity, AddressSuggestion, Coordinates, ExploreRequest } from '~/types/explore'

const view = ref<'discover' | 'map'>('discover')
const mapVisited = ref(false)
const origin = ref<AddressSuggestion | null>(null)
const activities = ref<Activity[]>([])
const selectedIndex = ref(0)
const selected = computed(() => activities.value[selectedIndex.value] ?? null)
const reviewedIds = ref<string[]>([])
const likedIds = ref<string[]>([])
const searched = ref(false)
const shortlist = computed(() => activities.value.filter(activity => likedIds.value.includes(activity.id)))
const roundComplete = computed(() => searched.value && activities.value.length > 0 && (likedIds.value.length >= 3 || reviewedIds.value.length === activities.value.length))
const chosenId = ref<string | null>(null)
const chosen = computed(() => shortlist.value.find(activity => activity.id === chosenId.value) ?? null)
const mapActivities = computed(() => roundComplete.value ? shortlist.value : activities.value.filter(activity => !reviewedIds.value.includes(activity.id)))
const detailActivity = ref<Activity | null>(null)
const roundNumber = ref(0)
const completionHeading = ref<HTMLElement>()
const chosenHeading = ref<HTMLElement>()
const loading = ref(false)
const searchError = ref('')
const details = useTemplateRef('details')
const mapRegion = ref<HTMLElement>()
const resultHeading = computed(() => chosen.value ? 'Deine Entscheidung' : roundComplete.value ? 'Deine Auswahl' : searched.value ? 'Was spricht dich an?' : 'Hier beginnt deine Auszeit')
const announcement = computed(() => {
  if (loading.value) return 'Aktivitäten werden geladen.'
  if (chosen.value) return `Deine Auszeit steht fest: ${chosen.value.title}.`
  if (roundComplete.value) return shortlist.value.length === 3 ? 'Deine drei Ideen stehen fest. Wähle jetzt deine Unternehmung.' : `${shortlist.value.length} spannende Aktivitäten gefunden. Alle Vorschläge sind bewertet.`
  if (!searched.value) return ''
  return selected.value ? `${likedIds.value.length} von 3 gefunden. Nächste Aktivität: ${selected.value.title}.` : 'Keine Aktivitäten gefunden.'
})
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
    reviewedIds.value = []
    likedIds.value = []
    chosenId.value = null
    detailActivity.value = null
    ++roundNumber.value
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
  if (!mapActivities.value.some(activity => activity.id === id)) return
  const index = activities.value.findIndex(activity => activity.id === id)
  if (index >= 0) selectedIndex.value = index
}

async function openDetails(activity: Activity) {
  selectActivity(activity.id)
  detailActivity.value = activity
  await nextTick()
  details.value?.open()
}

async function decide(id: string, interested: boolean) {
  if (loading.value || roundComplete.value || selected.value?.id !== id || reviewedIds.value.includes(id)) return
  reviewedIds.value.push(id)
  if (interested) likedIds.value.push(id)
  if (roundComplete.value) {
    selectedIndex.value = activities.value.findIndex(activity => likedIds.value.includes(activity.id))
    changeView('discover')
    await nextTick()
    completionHeading.value?.focus({ preventScroll: true })
    completionHeading.value?.scrollIntoView({ behavior: 'instant', block: 'nearest' })
  }
  else selectedIndex.value = activities.value.findIndex(activity => !reviewedIds.value.includes(activity.id))
}

async function choose(activity: Activity) {
  if (!roundComplete.value || !likedIds.value.includes(activity.id)) return
  chosenId.value = activity.id
  selectActivity(activity.id)
  await nextTick()
  chosenHeading.value?.focus({ preventScroll: true })
  chosenHeading.value?.scrollIntoView({ behavior: 'instant', block: 'nearest' })
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
        <div><p class="eyebrow">Weniger überlegen. Mehr erleben.</p><h1 id="page-title">Dein Münster.<br class="mobile-break"> <em>Deine Auszeit.</em></h1><p class="intro-copy">Drei gute Ideen. Eine leichte Entscheidung. Und los.</p></div>
        <div class="intro-stamp" aria-hidden="true"><AppIcon name="sun" :size="32" /><span>Gute Zeit<br>liegt so nah.</span></div>
      </section>
      <div class="workspace">
        <aside class="search-sidebar" aria-label="Aktivitäten suchen">
          <SearchForm v-model:origin="origin" :loading="loading" @search="search" @pick-on-map="showMap" />
          <div class="sidebar-note"><AppIcon name="leaf" :size="21" /><p>Manchmal ist die nächste<br>Auszeit gleich um die Ecke.</p></div>
        </aside>
        <section class="results-section" aria-labelledby="results-heading" :aria-busy="loading">
          <div class="results-toolbar">
            <div class="result-summary"><h2 id="results-heading">{{ resultHeading }}</h2><span v-if="searched">{{ roundComplete ? shortlist.length : activities.length }} {{ (roundComplete ? shortlist.length : activities.length) === 1 ? 'Aktivität' : 'Aktivitäten' }} · Beispieldaten</span><span v-else>Münster wartet auf dich</span></div>
            <div class="view-switch" role="group" aria-label="Ansicht wählen">
              <button type="button" :aria-pressed="view === 'discover'" :class="{ active: view === 'discover' }" @click="changeView('discover')"><AppIcon name="discover" :size="17" />Entdecken</button>
              <button type="button" :aria-pressed="view === 'map'" :class="{ active: view === 'map' }" @click="changeView('map')"><AppIcon name="map" :size="17" />Karte</button>
            </div>
          </div>
          <div class="sr-only" role="status" aria-atomic="true">{{ announcement }}</div>
          <p v-if="searchError" class="result-error" role="alert">{{ searchError }}</p>
          <div v-if="searched && !activities.length" class="empty-result" role="status"><AppIcon name="discover" :size="28" /><h3>Gerade keine Aktivitäten gefunden</h3><p>Ändere deine Suchangaben und suche erneut.</p></div>
          <div v-if="searched && activities.length && !roundComplete" class="decision-progress">
            <span><strong>{{ likedIds.length }}</strong> von 3 gefunden</span>
            <div class="progress-slots" aria-hidden="true"><span v-for="index in 3" :key="index" :class="{ filled: index <= likedIds.length }"><AppIcon v-if="index <= likedIds.length" name="check" :size="14" /><span v-else>{{ index }}</span></span></div>
          </div>
          <div v-show="view === 'discover'" class="discover-view">
            <div v-if="chosen" class="chosen-result">
              <div class="chosen-heading"><span class="chosen-check" aria-hidden="true"><AppIcon name="check" :size="24" /></span><div><p class="eyebrow">Weniger überlegen. Los geht’s.</p><h3 ref="chosenHeading" tabindex="-1">Deine Auszeit steht fest.</h3></div></div>
              <ActivityCard :activity="chosen" @details="openDetails(chosen)"><template #actions><button class="secondary-button chosen-map" type="button" @click="selectActivity(chosen.id); showMap()"><AppIcon name="map" :size="18" />Auf Karte zeigen</button></template></ActivityCard>
            </div>
            <div v-else-if="roundComplete" class="round-results">
              <div :key="roundNumber" class="round-completion" :class="{ 'round-completion--success': shortlist.length === 3 }">
                <div v-if="shortlist.length === 3" class="success-emblem" aria-hidden="true">
                  <div class="success-pieces"><span v-for="index in 12" :key="index" :style="{ '--angle': `${index * 30}deg`, '--delay': `${(index % 3) * 65}ms` }"></span></div>
                  <svg class="success-check" viewBox="0 0 64 64" fill="none"><circle cx="32" cy="32" r="29" /><path d="m19 32 9 9 18-19" /></svg>
                </div>
                <AppIcon v-else name="discover" :size="30" />
                <p class="eyebrow">{{ shortlist.length === 3 ? 'Geschafft. Deine Auswahl ist komplett.' : 'Alle Vorschläge sind bewertet.' }}</p>
                <h3 ref="completionHeading" tabindex="-1">{{ shortlist.length === 3 ? 'Deine drei Ideen stehen fest.' : shortlist.length ? `${shortlist.length === 1 ? 'Eine Idee hat' : 'Zwei Ideen haben'} dich überzeugt.` : 'Diesmal war noch nichts dabei.' }}</h3>
                <p>{{ shortlist.length ? 'Worauf hast du jetzt am meisten Lust?' : 'Ändere deine Suchangaben und starte eine neue Suche.' }}</p>
              </div>
              <div v-if="shortlist.length" class="shortlist-grid">
                <ActivityCard v-for="activity in shortlist" :key="activity.id" :activity="activity" @details="openDetails(activity)"><template #actions><p class="shortlist-address"><AppIcon name="pin" :size="14" />{{ activity.address }}</p><button class="primary-button choose-button" type="button" @click="choose(activity)">Das mache ich<AppIcon name="arrow" :size="16" /></button></template></ActivityCard>
              </div>
            </div>
            <template v-else-if="selected">
              <ActivityDecision :key="roundNumber" :activity="selected" :disabled="loading" @decide="decide" @details="openDetails(selected)" />
              <p class="swipe-hint">Nach links: nicht für mich. Nach rechts: spannend.<br>Oder entscheide mit den Buttons.</p>
            </template>
            <div v-else-if="!searched" class="welcome-card">
              <img src="/images/aasee.svg" alt="Illustration einer grünen Uferlandschaft mit Segelboot auf dem Aasee" class="welcome-landscape">
              <div class="welcome-content"><span class="welcome-label"><AppIcon name="pin" :size="15" />MÜNSTER, DEINE STADT</span><h3>Mal kurz<br><em>rauskommen.</em></h3><p>Was klingt nach deiner Auszeit?<br>Finde drei Ideen und wähle deinen Favoriten.</p><span class="welcome-footnote"><span></span>Natur, Kultur und kleine Abenteuer</span></div>
            </div>
          </div>
          <div v-show="view === 'map'" ref="mapRegion" class="map-region" tabindex="-1" aria-label="Kartenansicht">
            <p class="map-instruction"><AppIcon name="pin" :size="16" />Klicke auf die Karte, um deinen Startort zu wählen.</p>
            <div class="map-layout" :class="{ 'has-selection': selected, 'has-decision': selected && !roundComplete }">
              <ClientOnly><LazyActivityMap v-if="mapVisited" :activities="mapActivities" :selected-id="selected?.id" :origin="origin?.location ?? null" :active="view === 'map'" @select="selectActivity" @pick-origin="pickOrigin" /><template #fallback><div class="map-placeholder">Karte wird geladen …</div></template></ClientOnly>
              <ActivityDecision v-if="selected && !roundComplete" :key="roundNumber" :activity="selected" :disabled="loading" compact @decide="decide" @details="openDetails(selected)" />
              <ActivityCard v-else-if="selected" :key="selected.id" :activity="selected" compact @details="openDetails(selected)" />
            </div>
          </div>
          <p class="results-footnote"><span class="tiny-star" aria-hidden="true">✳</span>Dein nächster Lieblingsmoment könnte ganz nah sein.</p>
        </section>
      </div>
    </main>
    <footer class="site-footer"><span>Mit Neugier durch Münster.</span><p>Demo mit Beispieldaten. Veranstaltungen und Zeitangaben sind keine verifizierten aktuellen Informationen.</p></footer>
    <ActivityDetails ref="details" :activity="detailActivity" @show-map="showMap" />
  </div>
</template>
