<script setup lang="ts">
/** Error recuperable: explica qué falló y ofrece reintentar. */
withDefaults(
  defineProps<{
    title?: string;
    message: string;
    retryLabel?: string;
  }>(),
  { title: "Algo salió mal", retryLabel: "Reintentar" },
);

defineEmits<{ retry: [] }>();
</script>

<template>
  <div class="state-block state-block--error" role="alert">
    <svg width="34" height="34" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.4" />
      <path d="M12 7.5v5.5M12 16.2v.6" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
    </svg>
    <h3>{{ title }}</h3>
    <p>{{ message }}</p>
    <div class="row">
      <button class="btn btn--ghost" type="button" @click="$emit('retry')">
        {{ retryLabel }}
      </button>
      <slot />
    </div>
  </div>
</template>

<style scoped>
.state-block--error {
  border-color: #ecd0cb;
  background: var(--color-danger-bg);
  color: var(--color-danger);
}

.state-block--error p {
  color: var(--color-danger);
}
</style>
