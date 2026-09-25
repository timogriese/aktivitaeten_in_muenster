<script setup lang="ts">
import type { Activity } from '~/types/explore'

const props = defineProps<{ activity: Activity; disabled?: boolean }>()
const emit = defineEmits<{ decide: [id: string, interested: boolean]; details: [] }>()
const surface = ref<HTMLElement>()
const dragX = ref(0)
const dragging = ref(false)
const leaving = ref<'yes' | 'no' | null>(null)
const reducedMotion = ref(false)
let pointer: { id: number; x: number; y: number } | null = null
let timer: ReturnType<typeof setTimeout> | undefined
let motionPreference: MediaQueryList | undefined
const locked = computed(() => Boolean(props.disabled || leaving.value))
const cardStyle = computed(() => {
  if (leaving.value || !dragging.value) return undefined
  return { transform: `translateX(${dragX.value}px) rotate(${reducedMotion.value ? 0 : dragX.value / 25}deg)` }
})

function releasePointer() {
  if (pointer && surface.value?.hasPointerCapture(pointer.id)) surface.value.releasePointerCapture(pointer.id)
  pointer = null
  dragging.value = false
  dragX.value = 0
}

function reset() {
  clearTimeout(timer)
  leaving.value = null
  releasePointer()
}

function decide(interested: boolean) {
  if (locked.value) return
  const id = props.activity.id
  releasePointer()
  leaving.value = interested ? 'yes' : 'no'
  const finish = () => {
    if (!props.disabled && props.activity.id === id) emit('decide', id, interested)
    leaving.value = null
  }
  if (reducedMotion.value) finish()
  else timer = setTimeout(finish, 220)
}

function pointerDown(event: PointerEvent) {
  if (locked.value || !event.isPrimary || event.button !== 0) return
  if ((event.target as HTMLElement).closest('button, a, input')) return
  pointer = { id: event.pointerId, x: event.clientX, y: event.clientY }
}

function pointerMove(event: PointerEvent) {
  if (!pointer || pointer.id !== event.pointerId || locked.value) return
  const x = event.clientX - pointer.x
  const y = event.clientY - pointer.y
  if (!dragging.value) {
    if (Math.abs(y) > 10 && Math.abs(y) > Math.abs(x)) { releasePointer(); return }
    if (Math.abs(x) < 10) return
    surface.value?.setPointerCapture(event.pointerId)
    dragging.value = true
  }
  dragX.value = x
}

function pointerUp(event: PointerEvent) {
  if (!pointer || pointer.id !== event.pointerId) return
  const distance = dragX.value
  const threshold = Math.min(90, (surface.value?.clientWidth ?? 400) * 0.22)
  releasePointer()
  if (Math.abs(distance) >= threshold) decide(distance > 0)
}

function updateMotionPreference() { reducedMotion.value = motionPreference?.matches ?? false }
watch(() => props.activity.id, reset)
watch(() => props.disabled, (disabled) => { if (disabled) reset() })
onMounted(() => {
  motionPreference = window.matchMedia('(prefers-reduced-motion: reduce)')
  updateMotionPreference()
  motionPreference.addEventListener('change', updateMotionPreference)
})
onBeforeUnmount(() => {
  reset()
  motionPreference?.removeEventListener('change', updateMotionPreference)
})
</script>

<template>
  <div class="activity-decision">
    <div class="swipe-stage">
      <div ref="surface" class="swipe-surface" :class="{ 'is-dragging': dragging, 'swipe-yes': leaving === 'yes', 'swipe-no': leaving === 'no' }" :style="cardStyle" @pointerdown="pointerDown" @pointermove="pointerMove" @pointerup="pointerUp" @pointercancel="releasePointer" @lostpointercapture="releasePointer" @dragstart.prevent>
        <ActivityCard :key="activity.id" :activity="activity" @details="emit('details')" />
        <span v-if="dragging || leaving" class="swipe-verdict" :class="{ 'swipe-verdict--no': leaving === 'no' || (!leaving && dragX < 0) }" aria-hidden="true">{{ leaving === 'yes' || (!leaving && dragX > 0) ? 'Spannend' : 'Nicht für mich' }}</span>
      </div>
    </div>
    <div class="decision-actions" role="group" aria-label="Aktivität bewerten">
      <div class="decision-option">
        <button class="decision-button decision-button--no" type="button" aria-label="Nicht für mich" :disabled="locked" @click="decide(false)"><AppIcon name="close" :size="34" /></button>
        <span aria-hidden="true">Nicht für mich</span>
      </div>
      <div class="decision-option">
        <button class="decision-button decision-button--yes" type="button" aria-label="Spannend" :disabled="locked" @click="decide(true)"><AppIcon name="heart" :size="32" /></button>
        <span aria-hidden="true">Spannend</span>
      </div>
    </div>
  </div>
</template>
