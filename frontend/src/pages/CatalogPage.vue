<script setup lang="ts">
/**
 * Catálogo público: Comprar / Alquilar / Alquiler temporal / Emprendimientos.
 * Los filtros viven en la URL (se comparten y vuelven atrás sin perder nada).
 */
import { computed, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ApiError, api } from "../api/client";
import type { PropertySummary } from "../api/types";
import {
  activeFilterCount,
  defaultFilters,
  parseFilters,
  toApiParams,
  toRouteQuery,
  type CatalogMode,
  type CatalogFilters,
} from "../utils/filters";
import FilterPanel from "../components/FilterPanel.vue";
import PropertyCard from "../components/PropertyCard.vue";
import PaginationNav from "../components/PaginationNav.vue";
import LoadingBlock from "../components/LoadingBlock.vue";
import ErrorState from "../components/ErrorState.vue";
import EmptyState from "../components/EmptyState.vue";
import { useFavoritesStore } from "../stores/favorites";
import { useSettingsStore } from "../stores/settings";

const route = useRoute();
const router = useRouter();
const favorites = useFavoritesStore();
const settingsStore = useSettingsStore();

const mode = computed(() => (route.meta.mode as CatalogMode | undefined) ?? "all");

const MODE_COPY: Record<CatalogMode, { title: string; lede: string; label: string }> = {
  buy: {
    title: "Propiedades en venta",
    lede: "Departamentos, casas y locales para comprar en el sur del Gran Buenos Aires.",
    label: "Comprar",
  },
  rent: {
    title: "Propiedades en alquiler",
    lede: "Opciones residenciales con expensas, requisitos y contratos claros.",
    label: "Alquilar",
  },
  temporary_rent: {
    title: "Alquiler temporal",
    lede: "Estadías cortas, amobladas y listas para mudarse por días o semanas.",
    label: "Alquiler temporal",
  },
  development: {
    title: "Emprendimientos",
    lede: "Unidades nuevas y desarrollos en pozo con entrega en obra o en tiempo.",
    label: "Emprendimientos",
  },
  all: {
    title: "Todas las propiedades",
    lede: "Explorá el catálogo completo del estudio.",
    label: "Catálogo",
  },
};

const copy = computed(() => MODE_COPY[mode.value] ?? MODE_COPY.all);

const filters = ref<CatalogFilters>(defaultFilters());
const items = ref<PropertySummary[]>([]);
const total = ref(0);
const pages = ref(1);
const loading = ref(true);
const error = ref<string | null>(null);

const filterCount = computed(() => activeFilterCount(filters.value));
const favoritesOnly = computed(() => filters.value.favoritesOnly);

/** Los favoritos sólo existen en este dispositivo: se filtra en el cliente. */
const visibleItems = computed(() =>
  favoritesOnly.value ? items.value.filter((item) => favorites.has(item.code)) : items.value,
);

const showingFavorites = computed(() => favoritesOnly.value);

function syncFromUrl() {
  filters.value = parseFilters(route.query);
}

async function fetchCatalog() {
  loading.value = true;
  error.value = null;
  try {
    // Los favoritos sólo existen en este dispositivo: se pide una página amplia
    // y se filtra en el cliente por los códigos guardados.
    const requestFilters = favoritesOnly.value
      ? { ...filters.value, page: 1 }
      : filters.value;
    const pageSize = favoritesOnly.value ? 60 : undefined;

    const params = toApiParams(requestFilters, mode.value, pageSize);
    const query = new URLSearchParams();
    for (const [key, value] of Object.entries(params)) query.set(key, String(value));

    const response = await api.get<{
      items: PropertySummary[];
      total: number;
      page: number;
      pages: number;
    }>(`/properties?${query.toString()}`);

    if (favoritesOnly.value) {
      items.value = response.items.filter((item) => favorites.has(item.code));
      total.value = items.value.length;
      pages.value = 1;
    } else {
      items.value = response.items;
      total.value = response.total;
      pages.value = response.pages;
    }
  } catch (caught) {
    error.value =
      caught instanceof ApiError ? caught.message : "No pudimos cargar el catálogo.";
  } finally {
    loading.value = false;
  }
}

function pushFilters(next: CatalogFilters) {
  filters.value = next;
  void router.push({ path: route.path, query: toRouteQuery(next) });
}

