<script setup lang="ts">
/**
 * Armazón del panel: barra lateral, barra superior con el usuario y logout.
 * El `noindex` lo aplica el router (meta de todas las rutas /admin).
 */
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../../stores/auth";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const sidebarOpen = ref(false);

const navigation = [
  { to: "/admin/dashboard", label: "Resumen", icon: "grid" },
  { to: "/admin/propiedades", label: "Propiedades", icon: "home" },
  { to: "/admin/consultas", label: "Consultas", icon: "chat" },
  { to: "/admin/tasaciones", label: "Tasaciones", icon: "chart" },
  { to: "/admin/publicaciones", label: "Publicaciones", icon: "doc" },
  { to: "/admin/configuracion", label: "Configuración", icon: "settings" },
];

const sectionTitle = computed(() => {
  const title = route.meta.title;
  return typeof title === "string" ? title : "Panel";
});

const initials = computed(() => {
  const name = auth.user?.full_name ?? auth.user?.email ?? "";
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? "")
    .join("");
});

function closeSidebar() {
  sidebarOpen.value = false;
}

async function logout() {
  auth.logout();
  await router.replace({ name: "admin-login" });
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === "Escape") closeSidebar();
}

onMounted(() => window.addEventListener("keydown", onKeydown));
onUnmounted(() => window.removeEventListener("keydown", onKeydown));
</script>

<template>
  <div class="admin">
    <a class="skip-link" href="#admin-contenido">Saltar al contenido</a>

    <header class="admin__topbar">
      <button
        class="admin__burger"
        type="button"
        :aria-expanded="sidebarOpen"
        aria-controls="panel-lateral"
        @click="sidebarOpen = !sidebarOpen"
      >
        <span class="sr-only">{{ sidebarOpen ? "Cerrar menú" : "Abrir menú" }}</span>
        <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" />
        </svg>
      </button>

      <div class="admin__topbar-title">
        <span class="admin__topbar-brand">ALMATE · Panel</span>
        <strong>{{ sectionTitle }}</strong>
      </div>

      <div class="admin__topbar-right">
        <RouterLink class="admin__view-site" to="/" target="_blank" rel="noopener">
          Ver sitio
        </RouterLink>

        <div class="admin__user">
          <span class="admin__avatar" aria-hidden="true">{{ initials || "?" }}</span>
          <span class="admin__user-text">
            <strong>{{ auth.user?.full_name ?? "Usuario" }}</strong>
            <small>{{ auth.user?.role === "admin" ? "Administrador" : "Editor" }}</small>
          </span>
        </div>

        <button class="btn btn--ghost btn--sm" type="button" @click="logout">Salir</button>
      </div>
    </header>

    <div class="admin__body">
      <nav
        id="panel-lateral"
        class="admin__sidebar"
        :class="{ 'admin__sidebar--open': sidebarOpen }"
        aria-label="Navegación del panel"
      >
        <RouterLink
          v-for="item in navigation"
          :key="item.to"
          class="admin__link"
          :to="item.to"
          :class="{ 'admin__link--active': route.path.startsWith(item.to) }"
          @click="closeSidebar"
        >
          <span class="admin__link-icon" aria-hidden="true">
            <svg v-if="item.icon === 'grid'" width="17" height="17" viewBox="0 0 24 24">
              <rect x="4" y="4" width="7" height="7" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.6" />
              <rect x="13" y="4" width="7" height="7" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.6" />
              <rect x="4" y="13" width="7" height="7" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.6" />
              <rect x="13" y="13" width="7" height="7" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.6" />
            </svg>
            <svg v-else-if="item.icon === 'home'" width="17" height="17" viewBox="0 0 24 24">
              <path d="M4 20V9.5L12 4l8 5.5V20M9 20v-6h6v6" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" />
            </svg>
            <svg v-else-if="item.icon === 'chat'" width="17" height="17" viewBox="0 0 24 24">
              <path d="M4 5.5h16v11H9l-5 3.5v-14.5Z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" />
            </svg>
            <svg v-else-if="item.icon === 'chart'" width="17" height="17" viewBox="0 0 24 24">
              <path d="M4 19h16M7 16V9M12 16V5M17 16v-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
            </svg>
            <svg v-else-if="item.icon === 'doc'" width="17" height="17" viewBox="0 0 24 24">
              <path d="M6 3.5h8l4 4V20.5H6z" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" />
              <path d="M14 3.5v4h4" fill="none" stroke="currentColor" stroke-width="1.5" />
            </svg>
            <svg v-else width="17" height="17" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" stroke-width="1.5" />
              <path d="M12 3.5v2.2M12 18.3v2.2M3.5 12h2.2M18.3 12h2.2M6 6l1.6 1.6M16.4 16.4 18 18M18 6l-1.6 1.6M7.6 16.4 6 18" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
            </svg>
          </span>
          {{ item.label }}
        </RouterLink>

      </nav>

      <button
        v-if="sidebarOpen"
        class="admin__backdrop"
        type="button"
        aria-label="Cerrar menú"
        @click="closeSidebar"
      />

      <main id="admin-contenido" class="admin__content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.admin {
  min-height: 100vh;
  background: var(--color-bg-alt);
}

