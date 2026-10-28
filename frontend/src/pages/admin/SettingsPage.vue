<script setup lang="ts">
/**
 * Configuración del negocio: datos de contacto, marca y comportamiento del
 * sitio público. Sólo el rol admin puede guardar (el backend lo exige).
 */
import { onMounted, reactive, ref } from "vue";
import { ApiError, api } from "../../api/client";
import type { PublicSettings } from "../../api/types";
import { useAuthStore } from "../../stores/auth";
import { useSettingsStore } from "../../stores/settings";
import LoadingBlock from "../../components/LoadingBlock.vue";
import ErrorState from "../../components/ErrorState.vue";

type AdminSettings = PublicSettings & { id: number; created_at: string; updated_at: string };

const auth = useAuthStore();
const settingsStore = useSettingsStore();

const loading = ref(true);
const saving = ref(false);
const error = ref<string | null>(null);
const notice = ref<{ type: "success" | "error"; text: string } | null>(null);
const fieldErrors = reactive<Record<string, string>>({});

const form = reactive({
  brand_name: "",
  brand_descriptor: "",
  tagline: "",
  phone: "",
  whatsapp: "",
  whatsapp_is_demo: true,
  email: "",
  address_line: "",
  city: "",
  office_hours: "",
  instagram: "",
  facebook: "",
  linkedin: "",
  institutional_text: "",
  footer_note: "",
  default_currency: "USD" as "ARS" | "USD" | "EUR",
  show_expenses: true,
});

const canEdit = () => auth.isAdmin;

function apply(data: AdminSettings) {
  Object.assign(form, {
    brand_name: data.brand_name,
    brand_descriptor: data.brand_descriptor,
    tagline: data.tagline,
    phone: data.phone,
    whatsapp: data.whatsapp,
    whatsapp_is_demo: data.whatsapp_is_demo,
    email: data.email,
    address_line: data.address_line,
    city: data.city,
    office_hours: data.office_hours,
    instagram: data.instagram ?? "",
    facebook: data.facebook ?? "",
    linkedin: data.linkedin ?? "",
    institutional_text: data.institutional_text,
    footer_note: data.footer_note,
    default_currency: data.default_currency,
    show_expenses: data.show_expenses,
  });
}

async function load() {
  loading.value = true;
  error.value = null;
  try {
    apply(await api.get<AdminSettings>("/admin/settings", { auth: true }));
  } catch (caught) {
    error.value =
      caught instanceof ApiError ? caught.message : "No pudimos cargar la configuración.";
  } finally {
    loading.value = false;
  }
}

async function save() {
  notice.value = null;
  Object.keys(fieldErrors).forEach((key) => delete fieldErrors[key]);

  if (!form.brand_name.trim() || form.brand_name.trim().length < 2) {
    fieldErrors.brand_name = "El nombre de la marca debe tener al menos 2 caracteres.";
  }
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(form.email.trim())) {
    fieldErrors.email = "Ingresá un correo electrónico válido.";
  }
  if (Object.keys(fieldErrors).length) {
    notice.value = { type: "error", text: "Revisá los campos marcados." };
    return;
  }

  saving.value = true;
  try {
    const payload = {
      ...form,
      email: form.email.trim(),
      instagram: form.instagram.trim() || null,
      facebook: form.facebook.trim() || null,
      linkedin: form.linkedin.trim() || null,
    };
    const updated = await api.put<AdminSettings>("/admin/settings", payload, { auth: true });
    apply(updated);
    // Refresca los datos que usa el sitio público.
    await settingsStore.loadSettings(true);
    notice.value = { type: "success", text: "Configuración guardada y aplicada al sitio." };
  } catch (caught) {
    if (caught instanceof ApiError) {
      for (const item of caught.errors) {
        const field = item.loc[item.loc.length - 1];
        if (field && !fieldErrors[field]) fieldErrors[field] = item.msg;
      }
      notice.value = { type: "error", text: caught.message };
    } else {
      notice.value = { type: "error", text: "No pudimos guardar la configuración." };
    }
  } finally {
    saving.value = false;
  }
}

onMounted(() => void load());
</script>

