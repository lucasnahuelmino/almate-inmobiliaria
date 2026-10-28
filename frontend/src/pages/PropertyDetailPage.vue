<script setup lang="ts">
/**
 * Ficha pública de la propiedad: galería, datos, contacto directo (WhatsApp),
 * formulario de consulta y propiedades similares.
 */
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { ApiError, api, toQuery } from "../api/client";
import type { PropertyDetail, PropertySummary } from "../api/types";
import { useSettingsStore } from "../stores/settings";
import { usePageMeta } from "../composables/usePageMeta";
import {
  COMMERCIAL_LABELS,
  formatDate,
  formatPrice,
  formatSurface,
  locationLabel,
  operationLabel,
  typeLabel,
} from "../utils/format";
import { whatsappLink } from "../utils/whatsapp";
import PropertyGallery from "../components/PropertyGallery.vue";
import PropertyCard from "../components/PropertyCard.vue";
import StatusBadge from "../components/StatusBadge.vue";
import FavoriteButton from "../components/FavoriteButton.vue";
import ContactForm from "../components/ContactForm.vue";
import LoadingBlock from "../components/LoadingBlock.vue";
import ErrorState from "../components/ErrorState.vue";

const route = useRoute();
const settingsStore = useSettingsStore();
const { apply: applyMeta } = usePageMeta();

const property = ref<PropertyDetail | null>(null);
const similar = ref<PropertySummary[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

const code = computed(() => String(route.params.codigo ?? ""));

const location = computed(() => (property.value ? locationLabel(property.value) : ""));

const notAvailable = computed(
  () =>
    property.value &&
    (property.value.commercial_status !== "available" ||
      property.value.publication_status !== "published"),
);

const characteristics = computed(() => {
  const item = property.value;
  if (!item) return [] as { label: string; value: string }[];

  const rows: { label: string; value: string }[] = [
    { label: "Operación", value: operationLabel(item.operation) },
    { label: "Tipo", value: typeLabel(item.property_type) },
    { label: "Estado", value: COMMERCIAL_LABELS[item.commercial_status] ?? item.commercial_status },
  ];
  if (item.is_development) rows.push({ label: "Categoría", value: "Emprendimiento" });
  if (item.rooms) rows.push({ label: "Ambientes", value: String(item.rooms) });
  if (item.bedrooms) rows.push({ label: "Dormitorios", value: String(item.bedrooms) });
  if (item.bedrooms === 0) rows.push({ label: "Dormitorios", value: "Sin dormitorios" });
  if (item.toilets !== null) rows.push({ label: "Toilettes", value: String(item.toilets) });
  if (item.bathrooms) rows.push({ label: "Baños", value: String(item.bathrooms) });
  if (item.garages) rows.push({ label: "Cocheras", value: String(item.garages) });
  if (item.surface_covered) rows.push({ label: "Superficie cubierta", value: formatSurface(item.surface_covered) });
  if (item.surface_semicovered) rows.push({ label: "Superficie semicubierta", value: formatSurface(item.surface_semicovered) });
  if (item.surface_total) rows.push({ label: "Superficie total", value: formatSurface(item.surface_total) });
  if (item.antiquity_years !== null) rows.push({ label: "Antigüedad", value: `${item.antiquity_years} años` });
  rows.push({ label: "Apto profesional", value: item.apto_professional ? "Sí" : "No" });
  rows.push({ label: "Código", value: item.code });
  if (item.published_at) rows.push({ label: "Publicada", value: formatDate(item.published_at) });
  return rows;
});

const waLink = computed(() => {
  const item = property.value;
  const settings = settingsStore.settings;
  if (!item || !settings) return "";
  return whatsappLink(settings, {
    code: item.code,
    title: item.title,
    operation: item.operation,
    location: location.value,
    url: window.location.href,
    intent: `consultar por ${item.title}`,
  });
});

const waReady = computed(() => Boolean(waLink.value));

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const detail = await api.get<PropertyDetail>(`/properties/${code.value}`);
    property.value = detail;

    applyMeta({
      title: `${detail.title} | ${typeLabel(detail.property_type)} en ${location.value}`,
      description:
        detail.description.slice(0, 155) ||
        `${operationLabel(detail.operation)} de ${typeLabel(detail.property_type).toLowerCase()} en ${location.value}. Código ${detail.code}.`,
      image: detail.image?.url,
    });

    const similarResponse = await api.get<PropertySummary[]>(
      `/properties/${code.value}/similar${toQuery({ limit: 3 })}`,
    );
    similar.value = similarResponse;
  } catch (caught) {
    if (caught instanceof ApiError && caught.status === 404) {
      error.value = "No encontramos esta propiedad. Puede que se haya dado de baja.";
    } else {
      error.value = caught instanceof Error ? caught.message : "No pudimos cargar la ficha.";
    }
  } finally {
    loading.value = false;
  }
}

