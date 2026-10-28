<script setup lang="ts">
/** Página institucional: quiénes somos, cómo trabajamos y servicios. */
import { computed, onMounted } from "vue";
import { useSettingsStore } from "../stores/settings";

const settingsStore = useSettingsStore();
const settings = computed(() => settingsStore.settings);

const values = [
  {
    title: "Datos verificados",
    text: "Cada ficha se arma con medidas, gastos y documentación revisada antes de publicarse.",
    icon: "check",
  },
  {
    title: "Trato directo",
    text: "Un asesor acompaña la operación de principio a fin, sin intermediarios ni demoras.",
    icon: "chat",
  },
  {
    title: "Transparencia",
    text: "Precios, expensas y honorarios a la vista: sin sorpresas en el cierre.",
    icon: "eye",
  },
];

const process = [
  {
    step: "01",
    title: "Escuchamos",
    text: "Entendemos qué necesitás: presupuesto, zona, plazos y prioridades.",
  },
  {
    step: "02",
    title: "Seleccionamos",
    text: "Filtramos el catálogo y coordinamos visitas sólo a las propiedades que cumplen.",
  },
  {
    step: "03",
    title: "Acompañamos",
    text: "Revisamos documentación, tasación y contrato hasta la firma.",
  },
];

onMounted(() => {
  void settingsStore.loadSettings();
});
</script>

<template>
  <div>
    <header class="page-head">
      <div class="container container--narrow">
        <span class="eyebrow">Nosotros</span>
        <h1>Un estudio inmobiliario con mirada editorial</h1>
        <p class="lede">
          {{ settings?.tagline ?? "Propiedades seleccionadas en el sur del Gran Buenos Aires" }}.
        </p>
      </div>
    </header>

    <section class="section">
      <div class="container container--narrow prose">
        <p>
          {{ settings?.institutional_text ??
            "ALMATE Propiedades nació como estudio de comercialización de propiedades en el sur del Gran Buenos Aires. Trabajamos con catálogo propio, fichas cuidadas y una atención que prioriza la claridad por sobre la urgencia." }}
        </p>
        <p>
          Compramos, alquilamos y publicamos en modalidad temporal: cada operación tiene su
          propio proceso, sus tiempos y su documentación. Nuestro equipo se encarga de que
          ese recorrido sea previsible para todas las partes.
        </p>
      </div>
    </section>

    <section class="section section--alt">
      <div class="container">
        <div class="section-head">
          <div>
            <span class="eyebrow">Cómo trabajamos</span>
            <h2 class="section-title">Tres pasos, un solo interlocutor</h2>
          </div>
        </div>
        <div class="grid grid--two process">
          <article v-for="item in process" :key="item.step" class="process__item">
            <span class="process__step numeric">{{ item.step }}</span>
            <div>
              <h3>{{ item.title }}</h3>
              <p class="muted">{{ item.text }}</p>
            </div>
          </article>
        </div>
      </div>
    </section>

    <section class="section">
      <div class="container">
        <div class="section-head">
          <div>
            <span class="eyebrow">Principios</span>
            <h2 class="section-title">Lo que no negociamos</h2>
          </div>
        </div>
        <div class="grid grid--two values">
          <article v-for="value in values" :key="value.title" class="value card">
            <span class="value__icon" aria-hidden="true">
              <svg v-if="value.icon === 'check'" width="20" height="20" viewBox="0 0 24 24">
                <path d="M5 13l4 4 10-10" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <svg v-else-if="value.icon === 'chat'" width="20" height="20" viewBox="0 0 24 24">
                <path d="M4 5.5h16v11H9l-5 3.5v-14.5Z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" />
              </svg>
              <svg v-else width="20" height="20" viewBox="0 0 24 24">
                <path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z" fill="none" stroke="currentColor" stroke-width="1.5" />
                <circle cx="12" cy="12" r="2.6" fill="none" stroke="currentColor" stroke-width="1.5" />
              </svg>
            </span>
            <h3>{{ value.title }}</h3>
            <p class="muted">{{ value.text }}</p>
          </article>
        </div>
      </div>
    </section>

    <section class="section section--alt">
      <div class="container cta-row">
        <div>
          <h2>¿Querés conocernos?</h2>
          <p class="lede">Escribinos o pasá por el estudio: atendemos con hora previa.</p>
        </div>
        <div class="row">
          <RouterLink class="btn btn--primary" to="/contacto">Contactar</RouterLink>
          <RouterLink class="btn btn--ghost" to="/comprar">Ver propiedades</RouterLink>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.page-head {
  padding-block: clamp(2.5rem, 2rem + 4vw, 4.5rem) 0;
  text-align: center;
}

.page-head h1 {
  margin-top: var(--space-3);
}

.page-head .lede {
  margin: var(--space-4) auto 0;
}

.prose {
  display: grid;
  gap: var(--space-4);
  font-size: var(--text-md);
  line-height: 1.8;
  color: var(--color-ink-soft);
}

.process__item {
  display: flex;
  gap: var(--space-4);
  padding: var(--space-5);
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-lg);
}

.process__step {
  font-family: var(--font-display);
  font-size: var(--text-xl);
  color: var(--color-bronze);
}

.value {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-5);
}

.value__icon {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: var(--color-sage-light);
  color: var(--color-sage-dark);
}

.cta-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-5);
}
</style>
