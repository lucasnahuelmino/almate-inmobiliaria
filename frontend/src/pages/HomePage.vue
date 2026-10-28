<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ApiError, api, toQuery } from "../api/client";
import type { PropertySummary } from "../api/types";
import { useSettingsStore } from "../stores/settings";
import PropertyCard from "../components/PropertyCard.vue";
import ContactForm from "../components/ContactForm.vue";
import LoadingBlock from "../components/LoadingBlock.vue";
import ErrorState from "../components/ErrorState.vue";
import EmptyState from "../components/EmptyState.vue";

const router = useRouter();
const settingsStore = useSettingsStore();

const featured = ref<PropertySummary[]>([]);
const recent = ref<PropertySummary[]>([]);
const total = ref<number | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

const search = ref({ operation: "", type: "", locality: "", maxPrice: "" });

const heroStyle = computed(() => {
  const image = featured.value[0]?.image?.url;
  return image ? { backgroundImage: `linear-gradient(90deg, rgba(24,25,24,.88), rgba(24,25,24,.55)), url("${image}")` } : {};
});

const services = [
  {
    title: "Compra",
    text: "Te acompañamos en la búsqueda, la visita y el cierre de la operación con documentación en orden.",
    to: "/comprar",
    cta: "Ver propiedades en venta",
    icon: "home",
  },
  {
    title: "Alquiler",
    text: "Opciones residenciales con expensas, requisitos y contratos claros desde el primer contacto.",
    to: "/alquilar",
    cta: "Ver opciones en alquiler",
    icon: "key",
  },
  {
    title: "Alquiler temporal",
    text: "Estadías cortas y workation: propiedades amobladas con precios por noche.",
    to: "/alquiler-temporal",
    cta: "Ver alquiler temporal",
    icon: "calendar",
  },
  {
    title: "Tasación",
    text: "Conocé el valor real de tu propiedad con un informe comparativo del mercado zonal.",
    to: "/tasacion",
    cta: "Solicitar tasación",
    icon: "chart",
  },
];

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const [featuredData, recentData, listing] = await Promise.all([
      api.get<PropertySummary[]>("/properties/featured?limit=6"),
      api.get<{ items: PropertySummary[] }>("/properties" + toQuery({ sort: "recent", page_size: 6 })),
      api.get<{ total: number }>("/properties" + toQuery({ page_size: 1 })),
    ]);
    featured.value = featuredData;
    recent.value = recentData.items;
    total.value = listing.total;
  } catch (caught) {
    error.value =
      caught instanceof ApiError ? caught.message : "No pudimos cargar las propiedades.";
  } finally {
    loading.value = false;
  }
}

function runSearch() {
  const query: Record<string, string> = {};
  if (search.value.type) query.tipo = search.value.type;
  if (search.value.locality) query.localidad = search.value.locality;
  if (search.value.maxPrice) query.precio_max = search.value.maxPrice;

  const target =
    search.value.operation === "rent"
      ? "/alquilar"
      : search.value.operation === "temporary_rent"
        ? "/alquiler-temporal"
        : "/comprar";
  void router.push({ path: target, query });
}

onMounted(() => {
  void load();
  void settingsStore.loadMeta();
});
</script>

