<script setup lang="ts">
/**
 * "Publicá tu propiedad": los propietarios dejan los datos del inmueble y el
 * estudio se pone en contacto. Confirmación sólo tras la respuesta del servidor.
 */
import { reactive, ref } from "vue";
import { ApiError, api } from "../api/client";
import type { AcceptedResponse } from "../api/types";

const form = reactive({
  name: "",
  email: "",
  phone: "",
  operation: "buy",
  propertyType: "apartment",
  locality: "",
  neighborhood: "",
  surface: "",
  bedrooms: "",
  expectedPrice: "",
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
    fieldErrors.surface = "Ingresá la superficie en m² (por ejemplo 85).";
  }
  if (form.message.trim().length < 10) {
    fieldErrors.message = "Contanos un poco más: al menos 10 caracteres.";
  }
  return Object.keys(fieldErrors).length === 0;
}

async function submit() {
  serverError.value = null;
  confirmed.value = null;
  if (!validate()) return;

  sending.value = true;
  try {
    const response = await api.post<AcceptedResponse>("/listing-requests", {
      name: form.name.trim(),
      email: form.email.trim(),
      phone: form.phone.trim() || null,
      operation: form.operation,
      property_type: form.propertyType,
      locality: form.locality.trim(),
      neighborhood: form.neighborhood.trim() || null,
      surface_covered: form.surface.trim() || null,
      bedrooms: form.bedrooms.trim() || null,
      expected_price: form.expectedPrice.trim() || null,
      message: form.message.trim(),
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
      expectedPrice: "",
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
        <span class="eyebrow">Para propietarios</span>
        <h1>Publicá tu propiedad</h1>
        <p class="lede">
          Contanos sobre tu propiedad y coordinamos una visita para fotografiarla, tasarla y
          publicarla en el catálogo del estudio.
        </p>
      </div>
    </header>

    <section class="section">
      <div class="container listing-grid">
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
              <legend>Datos de contacto</legend>
              <div class="form-grid">
                <div class="field">
                  <label for="pub-nombre">Nombre y apellido *</label>
                  <input
                    id="pub-nombre"
                    v-model="form.name"
                    class="input"
                    type="text"
                    autocomplete="name"
                    :aria-invalid="Boolean(fieldErrors.name)"
                  />
                  <span v-if="fieldErrors.name" class="error">{{ fieldErrors.name }}</span>
                </div>
                <div class="field">
                  <label for="pub-email">Correo electrónico *</label>
                  <input
                    id="pub-email"
                    v-model="form.email"
                    class="input"
                    type="email"
                    autocomplete="email"
                    :aria-invalid="Boolean(fieldErrors.email)"
                  />
                  <span v-if="fieldErrors.email" class="error">{{ fieldErrors.email }}</span>
                </div>
                <div class="field">
                  <label for="pub-telefono">Teléfono (opcional)</label>
                  <input
                    id="pub-telefono"
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
                  <label for="pub-operacion">Operación deseada *</label>
                  <select id="pub-operacion" v-model="form.operation" class="select">
                    <option value="buy">Vender</option>
                    <option value="rent">Alquilar</option>
                    <option value="temporary_rent">Alquiler temporal</option>
                  </select>
                </div>

                <div class="field">
                  <label for="pub-tipo">Tipo de propiedad *</label>
                  <select id="pub-tipo" v-model="form.propertyType" class="select">
                    <option v-for="option in PROPERTY_TYPES" :key="option.value" :value="option.value">
                      {{ option.label }}
                    </option>
                  </select>
                </div>

                <div class="field">
                  <label for="pub-localidad">Localidad *</label>
                  <input
                    id="pub-localidad"
                    v-model="form.locality"
                    class="input"
                    type="text"
                    placeholder="Wilde"
                    :aria-invalid="Boolean(fieldErrors.locality)"
                  />
                  <span v-if="fieldErrors.locality" class="error">{{ fieldErrors.locality }}</span>
                </div>

                <div class="field">
                  <label for="pub-barrio">Barrio (opcional)</label>
                  <input id="pub-barrio" v-model="form.neighborhood" class="input" type="text" />
                </div>

                <div class="field">
                  <label for="pub-superficie">Superficie cubierta (m²)</label>
                  <input
                    id="pub-superficie"
                    v-model="form.surface"
                    class="input numeric"
                    type="text"
                    inputmode="decimal"
                    placeholder="72"
                    :aria-invalid="Boolean(fieldErrors.surface)"
                  />
                  <span v-if="fieldErrors.surface" class="error">{{ fieldErrors.surface }}</span>
                </div>

                <div class="field">
                  <label for="pub-dormitorios">Dormitorios</label>
                  <select id="pub-dormitorios" v-model="form.bedrooms" class="select">
                    <option value="">No corresponde</option>
                    <option v-for="n in 7" :key="n" :value="String(n - 1)">{{ n - 1 }}</option>
                  </select>
                </div>

                <div class="field">
                  <label for="pub-precio">Precio esperado (opcional)</label>
                  <input
                    id="pub-precio"
                    v-model="form.expectedPrice"
                    class="input"
                    type="text"
                    placeholder="USD 90.000 o a convenir"
                  />
                  <span class="hint">Podés dejarlo en blanco: lo definimos en la tasación.</span>
                </div>

                <div class="field field--full">
                  <label for="pub-mensaje">Contanos sobre la propiedad *</label>
                  <textarea
                    id="pub-mensaje"
                    v-model="form.message"
                    class="textarea"
                    rows="5"
                    placeholder="Estado, expensas, antigüedad, si tiene documentación al día…"
                    :aria-invalid="Boolean(fieldErrors.message)"
                  />
                  <span v-if="fieldErrors.message" class="error">{{ fieldErrors.message }}</span>
                </div>
              </div>
            </fieldset>

            <button class="btn btn--bronze" type="submit" :disabled="sending">
              {{ sending ? "Enviando solicitud…" : "Enviar solicitud" }}
            </button>

            <p class="hint small">
              Usamos estos datos únicamente para coordinar la publicación. No los compartimos
              con terceros.
            </p>
          </form>
        </div>

        <aside class="side">
          <div class="panel">
            <h2 class="side__title">Cómo publicamos</h2>
            <ol class="side__steps">
              <li><strong>Visita técnica:</strong> medidas, fotos y documentación.</li>
              <li><strong>Tasación:</strong> rango de precio según comparables.</li>
              <li><strong>Ficha:</strong> redacción y selección de fotografías.</li>
              <li><strong>Publicación:</strong> sitio, WhatsApp y redes del estudio.</li>
            </ol>
          </div>
          <div class="panel">
            <h2 class="side__title">¿Sólo querés saber el valor?</h2>
            <p class="muted">
              Si no buscás publicar todavía, pedí directamente una tasación sin cargo.
            </p>
            <RouterLink class="link-btn" to="/tasacion">Ir a la tasación</RouterLink>
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

.listing-grid {
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

.side__steps {
  display: grid;
  gap: var(--space-3);
  padding-left: 1.2rem;
  font-size: var(--text-sm);
  color: var(--color-ink-soft);
}

.side__steps li::marker {
  color: var(--color-bronze);
  font-weight: 600;
}

.side .link-btn {
  display: inline-block;
  margin-top: var(--space-3);
}

@media (max-width: 860px) {
  .listing-grid {
    grid-template-columns: 1fr;
  }
}
</style>
