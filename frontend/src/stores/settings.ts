/** Configuración pública del negocio y metadatos de los filtros. */

import { defineStore } from "pinia";
import { ref } from "vue";
import { api } from "../api/client";
import type { CatalogMeta, PublicSettings } from "../api/types";

export const useSettingsStore = defineStore("settings", () => {
  const settings = ref<PublicSettings | null>(null);
  const meta = ref<CatalogMeta | null>(null);
  const settingsError = ref<string | null>(null);
  const metaError = ref<string | null>(null);
  let settingsPromise: Promise<void> | null = null;
  let metaPromise: Promise<void> | null = null;

  async function loadSettings(force = false): Promise<void> {
    if (settings.value && !force) return;
    if (settingsPromise && !force) return settingsPromise;
    settingsPromise = api
      .get<PublicSettings>("/settings")
      .then((data) => {
        settings.value = data;
        settingsError.value = null;
      })
      .catch((error: unknown) => {
        settingsError.value =
          error instanceof Error ? error.message : "No pudimos cargar la configuración.";
      })
      .finally(() => {
        settingsPromise = null;
      });
    return settingsPromise;
  }

  async function loadMeta(force = false): Promise<void> {
    if (meta.value && !force) return;
    if (metaPromise && !force) return metaPromise;
    metaPromise = api
      .get<CatalogMeta>("/meta")
      .then((data) => {
        meta.value = data;
        metaError.value = null;
      })
      .catch((error: unknown) => {
        metaError.value =
          error instanceof Error ? error.message : "No pudimos cargar las opciones de filtros.";
      })
      .finally(() => {
        metaPromise = null;
      });
    return metaPromise;
  }

  return { settings, meta, settingsError, metaError, loadSettings, loadMeta };
});
