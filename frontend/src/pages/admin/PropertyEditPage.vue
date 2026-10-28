<script setup lang="ts">
/**
 * Alta y edición de propiedades: formulario por secciones + gestor de fotos
 * (subida con previsualización, principal, orden, alt y borrado).
 */
import { computed, onMounted, reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ApiError, api } from "../../api/client";
import type { PropertyAdmin, PropertyImageAdmin, PropertyPayload } from "../../api/types";
import { useAuthStore } from "../../stores/auth";
import LoadingBlock from "../../components/LoadingBlock.vue";
import ErrorState from "../../components/ErrorState.vue";
import StatusBadge from "../../components/StatusBadge.vue";

interface UploadLimits {
  max_upload_mb: number;
  max_images_per_property: number;
  allowed_types: string[];
}

/**
 * Formulario: igual que `PropertyPayload` pero los campos editables mientras
 * el usuario escribe son cadenas (se convierten al guardar).
 */
type EditorForm = Omit<
  PropertyPayload,
  | "rooms"
  | "bedrooms"
  | "bathrooms"
  | "toilets"
  | "garages"
  | "antiquity_years"
  | "price"
  | "expenses"
  | "department"
  | "locality"
  | "neighborhood"
  | "address"
> & {
  rooms: number | string | null;
  bedrooms: number | string | null;
  bathrooms: number | string | null;
  toilets: number | string | null;
  garages: number | string | null;
  antiquity_years: number | string | null;
  price: string;
  expenses: string;
  department: string;
  locality: string;
  neighborhood: string;
  address: string;
};

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

const isNew = computed(() => route.name === "admin-property-new");
const identifier = computed(() => String(route.params.id ?? ""));

const loading = ref(!isNew.value);
const saving = ref(false);
const error = ref<string | null>(null);
const serverErrors = ref<Record<string, string>>({});
const notice = ref<{ type: "success" | "error"; text: string } | null>(null);

const property = ref<PropertyAdmin | null>(null);
const limits = ref<UploadLimits | null>(null);

const SERVICES_SUGGEST = [
  "Agua caliente",
  "Agua fría",
  "Gas natural",
  "Closets",
  "Parrilla",
  "Pileta",
  "Aire acondicionado",
  "Calefacción",
  "Seguridad 24hs",
  "Ascensor",
];

const form = reactive<EditorForm>({
  title: "",
  description: "",
  operation: "buy",
  property_type: "apartment",
  is_development: false,
  price: "",
  currency: "USD",
  price_unit: null,
  expenses: "",
  commercial_status: "available",
  publication_status: "draft",
  is_featured: false,
  country: "Argentina",
  province: "Buenos Aires",
  department: "",
  locality: "",
  neighborhood: "",
  address: "",
  address_is_public: true,
  rooms: null,
  bedrooms: null,
  bathrooms: null,
  toilets: null,
  garages: null,
  antiquity_years: null,
  surface_covered: null,
  surface_semicovered: null,
  surface_total: null,
  apto_professional: false,
  services: [],
});

const servicesText = ref("");
const newService = ref("");

// --- imágenes --------------------------------------------------------------
const images = ref<PropertyImageAdmin[]>([]);
const uploading = ref(false);
const uploadError = ref<string | null>(null);
const previews = ref<{ file: File; url: string }[]>([]);

function numeric(value: string | number | null): number | null {
  if (value === null || value === "") return null;
  const parsed = typeof value === "number" ? value : Number(String(value).replace(",", "."));
  return Number.isFinite(parsed) ? parsed : null;
}

function applyProperty(data: PropertyAdmin) {
  property.value = data;
  images.value = data.images;

  Object.assign(form, {
    title: data.title,
    description: data.description,
    operation: data.operation,
    property_type: data.property_type,
    is_development: data.is_development,
    price: data.price ?? "",
    currency: data.currency,
    price_unit: data.price_unit,
    expenses: data.expenses ?? "",
    commercial_status: data.commercial_status,
    publication_status: data.publication_status,
    is_featured: data.is_featured,
    country: data.country,
    province: data.province,
    department: data.department ?? "",
    locality: data.locality ?? "",
    neighborhood: data.neighborhood ?? "",
    address: data.address ?? "",
    address_is_public: data.address_is_public,
    rooms: data.rooms,
    bedrooms: data.bedrooms,
    bathrooms: data.bathrooms,
    toilets: data.toilets,
    garages: data.garages,
    antiquity_years: data.antiquity_years,
    surface_covered: data.surface_covered,
    surface_semicovered: data.surface_semicovered,
    surface_total: data.surface_total,
    apto_professional: data.apto_professional,
    services: [...data.services],
  });
  servicesText.value = data.services.join(", ");
}

