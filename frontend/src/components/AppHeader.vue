<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { useSettingsStore } from "../stores/settings";
import { useFavoritesStore } from "../stores/favorites";

const route = useRoute();
const settingsStore = useSettingsStore();
const favorites = useFavoritesStore();

const menuOpen = ref(false);

const links = computed(() => [
  { to: "/comprar", label: "Comprar" },
  { to: "/alquilar", label: "Alquilar" },
  { to: "/alquiler-temporal", label: "Alquiler temporal" },
  { to: "/emprendimientos", label: "Emprendimientos" },
  { to: "/nosotros", label: "Nosotros" },
  { to: "/contacto", label: "Contacto" },
]);

const brand = computed(() => settingsStore.settings?.brand_name ?? "ALMATE Propiedades");
const descriptor = computed(() => settingsStore.settings?.brand_descriptor ?? "PROPIEDADES");

function closeMenu() {
  menuOpen.value = false;
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === "Escape") closeMenu();
}

watch(
  () => route.fullPath,
  () => closeMenu(),
);

onMounted(() => window.addEventListener("keydown", onKeydown));
onUnmounted(() => window.removeEventListener("keydown", onKeydown));
</script>

<template>
  <header class="site-header">
    <div class="container site-header__inner">
      <RouterLink
        class="brand"
        to="/"
        :aria-label="`${brand} ${descriptor}, ir al inicio`"
      >
        <span class="brand__mark" aria-hidden="true"></span>
        <span class="brand__text">
          <span class="brand__name">{{ brand }}</span>
          <span class="brand__descriptor">{{ descriptor }}</span>
        </span>
      </RouterLink>

      <nav
        id="menu-principal"
        class="nav"
        :class="{ 'nav--open': menuOpen }"
        aria-label="Navegación principal"
      >
        <RouterLink
          v-for="link in links"
          :key="link.to"
          class="nav__link"
          :to="link.to"
          :class="{ 'nav__link--active': route.path === link.to }"
        >
          {{ link.label }}
        </RouterLink>
        <RouterLink class="nav__link nav__link--cta" to="/tasacion">
          Pedí una tasación
        </RouterLink>
      </nav>

      <div class="site-header__actions">
        <RouterLink class="favorites" to="/comprar?favoritos=1" title="Favoritos guardados en este dispositivo">
          <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
            <path
              d="M12 20.5 4.7 13a4.6 4.6 0 0 1 0-6.5 4.6 4.6 0 0 1 6.5 0l.8.8.8-.8a4.6 4.6 0 0 1 6.5 0 4.6 4.6 0 0 1 0 6.5Z"
              fill="none"
              stroke="currentColor"
              stroke-width="1.6"
            />
          </svg>
          <span class="favorites__count numeric">{{ favorites.codes.length }}</span>
          <span class="sr-only">propiedades guardadas como favoritas</span>
        </RouterLink>

        <button
          class="burger"
          type="button"
          :aria-expanded="menuOpen"
          aria-controls="menu-principal"
          @click="menuOpen = !menuOpen"
        >
          <span class="sr-only">{{ menuOpen ? "Cerrar menú" : "Abrir menú" }}</span>
          <span class="burger__bar" />
          <span class="burger__bar" />
          <span class="burger__bar" />
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.site-header {
  position: sticky;
  top: 0;
  z-index: 40;
  background: rgba(245, 242, 236, 0.92);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--color-line);
}

.site-header__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  min-height: var(--header-height);
}

.brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  text-decoration: none;
}

.brand__mark {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  background: var(--color-ink);
  color: var(--color-bronze);
  font-family: var(--font-display);
  font-size: 1.35rem;
  border-radius: var(--radius-sm);
}

/* La "A" del logotipo es decorativa: se dibuja con CSS para que no entre
   en el nombre accesible del enlace de marca. */
.brand__mark::before {
  content: "A";
}

.brand__text {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.brand__name {
  font-family: var(--font-display);
  font-size: 1.0625rem;
  letter-spacing: 0.01em;
}

.brand__descriptor {
  font-size: 0.65rem;
  letter-spacing: 0.28em;
  color: var(--color-stone-dark);
}

.nav {
  display: flex;
  align-items: center;
  gap: var(--space-5);
}

.nav__link {
  position: relative;
  font-size: var(--text-sm);
  font-weight: 500;
  text-decoration: none;
  padding-block: var(--space-2);
}

.nav__link::after {
  content: "";
  position: absolute;
  left: 0;
  bottom: 0;
  width: 100%;
  height: 2px;
  background: var(--color-bronze);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform var(--fast);
}

.nav__link:hover::after,
.nav__link--active::after {
  transform: scaleX(1);
}

.nav__link--cta {
  padding: 0.5rem 1rem;
  border: 1px solid var(--color-line-strong);
  border-radius: var(--radius-pill);
}

.nav__link--cta::after {
  display: none;
}

.nav__link--cta:hover {
  border-color: var(--color-bronze);
  color: var(--color-bronze-dark);
}

.site-header__actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.favorites {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: 0.4rem 0.7rem;
  border: 1px solid var(--color-line-strong);
  border-radius: var(--radius-pill);
  color: var(--color-ink-soft);
  text-decoration: none;
}

.favorites:hover {
  border-color: var(--color-bronze);
  color: var(--color-bronze-dark);
}

.favorites__count {
  font-size: var(--text-xs);
  font-weight: 600;
}

.burger {
  display: none;
  flex-direction: column;
  justify-content: center;
  gap: 5px;
  width: 44px;
  height: 44px;
  padding: 10px;
  border: 1px solid var(--color-line-strong);
  border-radius: var(--radius-sm);
}

.burger__bar {
  display: block;
  height: 2px;
  background: var(--color-ink);
}

@media (max-width: 980px) {
  .burger {
    display: flex;
  }

  .nav {
    position: absolute;
    top: var(--header-height);
    left: 0;
    right: 0;
    display: none;
    flex-direction: column;
    align-items: stretch;
    gap: 0;
    padding: var(--space-3) var(--space-4) var(--space-5);
    background: var(--color-bg);
    border-bottom: 1px solid var(--color-line);
    box-shadow: var(--shadow-md);
  }

  .nav--open {
    display: flex;
  }

  .nav__link {
    padding: var(--space-3) 0;
    border-bottom: 1px solid var(--color-line);
    font-size: var(--text-base);
  }

  .nav__link::after {
    display: none;
  }

  .nav__link--cta {
    margin-top: var(--space-3);
    text-align: center;
    border-bottom: 1px solid var(--color-line-strong);
  }
}
</style>