function onPageChange(page: number) {
  pushFilters({ ...filters.value, page });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function clearAll() {
  pushFilters({ ...defaultFilters(), sort: filters.value.sort });
}

function clearFavoritesFilter() {
  pushFilters({ ...filters.value, favoritesOnly: false, page: 1 });
}

/** Cambio rápido de orden desde la barra de resultados. */
function onSortChange(event: Event) {
  const select = event.target as HTMLSelectElement;
  pushFilters({
    ...filters.value,
    sort: select.value as CatalogFilters["sort"],
    page: 1,
  });
}

watch(
  () => route.fullPath,
  () => {
    syncFromUrl();
    void fetchCatalog();
  },
);

onMounted(() => {
  syncFromUrl();
  void fetchCatalog();
  void settingsStore.loadMeta();
});
</script>

<template>
  <div>
    <header class="catalog-head">
      <div class="container">
        <span class="eyebrow">{{ copy.label }}</span>
        <h1>{{ copy.title }}</h1>
        <p class="lede">{{ copy.lede }}</p>
      </div>
    </header>

    <section class="section catalog-body">
      <div class="container">
        <FilterPanel
          :filters="filters"
          :meta="settingsStore.meta"
          :operation-label="copy.label"
          @apply="pushFilters"
          @reset="clearAll"
        />

        <div class="catalog-toolbar">
          <p class="catalog-toolbar__count" role="status" aria-live="polite">
            <template v-if="loading">Buscando propiedades…</template>
            <template v-else-if="error">—</template>
            <template v-else>
              <strong class="numeric">{{ showingFavorites ? visibleItems.length : total }}</strong>
              {{
                showingFavorites
                  ? visibleItems.length === 1
                    ? "favorito guardado"
                    : "favoritos guardados"
                  : total === 1
                    ? "propiedad encontrada"
                    : "propiedades encontradas"
              }}
              <span v-if="filterCount > 0" class="muted">
                · {{ filterCount }} {{ filterCount === 1 ? "filtro activo" : "filtros activos" }}
              </span>
            </template>
          </p>

          <div class="catalog-toolbar__actions">
            <label class="sr-only" for="orden-rapido">Ordenar resultados</label>
            <select
              id="orden-rapido"
              class="select select--inline"
              :value="filters.sort"
              @change="onSortChange"
            >
              <option value="recent">Más recientes</option>
              <option value="price_asc">Menor precio</option>
              <option value="price_desc">Mayor precio</option>
              <option value="oldest">Más antiguas</option>
            </select>
            <button v-if="filterCount > 0" class="btn btn--ghost btn--sm" type="button" @click="clearAll">
              Limpiar filtros
            </button>
          </div>
        </div>

        <div v-if="showingFavorites" class="alert alert--info favorites-note">
          <span>
            Estás viendo tus favoritos guardados en <strong>este dispositivo</strong>. No se
            sincronizan con una cuenta ni viajan al servidor.
          </span>
          <button class="link-btn" type="button" @click="clearFavoritesFilter">
            Ver todo el catálogo
          </button>
        </div>

        <LoadingBlock v-if="loading" label="Cargando propiedades…" />

        <ErrorState v-else-if="error" :message="error" @retry="fetchCatalog" />

        <EmptyState
          v-else-if="!visibleItems.length"
          :title="showingFavorites ? 'Todavía no guardaste favoritos' : 'No hay propiedades con esos filtros'"
          :description="
            showingFavorites
              ? 'Tocá el corazón de cualquier tarjeta para guardarla en este dispositivo.'
              : 'Probá ampliar el rango de precios o quitar algún filtro para ver más resultados.'
          "
          :action-label="showingFavorites ? 'Ir al catálogo' : 'Limpiar filtros'"
          @action="showingFavorites ? clearFavoritesFilter() : clearAll()"
        />

        <template v-else>
          <div class="grid grid--cards">
            <PropertyCard v-for="property in visibleItems" :key="property.code" :property="property" />
          </div>
          <PaginationNav
            v-if="!showingFavorites"
            :page="filters.page"
            :pages="pages"
            :total="total"
            @change="onPageChange"
          />
        </template>
      </div>
    </section>
  </div>
</template>

<style scoped>
.catalog-head {
  padding-block: clamp(2rem, 1.5rem + 3vw, 3.5rem) 0;
}

.catalog-head h1 {
  margin-top: var(--space-2);
}

.catalog-head .lede {
  margin-top: var(--space-3);
}

.catalog-body {
  padding-top: var(--space-6);
}

.catalog-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-block: var(--space-5) var(--space-4);
}

.catalog-toolbar__count {
  font-size: var(--text-md);
}

.catalog-toolbar__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.select--inline {
  width: auto;
  min-width: 190px;
}

.favorites-note {
  margin-bottom: var(--space-5);
}

@media (max-width: 640px) {
  .catalog-toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .select--inline {
    width: 100%;
  }
}
</style>