watch(code, () => void load());

onMounted(() => {
  void load();
  void settingsStore.loadSettings();
});
</script>

<template>
  <div class="detail">
    <LoadingBlock v-if="loading" label="Cargando la ficha…" />

    <section v-else-if="error" class="section">
      <div class="container">
        <ErrorState :message="error" @retry="load">
          <RouterLink class="btn btn--ghost" to="/comprar">Volver al catálogo</RouterLink>
        </ErrorState>
      </div>
    </section>

    <template v-else-if="property">
      <div class="detail__top">
        <div class="container">
          <nav class="breadcrumbs" aria-label="Migas de pan">
            <RouterLink to="/">Inicio</RouterLink>
            <span aria-hidden="true">/</span>
            <RouterLink
              :to="
                property.operation === 'rent'
                  ? '/alquilar'
                  : property.operation === 'temporary_rent'
                    ? '/alquiler-temporal'
                    : '/comprar'
              "
            >
              {{ operationLabel(property.operation) }}
            </RouterLink>
            <span aria-hidden="true">/</span>
            <span aria-current="page">{{ property.title }}</span>
          </nav>
        </div>
      </div>

      <section class="section detail__main">
        <div class="container detail__grid">
          <div class="detail__gallery">
            <PropertyGallery :images="property.images" :title="property.title" />
          </div>

          <aside class="detail__side">
            <div class="detail__head">
              <StatusBadge
                :commercial="property.commercial_status"
                :development="property.is_development"
                :featured="property.is_featured"
              />
              <span class="detail__code">Cód. {{ property.code }}</span>
            </div>

            <h1 class="detail__title">{{ property.title }}</h1>
            <p class="detail__location">
              <svg width="15" height="15" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 21s7-5.6 7-11a7 7 0 1 0-14 0c0 5.4 7 11 7 11Z" fill="none" stroke="currentColor" stroke-width="1.6" />
                <circle cx="12" cy="10" r="2.4" fill="none" stroke="currentColor" stroke-width="1.6" />
              </svg>
              {{ location }}
            </p>

            <p class="detail__price numeric">
              {{ formatPrice(property.price, property.currency, property.price_unit) }}
            </p>
            <p v-if="property.expenses" class="detail__expenses">
              Expensas: {{ formatPrice(property.expenses, property.currency, "monthly") }}
            </p>

            <div v-if="notAvailable" class="alert alert--warning">
              Esta propiedad está marcada como
              <strong>{{ COMMERCIAL_LABELS[property.commercial_status] }}</strong>. Contactanos
              para conocer opciones similares disponibles.
            </div>

            <div class="detail__quick">
              <span v-if="property.bedrooms">
                <strong class="numeric">{{ property.bedrooms }}</strong> dorm.
              </span>
              <span v-if="property.bathrooms">
                <strong class="numeric">{{ property.bathrooms }}</strong> baños
              </span>
              <span v-if="property.garages">
                <strong class="numeric">{{ property.garages }}</strong> cochera{{ property.garages > 1 ? "s" : "" }}
              </span>
              <span v-if="property.surface_total">
                <strong class="numeric">{{ formatSurface(property.surface_total) }}</strong>
              </span>
            </div>

            <div class="detail__actions">
              <a
                v-if="waReady"
                class="btn btn--sage btn--block"
                :href="waLink"
                target="_blank"
                rel="noopener noreferrer"
              >
                <svg width="17" height="17" viewBox="0 0 24 24" aria-hidden="true">
                  <path
                    d="M12 3a9 9 0 0 0-7.8 13.5L3 21l4.7-1.2A9 9 0 1 0 12 3Z"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.6"
                  />
                </svg>
                Escribir por WhatsApp
              </a>
              <div class="detail__fav">
                <FavoriteButton :code="property.code" />
                <span class="small muted">Guardar</span>
              </div>
            </div>

            <p v-if="settingsStore.settings?.whatsapp_is_demo" class="small muted">
              Número de demostración: el botón abre WhatsApp con el mensaje precargado, pero no
              envía nada automáticamente.
            </p>

            <div class="panel detail__form">
              <h2 class="detail__form-title">Solicitar información</h2>
              <ContactForm
                :property-code="property.code"
                :property-title="property.title"
                :operation="property.operation"
                :location="location"
                submit-label="Enviar consulta"
              />
            </div>
          </aside>
        </div>
      </section>

      <section class="section section--alt">
        <div class="container detail__grid detail__grid--lower">
          <div>
            <span class="eyebrow">La propiedad</span>
            <h2 class="section-title">Descripción</h2>
            <div class="detail__description">
              <p v-for="(paragraph, index) in property.description.split(/\n+/)" :key="index">
                {{ paragraph }}
              </p>
            </div>

            <template v-if="property.services.length">
              <h3 class="detail__subtitle">Servicios</h3>
              <ul class="detail__services">
                <li v-for="service in property.services" :key="service">{{ service }}</li>
              </ul>
            </template>
          </div>

          <div>
            <span class="eyebrow">Ficha técnica</span>
            <h2 class="section-title">Características</h2>
            <dl class="detail__specs">
              <div v-for="row in characteristics" :key="row.label" class="detail__spec">
                <dt>{{ row.label }}</dt>
                <dd class="numeric">{{ row.value }}</dd>
              </div>
            </dl>
          </div>
        </div>
      </section>

      <section v-if="similar.length" class="section">
        <div class="container">
          <div class="section-head">
            <div>
              <span class="eyebrow">Seguí mirando</span>
              <h2 class="section-title">Propiedades similares</h2>
            </div>
            <RouterLink class="link-btn" to="/comprar">Ver todo el catálogo</RouterLink>
          </div>
          <div class="grid grid--cards">
            <PropertyCard v-for="item in similar" :key="item.code" :property="item" />
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.detail__top {
  padding-top: var(--space-5);
}

