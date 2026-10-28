<script setup lang="ts">
/** Resumen del panel: métricas reales calculadas por el backend. */
import { onMounted, ref } from "vue";
import { ApiError, api } from "../../api/client";
import type { Dashboard } from "../../api/types";
import LoadingBlock from "../../components/LoadingBlock.vue";
import ErrorState from "../../components/ErrorState.vue";
import StatusBadge from "../../components/StatusBadge.vue";
import { formatDate, formatPrice } from "../../utils/format";

const data = ref<Dashboard | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

const LEAD_STATUS_LABELS: Record<string, string> = {
  new: "Nuevas",
  following: "En seguimiento",
  answered: "Respondidas",
  archived: "Archivadas",
};

async function load() {
  loading.value = true;
  error.value = null;
  try {
    data.value = await api.get<Dashboard>("/admin/dashboard", { auth: true });
  } catch (caught) {
    error.value =
      caught instanceof ApiError ? caught.message : "No pudimos cargar el resumen.";
  } finally {
    loading.value = false;
  }
}

onMounted(() => void load());
</script>

<template>
  <div>
    <div class="admin-head">
      <div>
        <h1>Resumen</h1>
        <p class="muted small">Métricas calculadas sobre la base de datos del panel.</p>
      </div>
      <div class="row">
        <RouterLink class="btn btn--ghost btn--sm" to="/admin/propiedades/nueva">
          + Nueva propiedad
        </RouterLink>
        <button class="btn btn--ghost btn--sm" type="button" @click="load">Actualizar</button>
      </div>
    </div>

    <LoadingBlock v-if="loading" label="Cargando métricas…" />
    <ErrorState v-else-if="error" :message="error" @retry="load" />

    <template v-else-if="data">
      <section aria-labelledby="metricas-titulo">
        <h2 id="metricas-titulo" class="sr-only">Métricas del catálogo</h2>
        <div class="grid grid--stats stats">
          <article class="stat card">
            <span class="stat__label">Propiedades totales</span>
            <strong class="stat__value numeric">{{ data.counts.properties_total }}</strong>
          </article>
          <article class="stat card">
            <span class="stat__label">Publicadas</span>
            <strong class="stat__value numeric">{{ data.counts.published }}</strong>
            <span class="stat__hint">visibles en el sitio</span>
          </article>
          <article class="stat card">
            <span class="stat__label">Borradores</span>
            <strong class="stat__value numeric">{{ data.counts.draft }}</strong>
            <span class="stat__hint">esperando publicación</span>
          </article>
          <article class="stat card">
            <span class="stat__label">Archivadas</span>
            <strong class="stat__value numeric">{{ data.counts.archived }}</strong>
          </article>
          <article class="stat card">
            <span class="stat__label">Destacadas</span>
            <strong class="stat__value numeric">{{ data.counts.featured }}</strong>
          </article>
        </div>
      </section>

      <section aria-labelledby="comercial-titulo" class="admin-block">
        <h2 id="comercial-titulo" class="admin-block__title">Estado comercial</h2>
        <div class="grid grid--stats stats">
          <article class="stat card">
            <span class="stat__label">Disponibles</span>
            <strong class="stat__value numeric stat__value--ok">{{ data.counts.available }}</strong>
          </article>
          <article class="stat card">
            <span class="stat__label">Reservadas</span>
            <strong class="stat__value numeric stat__value--warn">{{ data.counts.reserved }}</strong>
          </article>
          <article class="stat card">
            <span class="stat__label">Vendidas</span>
            <strong class="stat__value numeric">{{ data.counts.sold }}</strong>
          </article>
          <article class="stat card">
            <span class="stat__label">Alquiladas</span>
            <strong class="stat__value numeric">{{ data.counts.rented }}</strong>
          </article>
        </div>
      </section>

      <section aria-labelledby="bandeja-titulo" class="admin-block">
        <h2 id="bandeja-titulo" class="admin-block__title">Bandeja de entrada</h2>
        <div class="grid grid--stats stats">
          <article class="stat card">
            <span class="stat__label">Consultas nuevas</span>
            <strong class="stat__value numeric">{{ data.counts.inquiries_new }}</strong>
            <span class="stat__hint">de {{ data.counts.inquiries_total }} en total</span>
          </article>
          <article class="stat card">
            <span class="stat__label">Tasaciones pendientes</span>
            <strong class="stat__value numeric">{{ data.counts.valuations_pending }}</strong>
          </article>
          <article class="stat card">
            <span class="stat__label">Publicaciones pendientes</span>
            <strong class="stat__value numeric">{{ data.counts.listings_pending }}</strong>
          </article>
        </div>

        <div class="panel status-breakdown">
          <h3 class="status-breakdown__title">Consultas por estado</h3>
          <ul class="status-breakdown__list">
            <li v-for="(count, key) in data.inquiries_by_status" :key="key">
              <span>{{ LEAD_STATUS_LABELS[key] ?? key }}</span>
              <strong class="numeric">{{ count }}</strong>
            </li>
          </ul>
        </div>
      </section>

      <div class="admin-columns">
        <section class="panel" aria-labelledby="ultimas-consultas-titulo">
          <div class="panel__head">
            <h2 id="ultimas-consultas-titulo" class="panel__title">Últimas consultas</h2>
            <RouterLink class="link-btn" to="/admin/consultas">Ver todas</RouterLink>
          </div>

          <p v-if="!data.last_inquiries.length" class="muted small">
            Todavía no hay consultas registradas.
          </p>
          <ul v-else class="mini-list">
            <li v-for="inquiry in data.last_inquiries" :key="inquiry.id">
              <div>
                <strong>{{ inquiry.name }}</strong>
                <span class="muted small">
                  {{ inquiry.property_code ? `Por ${inquiry.property_code}` : "Consulta general" }}
                  · {{ formatDate(inquiry.created_at) }}
                </span>
              </div>
              <span class="badge" :class="`badge--${inquiry.status}`">
                {{ LEAD_STATUS_LABELS[inquiry.status] ?? inquiry.status }}
              </span>
            </li>
          </ul>
        </section>

        <section class="panel" aria-labelledby="ultimas-propiedades-titulo">
          <div class="panel__head">
            <h2 id="ultimas-propiedades-titulo" class="panel__title">Propiedades actualizadas</h2>
            <RouterLink class="link-btn" to="/admin/propiedades">Ver todas</RouterLink>
          </div>

          <p v-if="!data.last_properties.length" class="muted small">
            Todavía no hay propiedades cargadas.
          </p>
          <ul v-else class="mini-list">
            <li v-for="property in data.last_properties" :key="property.code">
              <div>
                <strong>{{ property.title }}</strong>
                <span class="muted small">
                  {{ property.code }} · {{ formatPrice(property.price, property.currency, property.price_unit) }}
                </span>
              </div>
              <StatusBadge
                :commercial="property.commercial_status"
                :publication="property.publication_status"
              />
            </li>
          </ul>
        </section>
      </div>
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
  margin-bottom: var(--space-5);
}