<template>
  <div>
    <div class="admin-head">
      <div>
        <h1>Configuración</h1>
        <p class="muted small">Datos del negocio que usa todo el sitio público.</p>
      </div>
      <button
        v-if="canEdit()"
        class="btn btn--primary"
        type="button"
        :disabled="saving"
        @click="save"
      >
        {{ saving ? "Guardando…" : "Guardar cambios" }}
      </button>
    </div>

    <LoadingBlock v-if="loading" label="Cargando configuración…" />
    <ErrorState v-else-if="error" :message="error" @retry="load" />

    <template v-else>
      <div v-if="!canEdit()" class="alert alert--info">
        Tu rol (editor) puede consultar esta información, pero sólo un administrador puede
        modificarla.
      </div>

      <div v-if="notice" class="alert" :class="`alert--${notice.type}`" role="status">
        {{ notice.text }}
      </div>

      <form class="settings" novalidate @submit.prevent="save">
        <fieldset class="panel settings__section" :disabled="!canEdit()">
          <legend>Marca</legend>
          <div class="form-grid">
            <div class="field">
              <label for="cfg-marca">Nombre de la marca</label>
              <input id="cfg-marca" v-model="form.brand_name" class="input" type="text" maxlength="120" />
              <span v-if="fieldErrors.brand_name" class="error">{{ fieldErrors.brand_name }}</span>
            </div>
            <div class="field">
              <label for="cfg-descriptor">Descriptor</label>
              <input
                id="cfg-descriptor"
                v-model="form.brand_descriptor"
                class="input"
                type="text"
                maxlength="60"
              />
              <span class="hint">Texto chico que acompaña al logotipo.</span>
            </div>
            <div class="field field--full">
              <label for="cfg-tagline">Frase institucional</label>
              <input id="cfg-tagline" v-model="form.tagline" class="input" type="text" maxlength="200" />
            </div>
            <div class="field field--full">
              <label for="cfg-institucional">Texto institucional</label>
              <textarea
                id="cfg-institucional"
                v-model="form.institutional_text"
                class="textarea"
                rows="4"
                maxlength="2000"
              />
            </div>
            <div class="field field--full">
              <label for="cfg-nota-pie">Nota al pie (pie del sitio)</label>
              <input id="cfg-nota-pie" v-model="form.footer_note" class="input" type="text" maxlength="400" />
            </div>
          </div>
        </fieldset>

        <fieldset class="panel settings__section" :disabled="!canEdit()">
          <legend>Contacto</legend>
          <div class="form-grid">
            <div class="field">
              <label for="cfg-telefono">Teléfono</label>
              <input id="cfg-telefono" v-model="form.phone" class="input" type="text" maxlength="40" />
            </div>
            <div class="field">
              <label for="cfg-whatsapp">WhatsApp (sólo dígitos)</label>
              <input
                id="cfg-whatsapp"
                v-model="form.whatsapp"
                class="input numeric"
                type="text"
                inputmode="numeric"
                maxlength="40"
                placeholder="5491155550000"
              />
              <span class="hint">Formato internacional sin + ni espacios.</span>
            </div>
            <div class="field">
              <label for="cfg-email">Correo</label>
              <input id="cfg-email" v-model="form.email" class="input" type="email" />
              <span v-if="fieldErrors.email" class="error">{{ fieldErrors.email }}</span>
            </div>
            <div class="field">
              <label for="cfg-horarios">Horarios</label>
              <input
                id="cfg-horarios"
                v-model="form.office_hours"
                class="input"
                type="text"
                maxlength="120"
                placeholder="Lunes a viernes de 9 a 18 hs"
              />
            </div>
            <div class="field">
              <label for="cfg-direccion">Dirección</label>
              <input id="cfg-direccion" v-model="form.address_line" class="input" type="text" maxlength="180" />
            </div>
            <div class="field">
              <label for="cfg-ciudad">Ciudad</label>
              <input id="cfg-ciudad" v-model="form.city" class="input" type="text" maxlength="120" />
            </div>
            <div class="field">
              <label for="cfg-instagram">Instagram</label>
              <input id="cfg-instagram" v-model="form.instagram" class="input" type="url" placeholder="https://instagram.com/…" />
            </div>
            <div class="field">
              <label for="cfg-facebook">Facebook</label>
              <input id="cfg-facebook" v-model="form.facebook" class="input" type="url" placeholder="https://facebook.com/…" />
            </div>
            <div class="field">
              <label for="cfg-linkedin">LinkedIn</label>
              <input id="cfg-linkedin" v-model="form.linkedin" class="input" type="url" placeholder="https://linkedin.com/…" />
            </div>
          </div>

          <label class="checkbox">
            <input v-model="form.whatsapp_is_demo" type="checkbox" />
            Marcar el número de WhatsApp como demostración (muestra el aviso en el sitio)
          </label>
        </fieldset>

        <fieldset class="panel settings__section" :disabled="!canEdit()">
          <legend>Comportamiento del catálogo</legend>
          <div class="form-grid">
            <div class="field">
              <label for="cfg-moneda">Moneda por defecto</label>
              <select id="cfg-moneda" v-model="form.default_currency" class="select">
                <option value="USD">USD</option>
                <option value="ARS">ARS</option>
                <option value="EUR">EUR</option>
              </select>
            </div>
          </div>
          <label class="checkbox">
            <input v-model="form.show_expenses" type="checkbox" />
            Mostrar expensas en las fichas públicas
          </label>
        </fieldset>

        <div class="settings__save">
          <button v-if="canEdit()" class="btn btn--primary" type="submit" :disabled="saving">
            {{ saving ? "Guardando…" : "Guardar cambios" }}
          </button>
          <span class="small muted">
            El crédito "Sitio demo desarrollado por ALMATE · Digital Studio" no es editable.
          </span>
        </div>
      </form>
    </template>
  </div>
</template>

<style scoped>
.admin-head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.admin-head h1 {
  font-size: var(--text-xl);
}

.settings {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.settings__section {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.settings__save {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
}
</style>
