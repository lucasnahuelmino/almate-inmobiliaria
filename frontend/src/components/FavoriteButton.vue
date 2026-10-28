<script setup lang="ts">
import { computed } from "vue";
import { useFavoritesStore } from "../stores/favorites";

const props = defineProps<{ code: string }>();
const favorites = useFavoritesStore();

const active = computed(() => favorites.has(props.code));

function toggle() {
  favorites.toggle(props.code);
}
</script>

<template>
  <button
    class="fav"
    type="button"
    :class="{ 'fav--active': active }"
    :aria-pressed="active"
    :title="active ? 'Quitar de favoritos' : 'Guardar en favoritos'"
    @click.stop.prevent="toggle"
  >
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M12 20.5 4.7 13a4.6 4.6 0 0 1 0-6.5 4.6 4.6 0 0 1 6.5 0l.8.8.8-.8a4.6 4.6 0 0 1 6.5 0 4.6 4.6 0 0 1 0 6.5Z"
        :fill="active ? 'currentColor' : 'none'"
        stroke="currentColor"
        stroke-width="1.6"
      />
    </svg>
    <span class="sr-only">{{ active ? "Quitar de favoritos" : "Guardar en favoritos" }}</span>
  </button>
</template>

<style scoped>
.fav {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.92);
  color: var(--color-ink-soft);
  border: 1px solid var(--color-line);
  transition:
    color var(--fast),
    transform var(--fast);
}

.fav:hover {
  color: var(--color-bronze-dark);
  transform: translateY(-1px);
}

.fav--active {
  color: var(--color-bronze-dark);
}
</style>
