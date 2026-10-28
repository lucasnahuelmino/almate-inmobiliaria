<script setup lang="ts">
/**
 * Bandeja genérica de leads (consultas, tasaciones y publicaciones):
 * búsqueda, filtro por estado, paginación, detalle con notas internas y
 * cambio de estado. Se usa desde las tres páginas del panel.
 */
import { computed, onMounted, ref } from "vue";
import { ApiError, api } from "../../api/client";
import type { LeadLike, LeadPage, LeadStatus, Note } from "../../api/types";
import LoadingBlock from "../LoadingBlock.vue";
import ErrorState from "../ErrorState.vue";
import EmptyState from "../EmptyState.vue";
import { formatDate } from "../../utils/format";

const props = withDefaults(
  defineProps<{
    endpoint: string;
    title: string;
    description?: string;
    /** Filas de detalle que se muestran al expandir un registro. */
    detailFields: (item: LeadLike) => { label: string; value: string }[];
    /** Etiquetas de los estados para la interfaz. */
    statusLabels?: Record<string, string>;
    emptyTitle?: string;
    emptyDescription?: string;
  }>(),
  {
    description: "",
    statusLabels: () => ({
      new: "Nueva",
      following: "En seguimiento",
      answered: "Respondida",
      archived: "Archivada",
    }),
    emptyTitle: "No hay registros",
    emptyDescription: "Cuando lleguen consultas aparecerán acá.",
  },
);

const emit = defineEmits<{ opened: [item: LeadLike] }>();

const items = ref<LeadLike[]>([]);
const total = ref(0);
const pages = ref(1);
const page = ref(1);
const loading = ref(true);
const error = ref<string | null>(null);
const actionError = ref<string | null>(null);
const busyId = ref<number | null>(null);

const search = ref("");
const statusFilter = ref("");
const pageSize = 20;

const expanded = ref<number | null>(null);
const noteText = ref("");
const noteSaving = ref(false);

const filtersActive = computed(() => Boolean(search.value || statusFilter.value));

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const params = new URLSearchParams();
    if (search.value) params.set("q", search.value);
    if (statusFilter.value) params.set("status", statusFilter.value);
    params.set("page", String(page.value));
    params.set("page_size", String(pageSize));

    const response = await api.get<LeadPage<LeadLike>>(
      `${props.endpoint}?${params.toString()}`,
      { auth: true },
    );
    items.value = response.items;
    total.value = response.total;
    pages.value = response.pages;
  } catch (caught) {
    error.value = caught instanceof ApiError ? caught.message : "No pudimos cargar los registros.";
  } finally {
    loading.value = false;
  }
}

function applyFilters() {
  page.value = 1;
  void load();
}

function clearFilters() {
  search.value = "";
  statusFilter.value = "";
  page.value = 1;
  void load();
}

function goToPage(next: number) {
  if (next < 1 || next > pages.value || next === page.value) return;
  page.value = next;
  void load();
}

function toggle(item: LeadLike) {
  expanded.value = expanded.value === item.id ? null : item.id;
  noteText.value = "";
  emit("opened", item);
}

async function changeStatus(item: LeadLike, status: LeadStatus) {
  busyId.value = item.id;
  actionError.value = null;
  try {
    const updated = await api.patch<LeadLike>(`${props.endpoint}/${item.id}`, { status }, { auth: true });
    const index = items.value.findIndex((entry) => entry.id === item.id);
    if (index >= 0) items.value[index] = { ...items.value[index], ...updated };
  } catch (caught) {
    actionError.value =
      caught instanceof ApiError ? caught.message : "No pudimos actualizar el estado.";
  } finally {
    busyId.value = null;
  }
}

async function saveNote(item: LeadLike) {
  const body = noteText.value.trim();
  if (body.length < 2) return;

  noteSaving.value = true;
  actionError.value = null;
  try {
    const note = await api.post<Note>(
      `${props.endpoint}/${item.id}/notes`,
      { body },
      { auth: true },
    );
    const index = items.value.findIndex((entry) => entry.id === item.id);
    if (index >= 0) {
      items.value[index] = { ...items.value[index], notes: [...items.value[index].notes, note] };
    }
    noteText.value = "";
  } catch (caught) {
    actionError.value =
      caught instanceof ApiError ? caught.message : "No pudimos guardar la nota.";
  } finally {
    noteSaving.value = false;
  }
}

function statusLabel(status: string): string {
  return props.statusLabels?.[status] ?? status;
}

/** Cambio de estado desde el <select> del detalle. */
function onStatusChange(item: LeadLike, event: Event) {
  const select = event.target as HTMLSelectElement;
  void changeStatus(item, select.value as LeadStatus);
}

onMounted(() => void load());
</script>

