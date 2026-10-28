<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import AppHeader from "./components/AppHeader.vue";
import AppFooter from "./components/AppFooter.vue";
import { useSettingsStore } from "./stores/settings";

const route = useRoute();
const settingsStore = useSettingsStore();

const isAdmin = computed(() => String(route.path).startsWith("/admin"));

onMounted(() => {
  void settingsStore.loadSettings();
});
</script>

<template>
  <a class="skip-link" href="#contenido">Saltar al contenido principal</a>

  <div class="app-shell" :class="{ 'app-shell--admin': isAdmin }">
    <AppHeader v-if="!isAdmin" />
    <main id="contenido" class="app-main">
      <RouterView />
    </main>
    <AppFooter v-if="!isAdmin" />
  </div>
</template>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-main {
  flex: 1;
}
</style>
