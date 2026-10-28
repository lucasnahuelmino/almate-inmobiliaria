<script setup lang="ts">
/**
 * Solicitud de tasación: se confirma recién cuando el servidor registra la
 * solicitud (nada de "enviado" local sin respuesta del backend).
 */
import { reactive, ref } from "vue";
import { ApiError, api } from "../api/client";
import type { AcceptedResponse } from "../api/types";

const form = reactive({
  name: "",
  email: "",
  phone: "",
  propertyType: "apartment",
  operation: "buy",
  locality: "",
  neighborhood: "",
  surface: "",
  bedrooms: "",
  message: "",
});

const sending = ref(false);
const confirmed = ref<string | null>(null);
const serverError = ref<string | null>(null);
const fieldErrors = reactive<Record<string, string>>({});

const PROPERTY_TYPES = [
  { value: "apartment", label: "Departamento" },
  { value: "house", label: "Casa" },
  { value: "ph", label: "PH" },
  { value: "land", label: "Terreno" },
  { value: "commercial", label: "Local comercial" },
  { value: "office", label: "Oficina" },
];

function validate(): boolean {
  Object.keys(fieldErrors).forEach((key) => delete fieldErrors[key]);

  if (form.name.trim().length < 2) fieldErrors.name = "Ingresá tu nombre y apellido.";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(form.email.trim())) {
    fieldErrors.email = "Ingresá un correo electrónico válido.";
  }
  if (form.phone.trim() && !/^[0-9\s()+.\-]{5,40}$/.test(form.phone.trim())) {
    fieldErrors.phone = "El teléfono sólo admite números y los símbolos + ( ) . -";
  }
  if (form.locality.trim().length < 2) fieldErrors.locality = "Indicá la localidad.";
  if (form.surface.trim() && !/^\d{1,6}([.,]\d{1,2})?$/.test(form.surface.trim())) {
    fieldErrors.surface = "Ingresá la superficie en m² (números, por ejemplo 85 o 85.5).";
  }
  return Object.keys(fieldErrors).length === 0;
}

async function submit() {
  serverError.value = null;
  confirmed.value = null;
  if (!validate()) return;

  sending.value = true;
  try {
    const response = await api.post<AcceptedResponse>("/valuation-requests", {
      name: form.name.trim(),
      email: form.email.trim(),
      phone: form.phone.trim() || null,
      property_type: form.propertyType,
      operation: form.operation,
      locality: form.locality.trim(),
      neighborhood: form.neighborhood.trim() || null,
      surface_covered: form.surface.trim() || null,
      bedrooms: form.bedrooms.trim() || null,
      message: form.message.trim() || null,
    });
    confirmed.value = response.message;
    Object.assign(form, {
      name: "",
      email: "",
      phone: "",
      locality: "",
      neighborhood: "",
      surface: "",
      bedrooms: "",
      message: "",
    });
  } catch (caught) {
    if (caught instanceof ApiError) {
      serverError.value = caught.message;
      for (const error of caught.errors) {
        const field = error.loc[error.loc.length - 1];
        if (field) fieldErrors[field] = error.msg;
      }
    } else {
      serverError.value = "No pudimos registrar la solicitud. Intentá nuevamente.";
    }
  } finally {
    sending.value = false;
  }
}
</script>

