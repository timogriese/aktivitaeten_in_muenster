<script setup lang="ts">
import { explore } from '~/data/explore'
import type { Activity, AddressSuggestion, ExploreRequest } from '~/types/explore'

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
const detailActivity = ref<Activity | null>(null)
const roundNumber = ref(0)
const completionHeading = ref<HTMLElement>()
const chosenHeading = ref<HTMLElement>()
const loading = ref(false)
const searchError = ref('')
const details = useTemplateRef('details')
const resultHeading = computed(() => chosen.value ? 'Deine Entscheidung' : roundComplete.value ? 'Deine Auswahl' : 'Was spricht dich an?')
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

async function openDetails(activity: Activity) {
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
    await nextTick()
    completionHeading.value?.focus({ preventScroll: true })
    completionHeading.value?.scrollIntoView({ behavior: 'instant', block: 'nearest' })
  }
  else selectedIndex.value = activities.value.findIndex(activity => !reviewedIds.value.includes(activity.id))
}

async function choose(activity: Activity) {
  if (!roundComplete.value || !likedIds.value.includes(activity.id)) return
  chosenId.value = activity.id
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
      <div class="brand" aria-label="MünsterMatch">
        <span class="brand-mark" aria-hidden="true">
          <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
            <path d="M26 12c0 7-10 16-10 16S6 19 6 12a10 10 0 0 1 20 0Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round" />
            <path d="M16 18s-6-3.7-6-7.2a3.3 3.3 0 0 1 6-1.8 3.3 3.3 0 0 1 6 1.8C22 14.3 16 18 16 18Z" fill="currentColor" />
          </svg>
        </span>
        <span>MünsterMatch<span class="brand-dot">.</span></span>
      </div>
      <div class="intro">
          <p class="eyebrow">Weniger überlegen. Mehr erleben.</p>
          <svg class="intro-logo" viewBox="0 0 132 84" fill="none" role="img" aria-label="Drei Aktivitätskarten mit einem Herz als Match-Symbol">
            <g transform="rotate(-15 36 46)">
              <rect x="12" y="17" width="47" height="59" rx="11" fill="#e6edda" stroke="#a8bb91" />
              <path d="M42 30c-16-1-24 9-18 17s19 1 18-17Z" fill="#afc58f" stroke="#65804d" stroke-width="1.5" />
              <path d="m23 51 12-13" stroke="#65804d" stroke-width="1.5" stroke-linecap="round" />
            </g>
            <g transform="rotate(15 96 46)">
              <rect x="73" y="17" width="47" height="59" rx="11" fill="#f2e9cc" stroke="#d1bd83" />
              <circle cx="97" cy="39" r="8" fill="#e0bf67" />
              <path d="M97 25v3m0 22v3M83 39h3m22 0h3M87 29l2 2m16 16 2 2M87 49l2-2m16-16 2-2" stroke="#a88636" stroke-width="1.5" stroke-linecap="round" />
            </g>
            <rect x="40" y="7" width="52" height="66" rx="13" fill="#254f3c" stroke="#f7f7ef" stroke-width="3" />
            <path d="M66 51s-15-9-15-19a8 8 0 0 1 15-4 8 8 0 0 1 15 4c0 10-15 19-15 19Z" fill="#e6edc8" />
            <path d="M60 61h12" stroke="#a8c08a" stroke-width="3" stroke-linecap="round" />
          </svg>
          <p class="intro-copy">Date dein Münster</p>
      </div>
    </header>
    <main id="main-content">
      <h1 id="page-title" class="sr-only">MünsterMatch</h1>
      <div class="workspace">
        <div v-if="searched" class="results-toolbar">
          <div class="result-summary"><h2 id="results-heading">{{ resultHeading }}</h2><span>{{ roundComplete ? shortlist.length : activities.length }} {{ (roundComplete ? shortlist.length : activities.length) === 1 ? 'Aktivität' : 'Aktivitäten' }}</span></div>
          <div v-if="activities.length && !roundComplete" class="decision-progress">
            <span><strong>{{ likedIds.length }}</strong> von 3 gefunden</span>
            <div class="progress-slots" aria-hidden="true"><span v-for="index in 3" :key="index" :class="{ filled: index <= likedIds.length }"><AppIcon v-if="index <= likedIds.length" name="check" :size="14" /><span v-else>{{ index }}</span></span></div>
          </div>
        </div>
        <aside class="search-sidebar" aria-label="Aktivitäten suchen">
          <SearchForm v-model:origin="origin" :loading="loading" @search="search" />
        </aside>
        <section class="results-section" :class="{ 'results-section--with-selection': selected }" :aria-labelledby="searched ? 'results-heading' : undefined" :aria-label="searched ? undefined : 'Entdecken'" :aria-busy="loading">
          <div class="sr-only" role="status" aria-atomic="true">{{ announcement }}</div>
          <p v-if="searchError" class="result-error" role="alert">{{ searchError }}</p>
          <div v-if="searched && !activities.length" class="empty-result" role="status"><AppIcon name="discover" :size="28" /><h3>Gerade keine Aktivitäten gefunden</h3><p>Ändere deine Suchangaben und suche erneut.</p></div>
          <div class="discover-view">
            <div v-if="chosen" class="chosen-result">
              <div class="chosen-heading"><span class="chosen-check" aria-hidden="true"><AppIcon name="check" :size="24" /></span><div><p class="eyebrow">Weniger überlegen. Los geht’s.</p><h3 ref="chosenHeading" tabindex="-1">Deine Auszeit steht fest.</h3></div></div>
              <ActivityCard :activity="chosen" @details="openDetails(chosen)" />
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
        </section>
      </div>
    </main>
    <ActivityDetails ref="details" :activity="detailActivity" />
  </div>
</template>