.breadcrumbs {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-stone-dark);
}

.breadcrumbs a {
  text-decoration: none;
}

.breadcrumbs a:hover {
  color: var(--color-bronze-dark);
}

.detail__main {
  padding-top: var(--space-5);
}

.detail__grid {
  display: grid;
  gap: var(--space-6);
  grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr);
  align-items: start;
}

.detail__side {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.detail__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.detail__code {
  font-size: var(--text-xs);
  letter-spacing: 0.08em;
  color: var(--color-stone-dark);
}

.detail__title {
  font-size: var(--text-2xl);
}

.detail__location {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-stone-dark);
  font-size: var(--text-sm);
}

.detail__price {
  font-family: var(--font-display);
  font-size: var(--text-2xl);
  color: var(--color-ink);
}

.detail__expenses {
  font-size: var(--text-sm);
  color: var(--color-stone-dark);
}

.detail__quick {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  font-size: var(--text-sm);
}

.detail__quick span {
  padding: 0.3rem 0.7rem;
  background: var(--color-bg-alt);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-pill);
}

.detail__actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-top: var(--space-2);
}

.detail__fav {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.detail__form {
  margin-top: var(--space-3);
}

.detail__form-title {
  font-size: var(--text-lg);
  margin-bottom: var(--space-4);
}

.detail__grid--lower {
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr);
}

.detail__description {
  display: grid;
  gap: var(--space-4);
  margin-top: var(--space-4);
  color: var(--color-ink-soft);
  line-height: 1.75;
}

.detail__subtitle {
  margin-top: var(--space-6);
  font-size: var(--text-lg);
}

.detail__services {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  padding: 0;
  margin: var(--space-3) 0 0;
  list-style: none;
}

.detail__services li {
  padding: 0.3rem 0.8rem;
  background: var(--color-sage-light);
  color: var(--color-sage-dark);
  border-radius: var(--radius-pill);
  font-size: var(--text-sm);
}

.detail__specs {
  margin: var(--space-4) 0 0;
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.detail__spec {
  display: flex;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-line);
  font-size: var(--text-sm);
}

.detail__spec:last-child {
  border-bottom: none;
}

.detail__spec dt {
  color: var(--color-stone-dark);
}

.detail__spec dd {
  margin: 0;
  font-weight: 600;
  text-align: right;
}

@media (max-width: 980px) {
  .detail__grid,
  .detail__grid--lower {
    grid-template-columns: 1fr;
  }
}
</style>