<template>
  <div>
    <header class="page-head">
      <div class="container container--narrow">
        <span class="eyebrow">Tasación</span>
        <h1>Solicitá una tasación sin cargo</h1>
        <p class="lede">
          Completá los datos de tu propiedad y un asesor prepara un informe comparativo del
          mercado zonal. La solicitud queda registrada recién cuando el servidor la confirma.
        </p>
      </div>
    </header>

    <section class="section">
      <div class="container valuation-grid">
        <div class="panel form-panel">
          <div v-if="confirmed" class="alert alert--success" role="status">
            <strong>Solicitud registrada.</strong>
            <span>{{ confirmed }}</span>
          </div>

          <div v-if="serverError" class="alert alert--error" role="alert">
            {{ serverError }}
          </div>

          <form novalidate @submit.prevent="submit">
            <fieldset>
              <legend>Quién solicita la tasación</legend>
              <div class="form-grid">
                <div class="field">
                  <label for="tas-nombre">Nombre y apellido *</label>
                  <input
                    id="tas-nombre"
                    v-model="form.name"
                    class="input"
                    type="text"
                    autocomplete="name"
                    :aria-invalid="Boolean(fieldErrors.name)"
                  />
                  <span v-if="fieldErrors.name" class="error">{{ fieldErrors.name }}</span>
                </div>
                <div class="field">
                  <label for="tas-email">Correo electrónico *</label>
                  <input
                    id="tas-email"
                    v-model="form.email"
                    class="input"
                    type="email"
                    autocomplete="email"
                    :aria-invalid="Boolean(fieldErrors.email)"
                  />
                  <span v-if="fieldErrors.email" class="error">{{ fieldErrors.email }}</span>
                </div>
                <div class="field">
                  <label for="tas-telefono">Teléfono (opcional)</label>
                  <input
                    id="tas-telefono"
                    v-model="form.phone"
                    class="input"
                    type="tel"
                    autocomplete="tel"
                    placeholder="+54 9 11 5555-0000"
                    :aria-invalid="Boolean(fieldErrors.phone)"
                  />
                  <span v-if="fieldErrors.phone" class="error">{{ fieldErrors.phone }}</span>
                </div>
              </div>
            </fieldset>

            <fieldset>
              <legend>Datos de la propiedad</legend>
              <div class="form-grid">
                <div class="field">
                  <label for="tas-tipo">Tipo de propiedad *</label>
                  <select id="tas-tipo" v-model="form.propertyType" class="select">
                    <option v-for="option in PROPERTY_TYPES" :key="option.value" :value="option.value">
                      {{ option.label }}
                    </option>
                  </select>
                </div>

                <div class="field">
                  <label for="tas-operacion">Operación pretendida</label>
                  <select id="tas-operacion" v-model="form.operation" class="select">
                    <option value="buy">Venta</option>
                    <option value="rent">Alquiler</option>
                    <option value="temporary_rent">Alquiler temporal</option>
                  </select>
                </div>

                <div class="field">
                  <label for="tas-localidad">Localidad *</label>
                  <input
                    id="tas-localidad"
                    v-model="form.locality"
                    class="input"
                    type="text"
                    placeholder="Quilmes"
                    :aria-invalid="Boolean(fieldErrors.locality)"
                  />
                  <span v-if="fieldErrors.locality" class="error">{{ fieldErrors.locality }}</span>
                </div>

                <div class="field">
                  <label for="tas-barrio">Barrio (opcional)</label>
                  <input id="tas-barrio" v-model="form.neighborhood" class="input" type="text" placeholder="Bernal" />
                </div>

                <div class="field">
                  <label for="tas-superficie">Superficie cubierta (m²)</label>
                  <input
                    id="tas-superficie"
                    v-model="form.surface"
                    class="input numeric"
                    type="text"
                    inputmode="decimal"
                    placeholder="85"
                    :aria-invalid="Boolean(fieldErrors.surface)"
                  />
                  <span v-if="fieldErrors.surface" class="error">{{ fieldErrors.surface }}</span>
                </div>

                <div class="field">
                  <label for="tas-dormitorios">Dormitorios</label>
                  <select id="tas-dormitorios" v-model="form.bedrooms" class="select">
                    <option value="">No corresponde</option>
                    <option v-for="n in 7" :key="n" :value="String(n - 1)">{{ n - 1 }}</option>
                  </select>
                </div>

                <div class="field field--full">
                  <label for="tas-mensaje">Comentarios (opcional)</label>
                  <textarea
                    id="tas-mensaje"
                    v-model="form.message"
                    class="textarea"
                    rows="4"
                    placeholder="Contanos detalles: estado, expensas, si está amoblada, plazos…"
                  />
                </div>
              </div>
            </fieldset>

            <button class="btn btn--bronze" type="submit" :disabled="sending">
              {{ sending ? "Enviando solicitud…" : "Solicitar tasación" }}
            </button>

            <p class="hint small">
              Usamos tus datos sólo para preparar la tasación y contactarte. No los compartimos
              con terceros.
            </p>
          </form>
        </div>

        <aside class="side">
          <div class="panel">
            <h2 class="side__title">¿Qué incluye?</h2>
            <ul class="side__list">
              <li>Análisis de propiedades comparables de la zona</li>
              <li>Rango de valor de mercado por metro cuadrado</li>
              <li>Recomendación de precio de publicación</li>
              <li>Plazo estimado de venta o alquiler</li>
            </ul>
          </div>
          <div class="panel">
            <h2 class="side__title">Tiempo de respuesta</h2>
            <p class="muted">
              Recibís el informe dentro de los 3 días hábiles siguientes a la solicitud. Si
              necesitás una tasación urgente, escribinos por WhatsApp desde la página de
              contacto.
            </p>
          </div>
        </aside>
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

.valuation-grid {
  display: grid;
  gap: var(--space-6);
  grid-template-columns: minmax(0, 1.7fr) minmax(0, 1fr);
  align-items: start;
}

.form-panel form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.form-panel fieldset + fieldset {
  margin-top: var(--space-2);
}

.field--full {
  grid-column: 1 / -1;
}

.side {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.side__title {
  font-size: var(--text-lg);
  margin-bottom: var(--space-3);
}

.side__list {
  display: grid;
  gap: var(--space-2);
  padding-left: 1.1rem;
  color: var(--color-ink-soft);
  font-size: var(--text-sm);
}

.side__list li::marker {
  color: var(--color-bronze);
}

@media (max-width: 860px) {
  .valuation-grid {
    grid-template-columns: 1fr;
  }
}
</style>
