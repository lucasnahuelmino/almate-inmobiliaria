<script setup lang="ts">
/** Página de contacto: datos del estudio + formulario general. */
import { computed, onMounted } from "vue";
import { useSettingsStore } from "../stores/settings";
import ContactForm from "../components/ContactForm.vue";

const settingsStore = useSettingsStore();
const settings = computed(() => settingsStore.settings);

onMounted(() => {
  void settingsStore.loadSettings();
});
</script>

<template>
  <div>
    <header class="page-head">
      <div class="container container--narrow">
        <span class="eyebrow">Contacto</span>
        <h1>Escribinos y te respondemos</h1>
        <p class="lede">
          Consultas sobre propiedades, visitas, operaciones o publicaciones. Respondemos dentro
          de las 24 horas hábiles.
        </p>
      </div>
    </header>

    <section class="section">
      <div class="container contact-grid">
        <div class="contact-info">
          <h2 class="contact-info__title">Datos del estudio</h2>

          <dl class="contact-info__list">
            <div>
              <dt>Teléfono</dt>
              <dd>
                <a v-if="settings?.phone" :href="`tel:${settings.phone.replace(/\s/g, '')}`">
                  {{ settings.phone }}
                </a>
                <span v-else>—</span>
              </dd>
            </div>
            <div>
              <dt>Correo</dt>
              <dd>
                <a v-if="settings?.email" :href="`mailto:${settings.email}`">{{ settings.email }}</a>
                <span v-else>—</span>
              </dd>
            </div>
            <div>
              <dt>Dirección</dt>
              <dd>
                {{ settings?.address_line ?? "—" }}
                <span v-if="settings?.city">, {{ settings.city }}</span>
              </dd>
            </div>
            <div>
              <dt>Horarios</dt>
              <dd>{{ settings?.office_hours ?? "—" }}</dd>
            </div>
          </dl>

          <div v-if="settings?.whatsapp" class="contact-info__wa">
            <a
              class="btn btn--sage"
              :href="`https://wa.me/${settings.whatsapp.replace(/\D/g, '')}`"
              target="_blank"
              rel="noopener noreferrer"
            >
              Abrir WhatsApp
            </a>
            <p class="small muted">
              {{ settings.whatsapp_is_demo
                ? "Número ficticio de demostración: no envía mensajes reales."
                : "Se abre la conversación con el número guardado en la configuración." }}
            </p>
          </div>

          <div class="contact-info__links">
            <RouterLink class="link-btn" to="/tasacion">Solicitar una tasación</RouterLink>
            <RouterLink class="link-btn" to="/publicar-propiedad">Publicar mi propiedad</RouterLink>
          </div>
        </div>

        <div class="panel contact-form-panel">
          <h2 class="contact-form-panel__title">Formulario de consulta</h2>
          <ContactForm submit-label="Enviar consulta" />
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

.contact-grid {
  display: grid;
  gap: var(--space-6);
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.3fr);
  align-items: start;
}

.contact-info__title,
.contact-form-panel__title {
  font-size: var(--text-lg);
  margin-bottom: var(--space-4);
}

.contact-info__list {
  display: grid;
  gap: var(--space-3);
  margin: 0;
}

.contact-info__list > div {
  display: grid;
  grid-template-columns: 110px 1fr;
  gap: var(--space-3);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-line);
  font-size: var(--text-sm);
}

.contact-info__list dt {
  color: var(--color-stone-dark);
}

.contact-info__list dd {
  margin: 0;
  font-weight: 500;
}

.contact-info__wa {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  align-items: flex-start;
  margin-top: var(--space-5);
  padding: var(--space-4);
  background: var(--color-sage-light);
  border-radius: var(--radius-md);
}

.contact-info__links {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  align-items: flex-start;
  margin-top: var(--space-5);
}

@media (max-width: 860px) {
  .contact-grid {
    grid-template-columns: 1fr;
  }
}
</style>