<template>
  <div>
    <!-- Hero -->
    <section class="hero" :class="{ 'hero--image': featured.length }" :style="heroStyle">
      <div class="container hero__inner">
        <div class="hero__content">
          <span class="eyebrow">Sur del Gran Buenos Aires</span>
          <h1>Encontrá tu próximo lugar</h1>
          <p class="hero__lede">
            Propiedades seleccionadas para comprar, alquilar y habitar mejor. Fichas claras,
            datos verificados y un equipo que acompaña cada paso de la operación.
          </p>

          <form class="hero__search" aria-label="Búsqueda rápida" @submit.prevent="runSearch">
            <div class="field">
              <label for="hero-operacion">Operación</label>
              <select id="hero-operacion" v-model="search.operation" class="select">
                <option value="buy">Comprar</option>
                <option value="rent">Alquilar</option>
                <option value="temporary_rent">Alquiler temporal</option>
              </select>
            </div>
            <div class="field">
              <label for="hero-tipo">Tipo</label>
              <select id="hero-tipo" v-model="search.type" class="select">
                <option value="">Todos</option>
                <option
                  v-for="option in settingsStore.meta?.property_types ?? []"
                  :key="option.value"
                  :value="option.value"
                >
                  {{ option.label }}
                </option>
              </select>
            </div>
            <div class="field">
              <label for="hero-localidad">Localidad</label>
              <select id="hero-localidad" v-model="search.locality" class="select">
                <option value="">Todas</option>
                <option
                  v-for="locality in settingsStore.meta?.localities ?? []"
                  :key="locality"
                  :value="locality"
                >
                  {{ locality }}
                </option>
              </select>
            </div>
            <div class="field">
              <label for="hero-precio">Precio máximo</label>
              <input
                id="hero-precio"
                v-model="search.maxPrice"
                class="input numeric"
                type="number"
                min="0"
                inputmode="numeric"
                placeholder="Sin máximo"
              />
            </div>
            <button class="btn btn--bronze hero__submit" type="submit">Buscar propiedades</button>
          </form>

          <p class="hero__meta">
            <template v-if="total !== null">
              <strong class="numeric">{{ total }}</strong> propiedades publicadas hoy
            </template>
            <template v-else>Cargando el catálogo…</template>
          </p>
        </div>
      </div>
    </section>

    <!-- Destacadas -->
    <section class="section" aria-labelledby="destacadas-titulo">
      <div class="container">
        <div class="section-head">
          <div>
            <span class="eyebrow">Selección del estudio</span>
            <h2 id="destacadas-titulo" class="section-title">Propiedades destacadas</h2>
          </div>
          <RouterLink class="btn btn--ghost btn--sm" to="/comprar">
            Ver el catálogo completo
          </RouterLink>
        </div>

        <LoadingBlock v-if="loading" label="Cargando destacadas…" />
        <ErrorState
          v-else-if="error"
          :message="error"
          @retry="load"
        />
        <EmptyState
          v-else-if="!featured.length"
          title="Todavía no hay destacadas"
          description="Estamos preparando la selección de la semana. Mientras tanto, explorá todo el catálogo."
          action-label="Ir al catálogo"
          @action="router.push('/comprar')"
        />
        <div v-else class="grid grid--cards">
          <PropertyCard
            v-for="property in featured"
            :key="property.code"
            :property="property"
          />
        </div>
      </div>
    </section>

    <!-- Recientes -->
    <section class="section section--alt" aria-labelledby="recientes-titulo">
      <div class="container">
        <div class="section-head">
          <div>
            <span class="eyebrow">Alta en el catálogo</span>
            <h2 id="recientes-titulo" class="section-title">Recién publicadas</h2>
          </div>
          <RouterLink class="link-btn" to="/comprar?orden=recent">Ver todas las recientes</RouterLink>
        </div>

        <div v-if="loading" class="grid grid--cards">
          <div v-for="index in 3" :key="index" class="skeleton" style="height: 340px" />
        </div>
        <div v-else class="grid grid--cards">
          <PropertyCard v-for="property in recent" :key="property.code" :property="property" />
        </div>
      </div>
    </section>

    <!-- Servicios -->
    <section class="section" aria-labelledby="servicios-titulo">
      <div class="container">
        <div class="section-head">
          <div>
            <span class="eyebrow">Qué hacemos</span>
            <h2 id="servicios-titulo" class="section-title">Servicios</h2>
          </div>
        </div>

        <div class="services">
          <article v-for="service in services" :key="service.title" class="service card">
            <span class="service__icon" aria-hidden="true">
              <svg v-if="service.icon === 'home'" width="22" height="22" viewBox="0 0 24 24">
                <path d="M4 20V9.5L12 4l8 5.5V20M9 20v-6h6v6" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" />
              </svg>
              <svg v-else-if="service.icon === 'key'" width="22" height="22" viewBox="0 0 24 24">
                <circle cx="8" cy="8" r="4" fill="none" stroke="currentColor" stroke-width="1.5" />
                <path d="M11 11l9 9M16 16l2-2M19 19l2-2" fill="none" stroke="currentColor" stroke-width="1.5" />
              </svg>
              <svg v-else-if="service.icon === 'calendar'" width="22" height="22" viewBox="0 0 24 24">
                <rect x="3.5" y="5.5" width="17" height="15" rx="2" fill="none" stroke="currentColor" stroke-width="1.5" />
                <path d="M3.5 10h17M8 3.5v4M16 3.5v4" fill="none" stroke="currentColor" stroke-width="1.5" />
              </svg>
              <svg v-else width="22" height="22" viewBox="0 0 24 24">
                <path d="M4 19h16M7 16V9M12 16V5M17 16v-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
              </svg>
            </span>
            <h3>{{ service.title }}</h3>
            <p class="muted">{{ service.text }}</p>
            <RouterLink class="link-btn" :to="service.to">{{ service.cta }}</RouterLink>
          </article>
        </div>
      </div>
    </section>

    <!-- Llamada a la acción -->
    <section class="cta">
      <div class="container cta__inner">
        <div>
          <span class="eyebrow eyebrow--light">Dueños de propiedades</span>
          <h2>¿Querés vender o alquilar tu propiedad?</h2>
          <p>
            Tasamos, preparamos la ficha, producimos las fotografías y publicamos en los
            canales del estudio. También recibimos propiedades de otros dueños.
          </p>
        </div>
        <div class="cta__actions">
          <RouterLink class="btn btn--bronze" to="/publicar-propiedad">
            Publicar mi propiedad
          </RouterLink>
          <RouterLink class="btn btn--ghost btn--on-dark" to="/tasacion">
            Pedir una tasación
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- Contacto -->
    <section class="section section--alt" aria-labelledby="contacto-titulo">
      <div class="container contact">
        <div class="contact__info">
          <span class="eyebrow">Hablemos</span>
          <h2 id="contacto-titulo" class="section-title">Contacto</h2>
          <p class="lede">
            Escribinos y te respondemos con opciones concretas según lo que estés buscando.
          </p>

          <ul class="contact__list">
            <li>
              <span class="strong">Teléfono</span>
              <a :href="`tel:${settingsStore.settings?.phone?.replace(/\s/g, '') ?? ''}`">
                {{ settingsStore.settings?.phone ?? "—" }}
              </a>
            </li>
            <li>
              <span class="strong">Correo</span>
              <a :href="`mailto:${settingsStore.settings?.email ?? ''}`">
                {{ settingsStore.settings?.email ?? "—" }}
              </a>
            </li>
            <li>
              <span class="strong">Estudio</span>
              <span>
                {{ settingsStore.settings?.address_line ?? "—" }},
                {{ settingsStore.settings?.city ?? "" }}
              </span>
            </li>
            <li>
              <span class="strong">Horarios</span>
              <span>{{ settingsStore.settings?.office_hours ?? "—" }}</span>
            </li>
          </ul>

          <p v-if="settingsStore.settings?.whatsapp_is_demo" class="alert alert--warning">
            El número de WhatsApp de esta demo es ficticio: no envía mensajes reales.
          </p>
        </div>

        <div class="contact__form panel">
          <ContactForm submit-label="Enviar consulta" />
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.hero {
  position: relative;
  background:
    radial-gradient(1200px 400px at 15% -10%, rgba(165, 139, 103, 0.22), transparent 60%),
    linear-gradient(180deg, #23241f 0%, #1b1c19 100%);
  color: #f3f1ea;
  background-size: cover;
  background-position: center;
}

.hero--image {
  background-size: cover;
  background-position: center;
}

.hero__inner {
  padding-block: clamp(3rem, 2rem + 6vw, 6rem);
}

.hero__content {
  max-width: 760px;
}

.hero .eyebrow {
  color: var(--color-bronze);
}

.hero h1 {
  margin-top: var(--space-3);
  color: #fff;
}

.hero__lede {
  margin-top: var(--space-4);
  max-width: 56ch;
  color: #cfccc4;
  font-size: var(--text-md);
}

.hero__search {
  display: grid;
  gap: var(--space-3);
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 180px), 1fr));
  align-items: end;
  margin-top: var(--space-6);
  padding: var(--space-4);
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: var(--radius-md);
  backdrop-filter: blur(6px);
}

