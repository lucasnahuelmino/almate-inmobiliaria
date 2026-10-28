<script setup lang="ts">
/** Bloque de estado vacío con acción opcional. */
withDefaults(
  defineProps<{
    title: string;
    description?: string;
    actionLabel?: string;
  }>(),
  { description: "", actionLabel: "" },
);

defineEmits<{ action: [] }>();
</script>

<template>
  <div class="state-block">
    <svg width="34" height="34" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M4 20V9.5L12 4l8 5.5V20M9 20v-6h6v6"
        fill="none"
        stroke="currentColor"
        stroke-width="1.4"
        stroke-linejoin="round"
      />
    </svg>
    <h3>{{ title }}</h3>
    <p v-if="description">{{ description }}</p>
    <button v-if="actionLabel" class="btn btn--ghost" type="button" @click="$emit('action')">
      {{ actionLabel }}
    </button>
    <slot />
  </div>
</template>
