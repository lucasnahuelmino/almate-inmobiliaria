<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ page: number; pages: number; total: number }>();
const emit = defineEmits<{ change: [page: number] }>();

/** Secuencia de números visible (con puntos suspensivos cuando hay saltos). */
const visible = computed<(number | "…")[]>(() => {
  const { pages, page } = props;
  if (pages <= 7) return Array.from({ length: pages }, (_, index) => index + 1);

  const items = new Set<number>([1, pages, page, page - 1, page + 1]);
  const sorted = [...items].filter((item) => item >= 1 && item <= pages).sort((a, b) => a - b);

  const result: (number | "…")[] = [];
  let previous = 0;
  for (const item of sorted) {
    if (previous && item - previous > 1) result.push("…");
    result.push(item);
    previous = item;
  }
  return result;
});

function go(page: number) {
  if (page < 1 || page > props.pages || page === props.page) return;
  emit("change", page);
}
</script>

<template>
  <nav v-if="pages > 1" class="pagination" aria-label="Paginación de resultados">
    <button type="button" :disabled="page <= 1" @click="go(page - 1)">Anterior</button>

    <template v-for="(item, index) in visible" :key="`${item}-${index}`">
      <span v-if="item === '…'" class="muted" aria-hidden="true">…</span>
      <button
        v-else
        type="button"
        :aria-current="item === page ? 'page' : undefined"
        :aria-label="`Página ${item}`"
        @click="go(item)"
      >
        {{ item }}
      </button>
    </template>

    <button type="button" :disabled="page >= pages" @click="go(page + 1)">Siguiente</button>
  </nav>
</template>
