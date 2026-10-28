<script setup lang="ts">
/** 404: explica el error y ofrece rutas reales para continuar. */
const suggestions = [
  { to: "/comprar", label: "Propiedades en venta" },
  { to: "/alquilar", label: "Propiedades en alquiler" },
  { to: "/alquiler-temporal", label: "Alquiler temporal" },
  { to: "/emprendimientos", label: "Emprendimientos" },
  { to: "/contacto", label: "Contacto" },
];
</script>

<template>
  <section class="section not-found">
    <div class="container container--narrow not-found__inner">
      <span class="not-found__code numeric" aria-hidden="true">404</span>
      <h1>Esta página no existe</h1>
      <p class="lede">
        Puede que el enlace esté incompleto o que la propiedad se haya dado de baja del
        catálogo. Probá con alguna de estas opciones:
      </p>

      <ul class="not-found__links">
        <li v-for="suggestion in suggestions" :key="suggestion.to">
          <RouterLink class="link-btn" :to="suggestion.to">{{ suggestion.label }}</RouterLink>
        </li>
      </ul>

      <div class="row not-found__actions">
        <RouterLink class="btn btn--primary" to="/">Volver al inicio</RouterLink>
        <RouterLink class="btn btn--ghost" to="/contacto">Reportar un problema</RouterLink>
      </div>
    </div>
  </section>
</template>

<style scoped>
.not-found__inner {
  text-align: center;
}

.not-found__code {
  display: block;
  font-family: var(--font-display);
  font-size: clamp(4rem, 3rem + 8vw, 8rem);
  line-height: 1;
  color: var(--color-bronze);
}

.not-found h1 {
  margin-top: var(--space-3);
}

.not-found .lede {
  margin: var(--space-4) auto 0;
}

.not-found__links {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--space-3) var(--space-5);
  padding: 0;
  margin: var(--space-6) 0 0;
  list-style: none;
}

.not-found__actions {
  justify-content: center;
  margin-top: var(--space-6);
}
</style>