.admin-head h1 {
  font-size: var(--text-xl);
}

.stats {
  gap: var(--space-4);
}

.stat {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-4);
}

.stat__label {
  font-size: var(--text-xs);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-stone-dark);
}

.stat__value {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  font-weight: 500;
  line-height: 1.1;
}

.stat__value--ok {
  color: var(--color-sage-dark);
}

.stat__value--warn {
  color: var(--color-warning);
}

.stat__hint {
  font-size: var(--text-xs);
  color: var(--color-stone-dark);
}

.admin-block {
  margin-top: var(--space-6);
}

.admin-block__title,
.panel__title,
.status-breakdown__title {
  font-family: var(--font-ui);
  font-size: var(--text-sm);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-stone-dark);
  margin-bottom: var(--space-3);
}

.status-breakdown {
  margin-top: var(--space-4);
}

.status-breakdown__list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
  padding: 0;
  margin: 0;
  list-style: none;
  font-size: var(--text-sm);
}

.status-breakdown__list li {
  display: flex;
  gap: var(--space-2);
  padding: 0.35rem 0.8rem;
  background: var(--color-bg-alt);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-pill);
}

.admin-columns {
  display: grid;
  gap: var(--space-5);
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 340px), 1fr));
  margin-top: var(--space-6);
}

.panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.mini-list {
  display: grid;
  gap: var(--space-3);
  padding: 0;
  margin: 0;
  list-style: none;
}

.mini-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-line);
  font-size: var(--text-sm);
}

.mini-list li:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.mini-list li > div {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
</style>
