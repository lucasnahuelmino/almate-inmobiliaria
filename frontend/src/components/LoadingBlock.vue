<script setup lang="ts">
/** Estado de carga reutilizable (spinner + texto). */
defineProps<{ label?: string }>();
</script>

<template>
  <div class="loading-row" role="status" aria-live="polite">
    <span class="spinner" aria-hidden="true" />
    <span>{{ label ?? "Cargando…" }}</span>
  </div>
</template>
