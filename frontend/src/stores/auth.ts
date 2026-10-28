/** Sesión del panel administrativo (JWT en localStorage). */

import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { api, getToken, getStoredUser, setSession } from "../api/client";
import type { AuthUser, LoginResponse } from "../api/types";

export const useAuthStore = defineStore("auth", () => {
  const token = ref<string | null>(getToken());
  const user = ref<AuthUser | null>(getStoredUser<AuthUser>());
  const loading = ref(false);
  const error = ref<string | null>(null);

  const isAuthenticated = computed(() => Boolean(token.value));
  const isAdmin = computed(() => user.value?.role === "admin");

  async function login(email: string, password: string): Promise<boolean> {
    loading.value = true;
    error.value = null;
    try {
      const response = await api.post<LoginResponse>("/auth/login", { email, password });
      token.value = response.access_token;
      user.value = response.user;
      setSession(response.access_token, JSON.stringify(response.user));
      return true;
    } catch (caught) {
      error.value =
        caught instanceof Error ? caught.message : "No pudimos iniciar sesión. Reintentá.";
      return false;
    } finally {
      loading.value = false;
    }
  }

  /** Revalida el token guardado contra el servidor (arranque de la sesión). */
  async function refresh(): Promise<void> {
    if (!token.value) return;
    try {
      user.value = await api.get<AuthUser>("/auth/me", { auth: true });
      setSession(token.value, JSON.stringify(user.value));
    } catch {
      logout();
    }
  }

  function logout(): void {
    token.value = null;
    user.value = null;
    setSession(null, null);
  }

  return { token, user, loading, error, isAuthenticated, isAdmin, login, logout, refresh };
});
