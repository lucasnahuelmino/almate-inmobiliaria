<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useSettingsStore } from "../stores/settings";

const settingsStore = useSettingsStore();
const settings = computed(() => settingsStore.settings);

const CREDIT_FALLBACK = "Sitio demo desarrollado por ALMATE · Digital Studio";

const navigation = [
  { to: "/comprar", label: "Comprar" },
  { to: "/alquilar", label: "Alquilar" },
  { to: "/alquiler-temporal", label: "Alquiler temporal" },
  { to: "/emprendimientos", label: "Emprendimientos" },
  { to: "/tasacion", label: "Tasaciones" },
  { to: "/publicar-propiedad", label: "Publicá tu propiedad" },
];

const legalLinks = [
  { to: "/nosotros", label: "Nosotros" },
  { to: "/contacto", label: "Contacto" },
];

const socials = computed(() => {
  const current = settings.value;
  if (!current) return [];
  return [
    { label: "Instagram", href: current.instagram },
    { label: "Facebook", href: current.facebook },
    { label: "LinkedIn", href: current.linkedin },
  ].filter((item): item is { label: string; href: string } => Boolean(item.href));
});

onMounted(() => {
  void settingsStore.loadSettings();
});
</script>

<template>
  <footer class="site-footer">
    <div class="container site-footer__grid">
      <div class="site-footer__brand">
        <p class="site-footer__name">
          {{ settings?.brand_name ?? "ALMATE Propiedades" }}
        </p>
        <p class="site-footer__tagline">
          {{
            settings?.tagline ??
            "Propiedades seleccionadas en el sur del Gran Buenos Aires"
          }}
        </p>
        <p v-if="settings?.footer_note" class="site-footer__note">
          {{ settings.footer_note }}
        </p>
        <div v-if="socials.length" class="site-footer__social">
          <a
            v-for="social in socials"
            :key="social.label"
            :href="social.href"
            target="_blank"
            rel="noopener noreferrer"
          >
            {{ social.label }}
          </a>
        </div>
      </div>

      <nav class="site-footer__col" aria-label="Explorar propiedades">
        <h2 class="site-footer__title">Explorar</h2>
        <RouterLink v-for="link in navigation" :key="link.to" :to="link.to">
          {{ link.label }}
        </RouterLink>
      </nav>

      <nav class="site-footer__col" aria-label="Información institucional">
        <h2 class="site-footer__title">Estudio</h2>
        <RouterLink v-for="link in legalLinks" :key="link.to" :to="link.to">
          {{ link.label }}
        </RouterLink>
        <RouterLink to="/admin/login">Panel administrativo</RouterLink>
      </nav>

      <address class="site-footer__col site-footer__address">
        <h2 class="site-footer__title">Contacto</h2>
        <a v-if="settings?.phone" :href="`tel:${settings.phone.replace(/\s/g, '')}`">
          {{ settings.phone }}
        </a>
        <a v-if="settings?.email" :href="`mailto:${settings.email}`">
          {{ settings.email }}
        </a>
        <span v-if="settings?.address_line">{{ settings.address_line }}</span>
        <span v-if="settings?.city">{{ settings.city }}</span>
        <span v-if="settings?.office_hours">{{ settings.office_hours }}</span>
      </address>
    </div>

    <div class="site-footer__bottom">
      <div class="container site-footer__bottom-inner">
        <p>{{ settings?.developer_credit ?? CREDIT_FALLBACK }}</p>
        <p class="small">
          Precios y datos de las propiedades con fines de demostración.
        </p>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.site-footer {
  margin-top: var(--space-8);
  background: var(--color-ink);
  color: #e9e6df;
}

.site-footer__grid {
  display: grid;
  gap: var(--space-6);
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 220px), 1fr));
  padding-block: var(--space-7);
}

.site-footer__name {
  font-family: var(--font-display);
  font-size: var(--text-lg);
}

.site-footer__tagline,
.site-footer__note {
  margin-top: var(--space-2);
  color: #a9a79f;
  font-size: var(--text-sm);
}

.site-footer__social {
  display: flex;
  gap: var(--space-4);
  margin-top: var(--space-4);
  font-size: var(--text-sm);
}

.site-footer__social a {
  color: var(--color-bronze-light);
}

.site-footer__title {
  font-family: var(--font-ui);
  font-size: var(--text-xs);
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--color-bronze);
  margin-bottom: var(--space-3);
}

.site-footer__col {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  font-size: var(--text-sm);
  font-style: normal;
}

.site-footer__col a {
  color: #d8d5cd;
  text-decoration: none;
}

.site-footer__col a:hover {
  color: var(--color-bronze-light);
  text-decoration: underline;
}

.site-footer__col span {
  color: #a9a79f;
}

.site-footer__bottom {
  border-top: 1px solid rgba(255, 255, 255, 0.12);
}

.site-footer__bottom-inner {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--space-3);
  padding-block: var(--space-4);
  font-size: var(--text-sm);
  color: #a9a79f;
}
</style>