async function load() {
  if (isNew.value) return;
  loading.value = true;
  error.value = null;
  try {
    applyProperty(await api.get<PropertyAdmin>(`/admin/properties/${identifier.value}`, { auth: true }));
  } catch (caught) {
    error.value =
      caught instanceof ApiError ? caught.message : "No pudimos cargar la propiedad.";
  } finally {
    loading.value = false;
  }
}

function buildPayload(): PropertyPayload {
  const services = servicesText.value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);

  return {
    title: form.title.trim(),
    description: form.description.trim(),
    operation: form.operation,
    property_type: form.property_type,
    is_development: form.is_development,
    price: form.price === "" ? null : String(form.price).trim(),
    currency: form.currency,
    price_unit: form.price_unit,
    expenses: form.expenses === "" ? null : String(form.expenses).trim(),
    commercial_status: form.commercial_status,
    publication_status: form.publication_status,
    is_featured: form.is_featured,
    country: form.country.trim() || "Argentina",
    province: form.province.trim() || "Buenos Aires",
    department: form.department.trim() || null,
    locality: form.locality.trim() || null,
    neighborhood: form.neighborhood.trim() || null,
    address: form.address.trim() || null,
    address_is_public: form.address_is_public,
    rooms: numeric(form.rooms),
    bedrooms: numeric(form.bedrooms),
    bathrooms: numeric(form.bathrooms),
    toilets: numeric(form.toilets),
    garages: numeric(form.garages),
    antiquity_years: numeric(form.antiquity_years),
    surface_covered: numeric(form.surface_covered) === null ? null : String(form.surface_covered),
    surface_semicovered:
      numeric(form.surface_semicovered) === null ? null : String(form.surface_semicovered),
    surface_total: numeric(form.surface_total) === null ? null : String(form.surface_total),
    apto_professional: form.apto_professional,
    services,
  };
}

function validate(): boolean {
  serverErrors.value = {};
  const errors: Record<string, string> = {};

  if (form.title.trim().length < 5) errors.title = "El título debe tener al menos 5 caracteres.";
  if (!form.operation) errors.operation = "Elegí la operación.";
  if (!form.property_type) errors.property_type = "Elegí el tipo de propiedad.";
  if (form.price !== "" && Number(form.price) < 0) errors.price = "El precio no puede ser negativo.";
  if (!form.locality.trim()) errors.locality = "Indicá la localidad.";

  serverErrors.value = errors;
  return Object.keys(errors).length === 0;
}

async function save() {
  notice.value = null;
  if (!validate()) {
    notice.value = { type: "error", text: "Revisá los campos marcados antes de guardar." };
    return;
  }

  saving.value = true;
  try {
    const payload = buildPayload();
    if (isNew.value) {
      const created = await api.post<PropertyAdmin>("/admin/properties", payload, { auth: true });
      notice.value = {
        type: "success",
        text: `Ficha creada con el código ${created.code}. Ya podés agregar fotografías.`,
      };
      applyProperty(created);
      await router.replace({
        name: "admin-property-edit",
        params: { id: created.code },
      });
    } else {
      const updated = await api.patch<PropertyAdmin>(
        `/admin/properties/${identifier.value}`,
        payload,
        { auth: true },
      );
      applyProperty(updated);
      notice.value = { type: "success", text: "Cambios guardados." };
    }
  } catch (caught) {
    if (caught instanceof ApiError) {
      const fieldErrors: Record<string, string> = {};
      for (const item of caught.errors) {
        const field = item.loc[item.loc.length - 1];
        if (field && !fieldErrors[field]) fieldErrors[field] = item.msg;
      }
      serverErrors.value = fieldErrors;
      notice.value = { type: "error", text: caught.message };
    } else {
      notice.value = { type: "error", text: "No pudimos guardar la propiedad." };
    }
  } finally {
    saving.value = false;
  }
}