.admin__topbar {
  position: sticky;
  top: 0;
  z-index: 30;
  display: flex;
  align-items: center;
  gap: var(--space-4);
  min-height: 64px;
  padding-inline: var(--space-4);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-line);
}

.admin__burger {
  display: none;
  place-items: center;
  width: 40px;
  height: 40px;
  border: 1px solid var(--color-line-strong);
  border-radius: var(--radius-sm);
  color: var(--color-ink);
}

.admin__topbar-title {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.admin__topbar-brand {
  font-size: 0.65rem;
  letter-spacing: 0.2em;
  color: var(--color-bronze-dark);
}

.admin__topbar-title strong {
  font-family: var(--font-display);
  font-size: var(--text-md);
  font-weight: 500;
}

.admin__topbar-right {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-left: auto;
}

.admin__view-site {
  font-size: var(--text-sm);
  text-decoration: none;
}

.admin__user {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.admin__avatar {
  display: grid;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--color-ink);
  color: var(--color-bronze-light);
  font-size: var(--text-xs);
  font-weight: 600;
}

.admin__user-text {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.admin__user-text strong {
  font-size: var(--text-sm);
}

.admin__user-text small {
  font-size: var(--text-xs);
  color: var(--color-stone-dark);
}

.admin__body {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
}

.admin__sidebar {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-4) var(--space-3);
  background: var(--color-ink);
  min-height: calc(100vh - 64px);
}

.admin__link {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0.7rem 0.85rem;
  border-radius: var(--radius-sm);
  color: #cfccc4;
  font-size: var(--text-sm);
  font-weight: 500;
  text-decoration: none;
  transition: background-color var(--fast), color var(--fast);
}

.admin__link:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.admin__link--active {
  background: rgba(165, 139, 103, 0.22);
  color: var(--color-bronze-light);
}

.admin__link-icon {
  display: grid;
  place-items: center;
  width: 20px;
}

.admin__sidebar-foot {
  margin-top: auto;
}

.admin__backdrop {
  display: none;
}

.admin__content {
  padding: var(--space-5);
  min-width: 0;
}

@media (max-width: 900px) {
  .admin__burger {
    display: grid;
  }

  .admin__body {
    grid-template-columns: 1fr;
  }

  .admin__sidebar {
    position: fixed;
    inset: 64px auto 0 0;
    z-index: 40;
    width: 260px;
    transform: translateX(-100%);
    transition: transform var(--slow);
  }

  .admin__sidebar--open {
    transform: translateX(0);
  }

  .admin__backdrop {
    display: block;
    position: fixed;
    inset: 64px 0 0 0;
    z-index: 35;
    background: var(--color-overlay);
    border: none;
  }

  .admin__content {
    padding: var(--space-4);
  }

  .admin__user-text {
    display: none;
  }
}

@media (max-width: 560px) {
  .admin__view-site {
    display: none;
  }
}
</style>
