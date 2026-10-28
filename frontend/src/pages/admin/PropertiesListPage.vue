<script setup lang="ts">
/**
 * Listado administrativo de propiedades: búsqueda, filtros, paginación y
 * acciones rápidas de estado (publicar, reservar, vender, archivar, eliminar).
 */
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { ApiError, api } from "../../api/client";
import type { PropertyAdmin } from "../../api/types";
import { useAuthStore } from "../../stores/auth";
import LoadingBlock from "../../components/LoadingBlock.vue";
import ErrorState from "../../components/ErrorState.vue";
import EmptyState from "../../components/EmptyState.vue";
import StatusBadge from "../../components/StatusBadge.vue";
import { formatDate, formatPrice } from "../../utils/format";

interface AdminPage {
  items: PropertyAdmin[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

const route = useRoute();
const auth = useAuthStore();

const items = ref<PropertyAdmin[]>([]);
const total = ref(0);
const pages = ref(1);
const page = ref(1);
const loading = ref(true);
const error = ref<string | null>(null);
const actionError = ref<string | null>(null);
const busyCode = ref<string | null>(null);

const search = ref("");
const publicationStatus = ref("");
const commercialStatus = ref("");
const operation = ref("");
const propertyType = ref("");
const pageSize = 15;

const canDelete = computed(() => auth.isAdmin);

function currentQuery(): Record<string, string | number> {
  return {
    q: search.value,
    publication_status: publicationStatus.value,
    commercial_status: commercialStatus.value,
    operation: operation.value,
    type: propertyType.value,
    page: page.value,
    page_size: pageSize,
  };
}

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(currentQuery())) {
      if (value !== "" && value !== undefined && value !== null) params.set(key, String(value));
    }
    const response = await api.get<AdminPage>(`/admin/properties?${params.toString()}`, {
      auth: true,
    });
    items.value = response.items;
    total.value = response.total;
    pages.value = response.pages;
  } catch (caught) {
    error.value =
      caught instanceof ApiError ? caught.message : "No pudimos cargar las propiedades.";
  } finally {
    loading.value = false;
  }
}

function applyFilters() {
  page.value = 1;
  void load();
}

