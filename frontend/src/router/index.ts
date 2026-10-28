import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { usePageMeta } from "../composables/usePageMeta";

export interface RouteMetaWithSEO {
  title?: string;
  description?: string;
  robots?: string;
}

const routes: RouteRecordRaw[] = [
  {
    path: "/",
    name: "home",
    component: () => import("../pages/HomePage.vue"),
    meta: {
      title: "Encontrá tu próximo lugar",
      description:
        "Propiedades seleccionadas en Quilmes, Bernal, Wilde y el sur del Gran Buenos Aires. Compra, alquiler, alquiler temporal y emprendimientos.",
    },
  },
  {
    path: "/comprar",
    name: "comprar",
    component: () => import("../pages/CatalogPage.vue"),
    meta: { mode: "buy" },
  },
  {
    path: "/alquilar",
    name: "alquilar",
    component: () => import("../pages/CatalogPage.vue"),
    meta: { mode: "rent" },
  },
  {
    path: "/alquiler-temporal",
    name: "alquiler-temporal",
    component: () => import("../pages/CatalogPage.vue"),
    meta: { mode: "temporary_rent" },
  },
  {
    path: "/emprendimientos",
    name: "emprendimientos",
    component: () => import("../pages/CatalogPage.vue"),
    meta: { mode: "development" },
  },
  {
    path: "/propiedades/:codigo",
    name: "property-detail",
    component: () => import("../pages/PropertyDetailPage.vue"),
    meta: { title: "Ficha de propiedad" },
  },
  {
    path: "/nosotros",
    name: "about",
    component: () => import("../pages/AboutPage.vue"),
    meta: {
      title: "Nosotros",
      description:
        "Conocé ALMATE Propiedades: equipo, forma de trabajo y servicios de compra, alquiler y tasación en el sur del GBA.",
    },
  },
  {
    path: "/contacto",
    name: "contact",
    component: () => import("../pages/ContactPage.vue"),
    meta: {
      title: "Contacto",
      description: "Escribinos o visitá nuestro estudio. Respondemos consultas sobre propiedades y operaciones.",
    },
  },
  {
    path: "/tasacion",
    name: "valuation",
    component: () => import("../pages/ValuationPage.vue"),
    meta: {
      title: "Solicitá una tasación",
      description: "Pedí una tasación sin cargo de tu propiedad y un asesor se comunica con vos.",
    },
  },
  {
    path: "/publicar-propiedad",
    name: "list-property",
    component: () => import("../pages/ListPropertyPage.vue"),
    meta: {
      title: "Publicá tu propiedad",
      description: "Contanos sobre tu propiedad y coordinamos una visita para publicarla en el sitio.",
    },
  },
  {
    path: "/:pathMatch(.*)*",
    name: "not-found",
    component: () => import("../pages/NotFoundPage.vue"),
    meta: { title: "Página no encontrada", robots: "noindex, follow" },
  },

  // --- Panel administrativo ------------------------------------------------
  {
    path: "/admin/login",
    name: "admin-login",
    component: () => import("../pages/admin/AdminLoginPage.vue"),
    meta: { title: "Ingresar al panel", robots: "noindex, nofollow", publicLogin: true },
  },
  {
    path: "/admin",
    component: () => import("../pages/admin/AdminLayout.vue"),
    meta: { requiresAuth: true, robots: "noindex, nofollow" },
    children: [
      { path: "", redirect: { name: "admin-dashboard" } },
      {
        path: "dashboard",
        name: "admin-dashboard",
        component: () => import("../pages/admin/DashboardPage.vue"),
        meta: { title: "Resumen", robots: "noindex, nofollow" },
      },
      {
        path: "propiedades",
        name: "admin-properties",
        component: () => import("../pages/admin/PropertiesListPage.vue"),
        meta: { title: "Propiedades", robots: "noindex, nofollow" },
      },
      {
        path: "propiedades/nueva",
        name: "admin-property-new",
        component: () => import("../pages/admin/PropertyEditPage.vue"),
        meta: { title: "Nueva propiedad", robots: "noindex, nofollow" },
      },
      {
        path: "propiedades/:id",
        name: "admin-property-edit",
        component: () => import("../pages/admin/PropertyEditPage.vue"),
        meta: { title: "Editar propiedad", robots: "noindex, nofollow" },
      },
      {
        path: "consultas",
        name: "admin-inquiries",
        component: () => import("../pages/admin/InquiriesPage.vue"),
        meta: { title: "Consultas", robots: "noindex, nofollow" },
      },
      {
        path: "tasaciones",
        name: "admin-valuations",
        component: () => import("../pages/admin/ValuationsPage.vue"),
        meta: { title: "Tasaciones", robots: "noindex, nofollow" },
      },
      {
        path: "publicaciones",
        name: "admin-listings",
        component: () => import("../pages/admin/ListingsPage.vue"),
        meta: { title: "Solicitudes de publicación", robots: "noindex, nofollow" },
      },
      {
        path: "configuracion",
        name: "admin-settings",
        component: () => import("../pages/admin/SettingsPage.vue"),
        meta: { title: "Configuración", robots: "noindex, nofollow" },
      },
    ],
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, _from, savedPosition) {
    if (savedPosition) return savedPosition;
    if (to.hash) return { el: to.hash, behavior: "smooth" };
    return { top: 0 };
  },
});

router.afterEach((to) => {
  const meta = to.meta as RouteMetaWithSEO;
  const { apply } = usePageMeta();
  apply({
    title: meta.title ?? "Propiedades",
    description: meta.description,
    robots: meta.robots,
  });
});

router.beforeEach((to) => {
  const auth = useAuthStore();

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: "admin-login", query: { next: to.fullPath } };
  }
  if (to.meta.publicLogin && auth.isAuthenticated) {
    return { name: "admin-dashboard" };
  }
  return true;
});