// --- fotografías -----------------------------------------------------------
/** Elimina la ficha y sus fotografías (sólo rol admin, lo exige el backend). */
async function removeProperty() {
  if (!property.value) return;
  const confirmed = window.confirm(
    `¿Eliminar "${property.value.title}"? Se borran la ficha y sus fotografías. Esta acción no se puede deshacer.`,
  );
  if (!confirmed) return;

  saving.value = true;
  try {
    await api.delete(`/admin/properties/${property.value.code}`, { auth: true });
    await router.replace({ name: "admin-properties" });
  } catch (caught) {
    notice.value = {
      type: "error",
      text: caught instanceof ApiError ? caught.message : "No pudimos eliminar la propiedad.",
    };
    saving.value = false;
  }
}

function onFilesSelected(event: Event) {
  const input = event.target as HTMLInputElement;
  const files = Array.from(input.files ?? []);
  uploadError.value = null;

  const maxMb = limits.value?.max_upload_mb ?? 8;
  const accepted = files.filter((file) => {
    if (file.size > maxMb * 1024 * 1024) {
      uploadError.value = `"${file.name}" supera los ${maxMb} MB.`;
      return false;
    }
    return true;
  });

  previews.value = accepted.map((file) => ({ file, url: URL.createObjectURL(file) }));
  input.value = "";
}

function discardPreviews() {
  previews.value.forEach((item) => URL.revokeObjectURL(item.url));
  previews.value = [];
}

async function uploadImages() {
  if (!previews.value.length || !property.value) return;

  uploading.value = true;
  uploadError.value = null;
  try {
    const data = new FormData();
    previews.value.forEach((item) => data.append("files", item.file));
    const updated = await api.post<PropertyImageAdmin[]>(
      `/admin/properties/${property.value.code}/images`,
      data,
      { auth: true },
    );
    images.value = updated;
    discardPreviews();
    notice.value = { type: "success", text: "Fotografías subidas correctamente." };
  } catch (caught) {
    uploadError.value =
      caught instanceof ApiError ? caught.message : "No pudimos subir las imágenes.";
  } finally {
    uploading.value = false;
  }
}

async function patchImage(imageId: number, payload: Record<string, unknown>) {
  if (!property.value) return;
  try {
    images.value = await api.patch<PropertyImageAdmin[]>(
      `/admin/properties/${property.value.code}/images/${imageId}`,
      payload,
      { auth: true },
    );
  } catch (caught) {
    notice.value = {
      type: "error",
      text: caught instanceof ApiError ? caught.message : "No pudimos actualizar la imagen.",
    };
  }
}

async function removeImage(image: PropertyImageAdmin) {
  if (!property.value) return;
  const confirmed = window.confirm("¿Eliminar esta fotografía? El archivo también se borra.");
  if (!confirmed) return;

  try {
    images.value = await api.delete<PropertyImageAdmin[]>(
      `/admin/properties/${property.value.code}/images/${image.id}`,
      { auth: true },
    );
    notice.value = { type: "success", text: "Fotografía eliminada." };
  } catch (caught) {
    notice.value = {
      type: "error",
      text: caught instanceof ApiError ? caught.message : "No pudimos eliminar la imagen.",
    };
  }
}

async function moveImage(index: number, direction: -1 | 1) {
  if (!property.value) return;
  const target = index + direction;
  if (target < 0 || target >= images.value.length) return;

  const ordered = [...images.value];
  const [moved] = ordered.splice(index, 1);
  ordered.splice(target, 0, moved);

  try {
    images.value = await api.post<PropertyImageAdmin[]>(
      `/admin/properties/${property.value.code}/images/reorder`,
      { ids: ordered.map((item) => item.id) },
      { auth: true },
    );
  } catch (caught) {
    notice.value = {
      type: "error",
      text: caught instanceof ApiError ? caught.message : "No pudimos reordenar las imágenes.",
    };
  }
}

async function toggleMain(image: PropertyImageAdmin) {
  if (image.is_main) return;
  await patchImage(image.id, { is_main: true });
}

function addService() {
  const value = newService.value.trim();
  if (!value) return;
  const current = servicesText.value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  if (!current.includes(value)) current.push(value);
  servicesText.value = current.join(", ");
  newService.value = "";
}

