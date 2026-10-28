/** Catálogo de favoritos guardado en el navegador (no se sincroniza con la cuenta). */

import { defineStore } from "pinia";
import { ref } from "vue";

const STORAGE_KEY = "almate.favoritos";

function load(): string[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? (JSON.parse(raw) as unknown) : [];
    return Array.isArray(parsed) ? parsed.filter((item): item is string => typeof item === "string") : [];
  } catch {
    return [];
  }
}

export const useFavoritesStore = defineStore("favorites", () => {
  const codes = ref<string[]>(load());

  function persist() {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(codes.value));
  }

  function has(code: string): boolean {
    return codes.value.includes(code);
  }

  function toggle(code: string): boolean {
    if (has(code)) {
      codes.value = codes.value.filter((item) => item !== code);
      persist();
      return false;
    }
    codes.value = [...codes.value, code];
    persist();
    return true;
  }

  function clear() {
    codes.value = [];
    persist();
  }

  return { codes, has, toggle, clear };
});
