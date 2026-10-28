<script setup lang="ts">
/**
 * Formulario de consulta reutilizable (ficha de propiedad y contacto general).
 * La confirmación se muestra sólo después de que el servidor confirma el alta.
 */
import { computed, reactive, ref } from "vue";
import { ApiError, api } from "../api/client";
import type { AcceptedResponse, Operation } from "../api/types";

const props = withDefaults(
  defineProps<{
    propertyCode?: string;
    propertyTitle?: string;
    operation?: Operation | "";
    location?: string;
    submitLabel?: string;
    defaultMessage?: string;
  }>(),
  {
    propertyCode: "",
    propertyTitle: "",
    operation: "",
    location: "",
    submitLabel: "Enviar consulta",
    defaultMessage: "",
  },
);

const form = reactive({
  name: "",
  email: "",
  phone: "",
  message: props.defaultMessage,
});

const sending = ref(false);
const success = ref<string | null>(null);
const serverError = ref<string | null>(null);
const fieldErrors = reactive<Record<string, string>>({});

const context = computed(() =>
  [props.propertyTitle, props.operation, props.location].filter(Boolean).join(" · "),
);

function validate(): boolean {
  Object.keys(fieldErrors).forEach((key) => delete fieldErrors[key]);

  if (form.name.trim().length < 2) fieldErrors.name = "Ingresá tu nombre y apellido.";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(form.email.trim())) {
    fieldErrors.email = "Ingresá un correo electrónico válido.";
  }
  if (form.phone.trim() && !/^[0-9\s()+.\-]{5,40}$/.test(form.phone.trim())) {
    fieldErrors.phone = "El teléfono sólo admite números y los símbolos + ( ) . -";
  }
  if (form.message.trim().length < 10) {
    fieldErrors.message = "Contanos un poco más: al menos 10 caracteres.";
  }
  return Object.keys(fieldErrors).length === 0;
}

async function submit() {
  serverError.value = null;
  success.value = null;
  if (!validate()) return;

  sending.value = true;
  try {
    const response = await api.post<AcceptedResponse>("/inquiries", {
      name: form.name.trim(),
      email: form.email.trim(),
      phone: form.phone.trim() || null,
      message: form.message.trim(),
      property_code: props.propertyCode || null,
    });
    success.value = response.message;
    form.message = props.defaultMessage;
  } catch (caught) {
    if (caught instanceof ApiError) {
      serverError.value = caught.message;
      for (const error of caught.errors) {
        const field = error.loc[error.loc.length - 1];
        if (field) fieldErrors[field] = error.msg;
      }
    } else {
      serverError.value = "No pudimos enviar tu consulta. Intentá nuevamente.";
    }
  } finally {
    sending.value = false;
  }
}
</script>

<template>
  <form class="contact-form" novalidate @submit.prevent="submit">
    <div v-if="success" class="alert alert--success" role="status">
      <strong>Consulta enviada.</strong>
      <span>{{ success }}</span>
    </div>

    <div v-if="serverError" class="alert alert--error" role="alert">
      {{ serverError }}
    </div>

    <p v-if="propertyCode" class="contact-form__context small">
      Consulta por la propiedad <strong>{{ propertyCode }}</strong>
      <span v-if="context"> — {{ context }}</span>
    </p>

    <div class="form-grid">
      <div class="field">
        <label for="consulta-nombre">Nombre y apellido *</label>
        <input
          id="consulta-nombre"
          v-model="form.name"
          class="input"
          type="text"
          autocomplete="name"
          :aria-invalid="Boolean(fieldErrors.name)"
          :aria-describedby="fieldErrors.name ? 'consulta-nombre-error' : undefined"
        />
        <span v-if="fieldErrors.name" id="consulta-nombre-error" class="error">
          {{ fieldErrors.name }}
        </span>
      </div>

      <div class="field">
        <label for="consulta-email">Correo electrónico *</label>
        <input
          id="consulta-email"
          v-model="form.email"
          class="input"
          type="email"
          autocomplete="email"
          :aria-invalid="Boolean(fieldErrors.email)"
          :aria-describedby="fieldErrors.email ? 'consulta-email-error' : undefined"
        />
        <span v-if="fieldErrors.email" id="consulta-email-error" class="error">
          {{ fieldErrors.email }}
        </span>
      </div>

      <div class="field">
        <label for="consulta-telefono">Teléfono (opcional)</label>
        <input
          id="consulta-telefono"
          v-model="form.phone"
          class="input"
          type="tel"
          autocomplete="tel"
          placeholder="+54 9 11 5555-0000"
          :aria-invalid="Boolean(fieldErrors.phone)"
        />
        <span v-if="fieldErrors.phone" class="error">{{ fieldErrors.phone }}</span>
      </div>

      <div class="field field--full">
        <label for="consulta-mensaje">Mensaje *</label>
        <textarea
          id="consulta-mensaje"
          v-model="form.message"
          class="textarea"
          rows="5"
          :aria-invalid="Boolean(fieldErrors.message)"
        />
        <span v-if="fieldErrors.message" class="error">{{ fieldErrors.message }}</span>
        <span class="hint">Respondemos dentro de las 24 horas hábiles.</span>
      </div>
    </div>

    <button class="btn btn--bronze" type="submit" :disabled="sending">
      {{ sending ? "Enviando…" : submitLabel }}
    </button>

    <p class="hint small">
      Al enviar aceptás que te contactemos por correo o teléfono. No compartimos tus datos
      con terceros.
    </p>
  </form>
</template>

<style scoped>
.contact-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.contact-form__context {
  padding: var(--space-3);
  background: var(--color-bronze-light);
  border-radius: var(--radius-sm);
  color: var(--color-bronze-dark);
}

.field--full {
  grid-column: 1 / -1;
}
</style>