function addSuggested(suggestion: string) {
  newService.value = suggestion;
  addService();
}

/** Guarda el texto alternativo cuando termina de editarlo el usuario. */
function onAltChange(imageId: number, event: Event) {
  const input = event.target as HTMLInputElement;
  void patchImage(imageId, { alt_text: input.value });
}

function fieldError(field: string): string | undefined {
  return serverErrors.value[field];
}

onMounted(() => {
  void load();
  api
    .get<UploadLimits>("/admin/uploads-limit", { auth: true })
    .then((data) => {
      limits.value = data;
    })
    .catch(() => undefined);
});
</script>

<template>
  <div>
    <div class="admin-head">
      <div>
        <RouterLink class="link-btn" to="/admin/propiedades">← Volver al listado</RouterLink>
        <h1>{{ isNew ? "Nueva propiedad" : property?.title ?? "Editar propiedad" }}</h1>
        <p v-if="property" class="row">
          <span class="small muted">Cód. {{ property.code }}</span>
          <StatusBadge
            :commercial="property.commercial_status"
            :publication="property.publication_status"
            :featured="property.is_featured"
            :development="property.is_development"
          />
        </p>
      </div>
      <div class="row">
        <button
          v-if="!isNew && property && auth.isAdmin"
          class="btn btn--danger"
          type="button"
          :disabled="saving"
          @click="removeProperty"
        >
          Eliminar
        </button>
        <button class="btn btn--primary" type="button" :disabled="saving" @click="save">
          {{ saving ? "Guardando…" : isNew ? "Crear propiedad" : "Guardar cambios" }}
        </button>
      </div>
    </div>

    <LoadingBlock v-if="loading" label="Cargando la ficha…" />
    <ErrorState v-else-if="error" :message="error" @retry="load" />

    <template v-else>
      <div v-if="notice" class="alert" :class="`alert--${notice.type}`" role="status">
        {{ notice.text }}
      </div>

      <form class="editor" novalidate @submit.prevent="save">
        <!-- Identificación -->
        <fieldset class="panel editor__section">
          <legend>Identificación</legend>

          <div class="form-grid form-grid--full">
            <div class="field field--full">
              <label for="prop-titulo">Título *</label>
              <input
                id="prop-titulo"
                v-model="form.title"
                class="input"
                type="text"
                maxlength="180"
                placeholder="Departamento con balcón al parque"
                :aria-invalid="Boolean(fieldError('title'))"
              />
              <span v-if="fieldError('title')" class="error">{{ fieldError("title") }}</span>
            </div>

            <div class="field">
              <label for="prop-operacion">Operación *</label>
              <select id="prop-operacion" v-model="form.operation" class="select">
                <option value="buy">Venta</option>
                <option value="rent">Alquiler</option>
                <option value="temporary_rent">Alquiler temporal</option>
              </select>
            </div>

            <div class="field">
              <label for="prop-tipo">Tipo de propiedad *</label>
              <select id="prop-tipo" v-model="form.property_type" class="select">
                <option value="apartment">Departamento</option>
                <option value="house">Casa</option>
                <option value="ph">PH</option>
                <option value="land">Terreno</option>
                <option value="commercial">Local comercial</option>
                <option value="office">Oficina</option>
                <option value="garage">Cochera</option>
              </select>
            </div>

            <div class="field">
              <label for="prop-publicacion">Publicación</label>
              <select id="prop-publicacion" v-model="form.publication_status" class="select">
                <option value="draft">Borrador (no visible)</option>
                <option value="published">Publicada</option>
                <option value="archived">Archivada</option>
              </select>
            </div>

            <div class="field">
              <label for="prop-comercial">Estado comercial</label>
              <select id="prop-comercial" v-model="form.commercial_status" class="select">
                <option value="available">Disponible</option>
                <option value="reserved">Reservada</option>
                <option value="sold">Vendida</option>
                <option value="rented">Alquilada</option>
              </select>
            </div>

            <div class="field field--full">
              <label class="checkbox">
                <input v-model="form.is_featured" type="checkbox" />
                Marcar como destacada (aparece en el inicio)
              </label>
              <label class="checkbox">
                <input v-model="form.is_development" type="checkbox" />
                Es un emprendimiento
              </label>
            </div>
          </div>
        </fieldset>

        <!-- Precio -->
        <fieldset class="panel editor__section">
          <legend>Precio y gastos</legend>

          <div class="form-grid">
            <div class="field">
              <label for="prop-precio">Precio</label>
              <input
                id="prop-precio"
                v-model="form.price"
                class="input numeric"
                type="text"
                inputmode="decimal"
                placeholder="152000.50"
                :aria-invalid="Boolean(fieldError('price'))"
              />
              <span v-if="fieldError('price')" class="error">{{ fieldError("price") }}</span>
              <span class="hint">Dejalo vacío para "Consultar precio".</span>
            </div>

            <div class="field">
              <label for="prop-moneda">Moneda</label>
              <select id="prop-moneda" v-model="form.currency" class="select">
                <option value="USD">USD</option>
                <option value="ARS">ARS</option>
                <option value="EUR">EUR</option>
              </select>
            </div>

            <div class="field">
              <label for="prop-unidad">Unidad del precio</label>
              <select id="prop-unidad" v-model="form.price_unit" class="select">
                <option :value="null">Automática (según operación)</option>
                <option value="total">Precio total</option>
                <option value="monthly">Por mes</option>
                <option value="daily">Por noche</option>
              </select>
            </div>

            <div class="field">
              <label for="prop-expensas">Expensas</label>
              <input
                id="prop-expensas"
                v-model="form.expenses"
                class="input numeric"
                type="text"
                inputmode="decimal"
                placeholder="35000"
              />
              <span class="hint">En la misma moneda, valor por mes.</span>
            </div>
          </div>
        </fieldset>

        <!-- Ubicación -->
        <fieldset class="panel editor__section">
          <legend>Ubicación</legend>

          <div class="form-grid form-grid--full">
            <div class="field">
              <label for="prop-pais">País</label>
              <input id="prop-pais" v-model="form.country" class="input" type="text" />
            </div>
            <div class="field">
              <label for="prop-provincia">Provincia</label>
              <input id="prop-provincia" v-model="form.province" class="input" type="text" />
            </div>
            <div class="field">
              <label for="prop-departamento">Departamento</label>
              <input id="prop-departamento" v-model="form.department" class="input" type="text" />
            </div>
            <div class="field">
              <label for="prop-localidad">Localidad *</label>
              <input
                id="prop-localidad"
                v-model="form.locality"
                class="input"
                type="text"
                placeholder="Quilmes"
                :aria-invalid="Boolean(fieldError('locality'))"
              />
              <span v-if="fieldError('locality')" class="error">{{ fieldError("locality") }}</span>
            </div>
            <div class="field">
              <label for="prop-barrio">Barrio</label>
              <input id="prop-barrio" v-model="form.neighborhood" class="input" type="text" />
            </div>
            <div class="field">
              <label for="prop-direccion">Dirección</label>
              <input
                id="prop-direccion"
                v-model="form.address"
                class="input"
                type="text"
                placeholder="Calle y número"
              />
            </div>
            <div class="field field--full">
              <label class="checkbox">
                <input v-model="form.address_is_public" type="checkbox" />
                Mostrar la dirección exacta en el sitio público
              </label>
              <span class="hint">
                Si se desmarca, sólo se publican barrio y localidad (privacidad del propietario).
              </span>
            </div>
          </div>
        </fieldset>

        <!-- Superficies y ambientes -->
        <fieldset class="panel editor__section">
          <legend>Superficies y ambientes</legend>

          <div class="form-grid">
            <div class="field">
              <label for="prop-ambientes">Ambientes</label>
              <input id="prop-ambientes" v-model="form.rooms" class="input numeric" type="number" min="0" max="50" />
            </div>
            <div class="field">
              <label for="prop-dormitorios">Dormitorios</label>
              <input
                id="prop-dormitorios"
                v-model="form.bedrooms"
                class="input numeric"
                type="number"
                min="0"
                max="50"
              />
            </div>
            <div class="field">
              <label for="prop-banos">Baños</label>
              <input id="prop-banos" v-model="form.bathrooms" class="input numeric" type="number" min="0" max="50" />
            </div>
            <div class="field">
              <label for="prop-toilettes">Toilettes</label>
              <input id="prop-toilettes" v-model="form.toilets" class="input numeric" type="number" min="0" max="50" />
            </div>
            <div class="field">
              <label for="prop-cocheras">Cocheras</label>
              <input id="prop-cocheras" v-model="form.garages" class="input numeric" type="number" min="0" max="50" />
            </div>
            <div class="field">
              <label for="prop-antiguedad">Antigüedad (años)</label>
              <input
                id="prop-antiguedad"
                v-model="form.antiquity_years"
                class="input numeric"
                type="number"
                min="0"
                max="500"
              />
            </div>
            <div class="field">
              <label for="prop-sup-cubierta">Superficie cubierta (m²)</label>
              <input id="prop-sup-cubierta" v-model="form.surface_covered" class="input numeric" type="number" min="0" step="0.01" />
            </div>
            <div class="field">
              <label for="prop-sup-semi">Superficie semicubierta (m²)</label>
              <input
                id="prop-sup-semi"
                v-model="form.surface_semicovered"
                class="input numeric"
                type="number"
                min="0"
                step="0.01"
              />
            </div>
            <div class="field">
              <label for="prop-sup-total">Superficie total (m²)</label>
              <input id="prop-sup-total" v-model="form.surface_total" class="input numeric" type="number" min="0" step="0.01" />
            </div>
            <div class="field field--full">
              <label class="checkbox">
                <input v-model="form.apto_professional" type="checkbox" />
                Apto profesional
              </label>
            </div>
          </div>
        </fieldset>

        <!-- Descripción -->
        <fieldset class="panel editor__section">
          <legend>Descripción y servicios</legend>

          <div class="form-grid form-grid--full">
            <div class="field field--full">
              <label for="prop-descripcion">Descripción</label>
              <textarea
                id="prop-descripcion"
                v-model="form.description"
                class="textarea"
                rows="7"
                maxlength="10000"
                placeholder="Ambientes, luminosidad, expensas, cercanías…"
              />
              <span class="hint">{{ form.description.length }} / 10000 caracteres</span>
            </div>

            <div class="field field--full">
              <label for="prop-servicios">Servicios (separados por coma)</label>
              <input
                id="prop-servicios"
                v-model="servicesText"
                class="input"
                type="text"
                placeholder="Gas natural, Closets, Parrilla"
              />
              <div class="chip-row">
                <button
                  v-for="suggestion in SERVICES_SUGGEST"
                  :key="suggestion"
                  class="chip"
                  type="button"
                  @click="addSuggested(suggestion)"
                >
                  + {{ suggestion }}
                </button>
              </div>
            </div>
          </div>
        </fieldset>

        <div class="editor__save">
          <button class="btn btn--primary" type="submit" :disabled="saving">
            {{ saving ? "Guardando…" : isNew ? "Crear propiedad" : "Guardar cambios" }}
          </button>
          <span class="small muted">Los cambios quedan registrados en el panel.</span>
        </div>
      </form>

      <!-- Fotografías -->
      <section class="panel editor__section images-panel" aria-labelledby="fotos-titulo">
        <div class="row row--between">
          <div>
            <h2 id="fotos-titulo" class="editor__section-title">Fotografías</h2>
            <p class="small muted">
              <template v-if="limits">
                Hasta {{ limits.max_upload_mb }} MB por archivo ·
                {{ limits.max_images_per_property }} imágenes por propiedad ·
                {{ limits.allowed_types.join(", ") }}
              </template>
              <template v-else>JPG, PNG o WebP de buena calidad.</template>
            </p>
          </div>
          <span class="small muted numeric">{{ images.length }} cargadas</span>
        </div>

        <div v-if="isNew" class="alert alert--info">
          Guardá la ficha primero: las fotografías se asocian al código de la propiedad.
        </div>

        <template v-else>
          <div class="upload">
            <label class="upload__drop" for="fotos-input">
              <svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 16V5M8 9l4-4 4 4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" />
                <path d="M4 15v3.5h16V15" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
              </svg>
              <span>Arrastrá o seleccioná imágenes</span>
              <input id="fotos-input" type="file" accept="image/*" multiple @change="onFilesSelected" />
            </label>

            <div v-if="previews.length" class="upload__previews">
              <figure v-for="item in previews" :key="item.url" class="upload__preview">
                <img :src="item.url" :alt="`Vista previa de ${item.file.name}`" />
                <figcaption class="small">{{ item.file.name }}</figcaption>
              </figure>
              <div class="upload__preview-actions">
                <button class="btn btn--bronze btn--sm" type="button" :disabled="uploading" @click="uploadImages">
                  {{ uploading ? "Subiendo…" : `Subir ${previews.length} imagen(es)` }}
                </button>
                <button class="btn btn--ghost btn--sm" type="button" :disabled="uploading" @click="discardPreviews">
                  Descartar
                </button>
              </div>
            </div>
          </div>

          <div v-if="uploadError" class="alert alert--error" role="alert">{{ uploadError }}</div>

          <p v-if="!images.length" class="muted small">
            Todavía no hay fotografías en esta propiedad.
          </p>

          <ul v-else class="image-grid">
            <li v-for="(image, index) in images" :key="image.id" class="image-card">
              <img class="image-card__photo" :src="image.url" :alt="image.alt || image.filename" />
              <div class="image-card__body">
                <div class="row row--between">
                  <span class="small muted numeric">#{{ index + 1 }}</span>
                  <button
                    v-if="!image.is_main"
                    class="link-btn"
                    type="button"
                    @click="toggleMain(image)"
                  >
                    Marcar principal
                  </button>
                  <span v-else class="badge badge--bronze">Principal</span>
                </div>

                <label class="sr-only" :for="`alt-${image.id}`">Texto alternativo</label>
                <input
                  :id="`alt-${image.id}`"
                  class="input input--sm"
                  type="text"
                  maxlength="200"
                  :value="image.alt"
                  placeholder="Descripción para accesibilidad"
                  @change="onAltChange(image.id, $event)"
                />

                <div class="row image-card__actions">
                  <button
                    class="btn btn--ghost btn--sm"
                    type="button"
                    :disabled="index === 0"
                    title="Mover a la izquierda"
                    @click="moveImage(index, -1)"
                  >
                    ←
                  </button>
                  <button
                    class="btn btn--ghost btn--sm"
                    type="button"
                    :disabled="index === images.length - 1"
                    title="Mover a la derecha"
                    @click="moveImage(index, 1)"
                  >
                    →
                  </button>
                  <button class="btn btn--danger btn--sm" type="button" @click="removeImage(image)">
                    Eliminar
                  </button>
                </div>
              </div>
            </li>
          </ul>
        </template>
      </section>
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
  margin-top: var(--space-2);
  font-size: var(--text-xl);
}

