<script setup lang="ts">
import type { Activity } from '~/types/explore'
const props = defineProps<{ activity: Activity }>()
defineEmits<{ details: [] }>()
const categoryIcon = computed(() => ({ 'Natur & draußen': 'leaf', 'Kunst & Kultur': 'culture', 'Sport & Bewegung': 'sport', 'Musik & Bühne': 'music' }[props.activity.category] || 'discover'))
</script>

<template>
  <article class="activity-card" :aria-label="activity.title">
    <div class="card-visual">
      <ActivityImage :src="activity.imageUrl" :title="activity.title" />
      <span class="image-location"><AppIcon name="pin" :size="15" /> Münster</span>
      <span v-if="activity.kind === 'event'" class="event-badge">Event</span>
    </div>
    <div class="card-content">
      <span class="category" :data-category="categoryIcon"><AppIcon :name="categoryIcon" :size="17" />{{ activity.category }}</span>
      <h3>{{ activity.title }}</h3>
      <p class="card-description">{{ activity.description }}</p>
      <div v-if="activity.timingLabel || activity.travelTimeMinutes != null" class="timing-info">
        <span v-if="activity.timingLabel"><AppIcon name="clock" :size="16" />{{ activity.timingLabel }}</span>
        <span v-if="activity.travelTimeMinutes != null"><AppIcon name="arrow" :size="16" />{{ activity.travelTimeMinutes }} Min. Anreise</span>
      </div>
      <button class="primary-button card-more" type="button" @click="$emit('details')">Mehr erfahren <AppIcon name="arrow" :size="18" /></button>
      <slot name="actions" />
    </div>
  </article>
</template>