.hero__search label {
  color: #e6e3db;
}

.hero__submit {
  min-height: 44px;
}

.hero__meta {
  margin-top: var(--space-4);
  font-size: var(--text-sm);
  color: #b6b3ab;
}

.services {
  display: grid;
  gap: var(--space-5);
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 260px), 1fr));
}

.service {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-5);
}

.service__icon {
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  border-radius: 50%;
  background: var(--color-sage-light);
  color: var(--color-sage-dark);
}

.service .link-btn {
  margin-top: auto;
}

.cta {
  background: var(--color-sage);
  color: #f4f6f2;
}

.cta__inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-5);
  padding-block: var(--section-y);
}

.cta h2 {
  margin-top: var(--space-2);
  max-width: 18ch;
}

.cta p {
  margin-top: var(--space-3);
  max-width: 58ch;
  color: #dfe4db;
}

.eyebrow--light {
  color: #e7dcc9;
}

.cta__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.btn--on-dark {
  border-color: rgba(255, 255, 255, 0.5);
  color: #fff;
}

.btn--on-dark:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
}

.contact {
  display: grid;
  gap: var(--space-6);
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 320px), 1fr));
  align-items: start;
}

.contact__list {
  list-style: none;
  padding: 0;
  margin: var(--space-5) 0;
  display: grid;
  gap: var(--space-3);
}

.contact__list li {
  display: grid;
  grid-template-columns: 110px 1fr;
  gap: var(--space-3);
  font-size: var(--text-sm);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-line);
}

.contact__form {
  padding: var(--space-5);
}
</style>