function goToPage(next: number) {
  if (next < 1 || next > pages.value || next === page.value) return;
  page.value = next;
  void load();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function clearFilters() {
  search.value = "";
  publicationStatus.value = "";
  commercialStatus.value = "";
  operation.value = "";
  propertyType.value = "";
  page.value = 1;
  void load();
}

async function setStatus(code: string, payload: Record<string, string>) {
  busyCode.value = code;
  actionError.value = null;
  try {
    const updated = await api.post<PropertyAdmin>(`/admin/properties/${code}/status`, payload, {
      auth: true,
    });
    const index = items.value.findIndex((item) => item.code === code);
    if (index >= 0) items.value[index] = updated;
  } catch (caught) {
    actionError.value =
      caught instanceof ApiError ? caught.message : "No pudimos actualizar el estado.";
  } finally {
    busyCode.value = null;
  }
}

async function removeProperty(property: PropertyAdmin) {
  const confirmed = window.confirm(
    `¿Eliminar "${property.title}"? Se borran la ficha y sus fotografías. Esta acción no se puede deshacer.`,
  );
  if (!confirmed) return;

  busyCode.value = property.code;
  actionError.value = null;
  try {
    await api.delete(`/admin/properties/${property.code}`, { auth: true });
    items.value = items.value.filter((item) => item.code !== property.code);
    total.value = Math.max(0, total.value - 1);
  } catch (caught) {
    actionError.value =
      caught instanceof ApiError ? caught.message : "No pudimos eliminar la propiedad.";
  } finally {
    busyCode.value = null;
  }
}

watch(
  () => route.query,
  () => {
    if (typeof route.query.q === "string") search.value = route.query.q;
  },
);

onMounted(() => {
  if (typeof route.query.q === "string") search.value = route.query.q;
  void load();
});
</script>

<template>
  <div>
    <div class="admin-head">
      <div>
        <h1>Propiedades</h1>
        <p class="muted small">
          <strong class="numeric">{{ total }}</strong> fichas en el panel
        </p>
      </div>
      <RouterLink class="btn btn--primary btn--sm" to="/admin/propiedades/nueva">
        + Nueva propiedad
      </RouterLink>
    </div>

    <form class="panel admin-filters" aria-label="Filtros del listado" @submit.prevent="applyFilters">
      <div class="admin-filters__grid">
        <div class="field">
          <label for="adm-q">Buscar</label>
          <input
            id="adm-q"
            v-model="search"
            class="input"
            type="search"
            placeholder="Código, título o localidad"
          />
        </div>

        <div class="field">
          <label for="adm-publicacion">Publicación</label>
          <select id="adm-publicacion" v-model="publicationStatus" class="select">
            <option value="">Todas</option>
            <option value="published">Publicadas</option>
            <option value="draft">Borradores</option>
            <option value="archived">Archivadas</option>
          </select>
        </div>

        <div class="field">
          <label for="adm-comercial">Estado comercial</label>
          <select id="adm-comercial" v-model="commercialStatus" class="select">
            <option value="">Todos</option>
            <option value="available">Disponibles</option>
            <option value="reserved">Reservadas</option>
            <option value="sold">Vendidas</option>
            <option value="rented">Alquiladas</option>
          </select>
        </div>

        <div class="field">
          <label for="adm-operacion">Operación</label>
          <select id="adm-operacion" v-model="operation" class="select">
            <option value="">Todas</option>
            <option value="buy">Venta</option>
            <option value="rent">Alquiler</option>
            <option value="temporary_rent">Alquiler temporal</option>
          </select>
        </div>

        <div class="field">
          <label for="adm-tipo">Tipo</label>
          <select id="adm-tipo" v-model="propertyType" class="select">
            <option value="">Todos</option>
            <option value="apartment">Departamento</option>
            <option value="house">Casa</option>
            <option value="ph">PH</option>
            <option value="land">Terreno</option>
            <option value="commercial">Local comercial</option>
            <option value="office">Oficina</option>
            <option value="garage">Cochera</option>
          </select>
        </div>
      </div>

      <div class="row">
        <button class="btn btn--primary btn--sm" type="submit">Aplicar filtros</button>
        <button class="btn btn--ghost btn--sm" type="button" @click="clearFilters">
          Limpiar filtros
        </button>
      </div>
    </form>

    <div v-if="actionError" class="alert alert--error" role="alert">
      {{ actionError }}
    </div>

    <LoadingBlock v-if="loading" label="Cargando propiedades…" />
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <EmptyState
      v-else-if="!items.length"
      title="No hay propiedades con esos filtros"
      description="Probá quitar algún filtro o creá una ficha nueva."
      action-label="Limpiar filtros"
      @action="clearFilters"
    />

    <template v-else>
      <div class="panel panel--flush table-wrap">
        <table class="table">
          <thead>
            <tr>
              <th scope="col">Propiedad</th>
              <th scope="col">Precio</th>
              <th scope="col">Estados</th>
              <th scope="col">Actualizada</th>
              <th scope="col"><span class="sr-only">Acciones</span></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="property in items" :key="property.code">
              <td>
                <div class="prop-cell">
                  <img
                    v-if="property.image"
                    class="prop-cell__thumb"
                    :src="property.image.url"
                    :alt="property.image.alt || property.title"
                    loading="lazy"
                  />
                  <div v-else class="prop-cell__thumb prop-cell__thumb--empty" aria-hidden="true">
                    —
                  </div>
                  <div>
                    <RouterLink
                      class="prop-cell__title"
                      :to="{ name: 'admin-property-edit', params: { id: property.code } }"
                    >
                      {{ property.title }}
                    </RouterLink>
                    <span class="prop-cell__meta small muted">
                      {{ property.code }} · {{ property.locality ?? "—" }}
                      <template v-if="property.is_development"> · Emprendimiento</template>
                    </span>
                  </div>
                </div>
              </td>
              <td class="numeric">
                {{ formatPrice(property.price, property.currency, property.price_unit) }}
              </td>
              <td>
                <StatusBadge
                  :commercial="property.commercial_status"
                  :publication="property.publication_status"
                  :featured="property.is_featured"
                />
              </td>
              <td class="small muted">{{ formatDate(property.updated_at) }}</td>
              <td>
                <div class="actions">
                  <RouterLink
                    class="btn btn--ghost btn--sm"
                    :to="{ name: 'admin-property-edit', params: { id: property.code } }"
                  >
                    Editar
                  </RouterLink>

                  <button
                    v-if="property.publication_status !== 'published'"
                    class="btn btn--sage btn--sm"
                    type="button"
                    :disabled="busyCode === property.code"
                    @click="setStatus(property.code, { publication_status: 'published' })"
                  >
                    Publicar
                  </button>
                  <button
                    v-else
                    class="btn btn--ghost btn--sm"
                    type="button"
                    :disabled="busyCode === property.code"
                    @click="setStatus(property.code, { publication_status: 'draft' })"
                  >
                    Despublicar
                  </button>

                  <button
                    v-if="property.commercial_status === 'available'"
                    class="btn btn--ghost btn--sm"
                    type="button"
                    :disabled="busyCode === property.code"
                    @click="setStatus(property.code, { commercial_status: 'reserved' })"
                  >
                    Reservar
                  </button>
                  <button
                    v-if="property.commercial_status !== 'sold' && property.operation === 'buy'"
                    class="btn btn--ghost btn--sm"
                    type="button"
                    :disabled="busyCode === property.code"
                    @click="setStatus(property.code, { commercial_status: 'sold' })"
                  >
                    Vendida
                  </button>
                  <button
                    v-if="property.commercial_status !== 'rented' && property.operation !== 'buy'"
                    class="btn btn--ghost btn--sm"
                    type="button"
                    :disabled="busyCode === property.code"
                    @click="setStatus(property.code, { commercial_status: 'rented' })"
                  >
                    Alquilada
                  </button>

                  <button
                    v-if="property.publication_status !== 'archived'"
                    class="btn btn--ghost btn--sm"
                    type="button"
                    :disabled="busyCode === property.code"
                    @click="setStatus(property.code, { publication_status: 'archived' })"
                  >
                    Archivar
                  </button>

                  <button
                    v-if="canDelete"
                    class="btn btn--danger btn--sm"
                    type="button"
                    :disabled="busyCode === property.code"
                    @click="removeProperty(property)"
                  >
                    Eliminar
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <nav class="pagination" aria-label="Paginación de propiedades">
        <button type="button" :disabled="page <= 1" @click="goToPage(page - 1)">Anterior</button>
        <span class="small muted numeric">Página {{ page }} de {{ Math.max(pages, 1) }}</span>
        <button type="button" :disabled="page >= pages" @click="goToPage(page + 1)">Siguiente</button>
      </nav>
    </template>
  </div>
</template>

<style scoped>
.admin-head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.admin-head h1 {
  font-size: var(--text-xl);
}

.admin-filters {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.admin-filters__grid {
  display: grid;
  gap: var(--space-4);
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 190px), 1fr));
}

.prop-cell {
  display: flex;
  gap: var(--space-3);
  align-items: center;
  min-width: 240px;
}

.prop-cell__thumb {
  width: 58px;
  height: 44px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  background: var(--color-bg-alt);
  flex-shrink: 0;
}

.prop-cell__thumb--empty {
  display: grid;
  place-items: center;
  color: var(--color-stone-dark);
}

.prop-cell__title {
  display: block;
  font-weight: 600;
  text-decoration: none;
}

.prop-cell__title:hover {
  color: var(--color-bronze-dark);
}

.prop-cell__meta {
  display: block;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  justify-content: flex-end;
  min-width: 320px;
}
</style>
