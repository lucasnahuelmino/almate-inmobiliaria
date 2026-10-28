<script setup lang="ts">
/** Panel de filtros combinables del catálogo (formulario controlado). */
import { reactive, watch } from "vue";
import type { CatalogMeta } from "../api/types";
import {
  activeFilterCount,
  defaultFilters,
  SORT_OPTIONS,
  type CatalogFilters,
} from "../utils/filters";

const props = defineProps<{
  filters: CatalogFilters;
  meta: CatalogMeta | null;
  operationLabel?: string;
}>();

const emit = defineEmits<{
  apply: [filters: CatalogFilters];
  reset: [];
}>();

const form = reactive<CatalogFilters>({ ...defaultFilters(), ...props.filters });

watch(
  () => props.filters,
  (next) => Object.assign(form, defaultFilters(), next),
  { deep: true },
);

function submit() {
  emit("apply", { ...form, page: 1 });
}

function applyNow() {
  emit("apply", { ...form, page: 1 });
}

function reset() {
  const keep: CatalogFilters = {
    ...defaultFilters(),
    sort: form.sort,
    favoritesOnly: form.favoritesOnly,
  };
  Object.assign(form, keep);
  emit("reset");
}

const count = () => activeFilterCount(form);
</script>

<template>
  <form class="filters panel" aria-label="Filtros de búsqueda" @submit.prevent="submit">
    <div class="filters__search">
      <label class="sr-only" for="filtro-texto">Buscar por palabra clave</label>
      <input
        id="filtro-texto"
        v-model="form.q"
        class="input"
        type="search"
        placeholder="Buscar por código, barrio o palabra clave"
        autocomplete="off"
      />
      <button class="btn btn--primary" type="submit">Buscar</button>
    </div>

    <div class="filters__grid">
      <div class="field">
        <label for="filtro-tipo">Tipo de propiedad</label>
        <select id="filtro-tipo" v-model="form.type" class="select" @change="applyNow">
          <option value="">Todos</option>
          <option
            v-for="option in meta?.property_types ?? []"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </option>
        </select>
      </div>

      <div class="field">
        <label for="filtro-localidad">Localidad</label>
        <select id="filtro-localidad" v-model="form.locality" class="select" @change="applyNow">
          <option value="">Todas</option>
          <option v-for="locality in meta?.localities ?? []" :key="locality" :value="locality">
            {{ locality }}
          </option>
        </select>
      </div>

      <div class="field">
        <label for="filtro-precio-min">Precio mínimo</label>
        <input
          id="filtro-precio-min"
          v-model="form.minPrice"
          class="input numeric"
          type="number"
          inputmode="numeric"
          min="0"
          placeholder="Sin mínimo"
        />
      </div>

      <div class="field">
        <label for="filtro-precio-max">Precio máximo</label>
        <input
          id="filtro-precio-max"
          v-model="form.maxPrice"
          class="input numeric"
          type="number"
          inputmode="numeric"
          min="0"
          placeholder="Sin máximo"
        />
      </div>

      <div class="field">
        <label for="filtro-dormitorios">Dormitorios mínimos</label>
        <select id="filtro-dormitorios" v-model="form.bedrooms" class="select" @change="applyNow">
          <option value="">Cualquiera</option>
          <option v-for="n in 6" :key="n" :value="String(n - 1)">
            {{ n - 1 === 0 ? "Sin dormitorios" : `+ ${n - 1}` }}
          </option>
        </select>
      </div>

      <div class="field">
        <label for="filtro-banos">Baños mínimos</label>
        <select id="filtro-banos" v-model="form.bathrooms" class="select" @change="applyNow">
          <option value="">Cualquiera</option>
          <option v-for="n in 4" :key="n" :value="String(n - 1)">
            {{ n - 1 === 0 ? "Sin baños" : `+ ${n - 1}` }}
          </option>
        </select>
      </div>

      <div class="field">
        <label for="filtro-superficie-min">Superficie mínima (m²)</label>
        <input
          id="filtro-superficie-min"
          v-model="form.minSurface"
          class="input numeric"
          type="number"
          inputmode="numeric"
          min="0"
          placeholder="Sin mínimo"
        />
      </div>

      <div class="field">
        <label for="filtro-superficie-max">Superficie máxima (m²)</label>
        <input
          id="filtro-superficie-max"
          v-model="form.maxSurface"
          class="input numeric"
          type="number"
          inputmode="numeric"
          min="0"
          placeholder="Sin máximo"
        />
      </div>

      <div class="field">
        <label for="filtro-orden">Ordenar por</label>
        <select id="filtro-orden" v-model="form.sort" class="select" @change="applyNow">
          <option v-for="option in SORT_OPTIONS" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
      </div>
    </div>

    <div class="filters__checks">
      <label class="checkbox">
        <input v-model="form.garage" type="checkbox" @change="applyNow" />
        Con cochera
      </label>
      <label class="checkbox">
        <input v-model="form.apto" type="checkbox" @change="applyNow" />
        Apto profesional
      </label>
      <span v-if="operationLabel" class="filters__operation">
        Operación: <strong>{{ operationLabel }}</strong>
      </span>
    </div>

    <div class="filters__actions">
      <button class="btn btn--primary" type="submit">Aplicar filtros</button>
      <button
        v-if="count() > 0"
        class="btn btn--ghost"
        type="button"
        @click="reset"
      >
        Limpiar filtros ({{ count() }})
      </button>
    </div>
  </form>
</template>

<style scoped>
.filters {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.filters__search {
  display: flex;
  gap: var(--space-3);
}

.filters__search .input {
  flex: 1;
}

.filters__grid {
  display: grid;
  gap: var(--space-4);
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 200px), 1fr));
}

.filters__checks {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-4);
  padding-top: var(--space-2);
  border-top: 1px dashed var(--color-line);
}

.filters__operation {
  font-size: var(--text-sm);
  color: var(--color-stone-dark);
}

.filters__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}

@media (max-width: 640px) {
  .filters__search {
    flex-direction: column;
  }
}
</style>
