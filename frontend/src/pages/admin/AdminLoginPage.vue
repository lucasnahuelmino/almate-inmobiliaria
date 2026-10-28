<script setup lang="ts">
/** Login del panel: valida contra la API real (bcrypt + JWT). */
import { ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "../../stores/auth";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const email = ref("");
const password = ref("");
const localError = ref<string | null>(null);

async function submit() {
  localError.value = null;

  if (!email.value.trim() || !password.value) {
    localError.value = "Completá el correo y la contraseña.";
    return;
  }

  const ok = await auth.login(email.value.trim(), password.value);
  if (ok) {
    const next = typeof route.query.next === "string" ? route.query.next : "/admin/dashboard";
    void router.replace(next);
  }
}
</script>

<template>
  <div class="login">
    <main class="login__card card">
      <div class="login__brand">
        <span class="login__mark" aria-hidden="true">A</span>
        <div>
          <p class="login__name">ALMATE Propiedades</p>
          <p class="login__descriptor">PANEL ADMINISTRATIVO</p>
        </div>
      </div>

      <h1 class="login__title">Iniciar sesión</h1>
      <p class="login__hint">
        Ingresá con tu usuario del estudio. El acceso está restringido al personal autorizado.
      </p>

      <div v-if="localError || auth.error" class="alert alert--error" role="alert">
        {{ localError ?? auth.error }}
      </div>

      <form class="login__form" novalidate @submit.prevent="submit">
        <div class="field">
          <label for="login-email">Correo electrónico</label>
          <input
            id="login-email"
            v-model="email"
            class="input"
            type="email"
            autocomplete="username"
            placeholder="admin@almate.demo"
            :aria-invalid="Boolean(localError && !email.trim())"
          />
        </div>

        <div class="field">
          <label for="login-password">Contraseña</label>
          <input
            id="login-password"
            v-model="password"
            class="input"
            type="password"
            autocomplete="current-password"
            placeholder="••••••••"
          />
        </div>

        <button class="btn btn--primary btn--block" type="submit" :disabled="auth.loading">
          {{ auth.loading ? "Verificando…" : "Ingresar" }}
        </button>
      </form>

      <p class="login__demo small">
        Cuenta de demostración: <strong>admin@almate.demo</strong> ·
        <strong>AlmateDemo2026!</strong>
      </p>

      <RouterLink class="login__back" to="/">← Volver al sitio público</RouterLink>
    </main>
  </div>
</template>

<style scoped>
.login {
  display: grid;
  place-items: center;
  min-height: 100vh;
  padding: var(--space-5);
  background:
    radial-gradient(900px 320px at 20% -10%, rgba(165, 139, 103, 0.18), transparent 60%),
    linear-gradient(180deg, #23241f 0%, #1a1b18 100%);
}

.login__card {
  width: min(100%, 420px);
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.login__brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.login__mark {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  background: var(--color-ink);
  color: var(--color-bronze);
  font-family: var(--font-display);
  font-size: 1.4rem;
  border-radius: var(--radius-sm);
}

.login__name {
  font-family: var(--font-display);
  font-size: 1.05rem;
  line-height: 1.2;
}

.login__descriptor {
  font-size: 0.65rem;
  letter-spacing: 0.24em;
  color: var(--color-stone-dark);
}

.login__title {
  font-size: var(--text-xl);
}

.login__hint {
  font-size: var(--text-sm);
  color: var(--color-stone-dark);
}

.login__form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.login__demo {
  padding: var(--space-3);
  background: var(--color-bronze-light);
  border-radius: var(--radius-sm);
  color: var(--color-bronze-dark);
}

.login__back {
  font-size: var(--text-sm);
  text-align: center;
}
</style>