.editor {
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}

.editor__section {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.editor__section-title {
  font-family: var(--font-ui);
  font-size: var(--text-md);
  font-weight: 600;
}

.editor__save {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--space-3);
}

.images-panel {
  margin-top: var(--space-5);
}

.chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-2);
}

.chip {
  padding: 0.25rem 0.7rem;
  border: 1px dashed var(--color-line-strong);
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  color: var(--color-stone-dark);
}

.chip:hover {
  border-color: var(--color-bronze);
  color: var(--color-bronze-dark);
}

.upload__drop {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-5);
  border: 2px dashed var(--color-line-strong);
  border-radius: var(--radius-md);
  color: var(--color-stone-dark);
  font-size: var(--text-sm);
  cursor: pointer;
  text-align: center;
}

.upload__drop:hover {
  border-color: var(--color-bronze);
  color: var(--color-bronze-dark);
}

.upload__drop input {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.upload__previews {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  margin-top: var(--space-4);
}

.upload__preview {
  width: 140px;
}

.upload__preview img {
  width: 140px;
  height: 100px;
  object-fit: cover;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-line);
}

.upload__preview figcaption {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.upload__preview-actions {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  width: 160px;
}

.image-grid {
  display: grid;
  gap: var(--space-4);
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 250px), 1fr));
  padding: 0;
  margin: var(--space-4) 0 0;
  list-style: none;
}

.image-card {
  overflow: hidden;
  background: var(--color-surface);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
}

.image-card__photo {
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
  background: var(--color-bg-alt);
}

.image-card__body {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-3);
}

.input--sm {
  min-height: 38px;
  padding: 0.4rem 0.6rem;
  font-size: var(--text-sm);
}

.image-card__actions {
  gap: var(--space-2);
}
</style>