<template>
  <div>
    <div class="admin-head">
      <div>
        <h1>{{ title }}</h1>
        <p class="muted small">
          <strong class="numeric">{{ total }}</strong> registros ·
          {{ description }}
        </p>
      </div>
      <button class="btn btn--ghost btn--sm" type="button" @click="load">Actualizar</button>
    </div>

    <form class="panel inbox-filters" aria-label="Filtros" @submit.prevent="applyFilters">
      <div class="inbox-filters__grid">
        <div class="field">
          <label :for="`inbox-q-${endpoint}`">Buscar</label>
          <input
            :id="`inbox-q-${endpoint}`"
            v-model="search"
            class="input"
            type="search"
            placeholder="Nombre, correo, localidad o mensaje"
          />
        </div>
        <div class="field">
          <label :for="`inbox-status-${endpoint}`">Estado</label>
          <select :id="`inbox-status-${endpoint}`" v-model="statusFilter" class="select">
            <option value="">Todos</option>
            <option value="new">Nuevas</option>
            <option value="following">En seguimiento</option>
            <option value="answered">Respondidas</option>
            <option value="archived">Archivadas</option>
          </select>
        </div>
      </div>
      <div class="row">
        <button class="btn btn--primary btn--sm" type="submit">Aplicar filtros</button>
        <button v-if="filtersActive" class="btn btn--ghost btn--sm" type="button" @click="clearFilters">
          Limpiar filtros
        </button>
      </div>
    </form>

    <div v-if="actionError" class="alert alert--error" role="alert">{{ actionError }}</div>

    <LoadingBlock v-if="loading" label="Cargando registros…" />
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <EmptyState
      v-else-if="!items.length"
      :title="filtersActive ? 'No hay resultados con esos filtros' : emptyTitle"
      :description="filtersActive ? 'Probá con otra búsqueda o estado.' : emptyDescription"
      :action-label="filtersActive ? 'Limpiar filtros' : ''"
      @action="clearFilters"
    />

    <template v-else>
      <ul class="inbox">
        <li v-for="item in items" :key="item.id" class="inbox__item card">
          <button
            class="inbox__summary"
            type="button"
            :aria-expanded="expanded === item.id"
            @click="toggle(item)"
          >
            <div class="inbox__who">
              <strong>{{ item.name }}</strong>
              <span class="small muted">
                {{ item.email }}
                <template v-if="item.phone"> · {{ item.phone }}</template>
              </span>
            </div>
            <span class="inbox__date small muted">{{ formatDate(item.created_at) }}</span>
            <span class="badge" :class="`badge--${item.status}`">{{ statusLabel(item.status) }}</span>
            <span class="inbox__chevron" aria-hidden="true">{{ expanded === item.id ? "−" : "+" }}</span>
          </button>

          <div v-if="expanded === item.id" class="inbox__detail">
            <dl class="inbox__fields">
              <div v-for="row in detailFields(item)" :key="row.label">
                <dt>{{ row.label }}</dt>
                <dd>{{ row.value }}</dd>
              </div>
            </dl>

            <div class="inbox__status-row">
              <label class="small muted" :for="`estado-${item.id}`">Cambiar estado:</label>
              <select
                :id="`estado-${item.id}`"
                class="select select--inline"
                :value="item.status"
                :disabled="busyId === item.id"
                @change="onStatusChange(item, $event)"
              >
                <option value="new">Nueva</option>
                <option value="following">En seguimiento</option>
                <option value="answered">Respondida</option>
                <option value="archived">Archivada</option>
              </select>
            </div>

            <div class="inbox__notes">
              <h3 class="inbox__notes-title">Notas internas</h3>
              <p class="small muted inbox__notes-warning">
                Sólo visibles en el panel: nunca se publican en el sitio.
              </p>

              <p v-if="!item.notes.length" class="small muted">Sin notas todavía.</p>
              <ul v-else class="inbox__notes-list">
                <li v-for="note in item.notes" :key="note.id">
                  <span>{{ note.body }}</span>
                  <time class="small muted">{{ formatDate(note.created_at) }}</time>
                </li>
              </ul>

              <form class="inbox__note-form" @submit.prevent="saveNote(item)">
                <label class="sr-only" :for="`nota-${item.id}`">Nueva nota interna</label>
                <textarea
                  :id="`nota-${item.id}`"
                  v-model="noteText"
                  class="textarea textarea--sm"
                  rows="2"
                  maxlength="2000"
                  placeholder="Ej.: Se llamó al interesado, queda para el sábado 15 hs."
                />
                <button class="btn btn--ghost btn--sm" type="submit" :disabled="noteSaving">
                  {{ noteSaving ? "Guardando…" : "Agregar nota" }}
                </button>
              </form>
            </div>
          </div>
        </li>
      </ul>

      <nav class="pagination" aria-label="Paginación">
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

.inbox-filters {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.inbox-filters__grid {
  display: grid;
  gap: var(--space-4);
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr));
}

.inbox {
  display: grid;
  gap: var(--space-3);
  padding: 0;
  margin: 0;
  list-style: none;
}

.inbox__item {
  overflow: hidden;
}

.inbox__summary {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  width: 100%;
  padding: var(--space-4);
  text-align: left;
}

.inbox__summary:hover {
  background: #faf8f4;
}

.inbox__who {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.inbox__date {
  white-space: nowrap;
}

.inbox__chevron {
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border: 1px solid var(--color-line-strong);
  border-radius: 50%;
  font-size: var(--text-md);
  color: var(--color-stone-dark);
}

.inbox__detail {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-4);
  border-top: 1px solid var(--color-line);
  background: #fbfaf7;
}

.inbox__fields {
  display: grid;
  gap: var(--space-3);
  margin: 0;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr));
}

.inbox__fields > div {
  display: flex;
  flex-direction: column;
}

.inbox__fields dt {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-stone-dark);
}

.inbox__fields dd {
  margin: 0;
  font-size: var(--text-sm);
  white-space: pre-wrap;
}

.inbox__status-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
}

.select--inline {
  width: auto;
  min-width: 190px;
}

.inbox__notes-title {
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 600;
}

.inbox__notes-warning {
  margin-bottom: var(--space-2);
}

.inbox__notes-list {
  display: grid;
  gap: var(--space-2);
  padding: 0;
  margin: 0 0 var(--space-3);
  list-style: none;
}

.inbox__notes-list li {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: var(--space-3);
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-left: 3px solid var(--color-bronze);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
}

.inbox__note-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  align-items: flex-start;
}

.textarea--sm {
  min-height: 70px;
}
</style>
