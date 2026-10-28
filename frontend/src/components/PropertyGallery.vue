<script setup lang="ts">
/**
 * Galería de la ficha: imagen principal, miniaturas, teclado y visor ampliado.
 */
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import type { PropertyImage } from "../api/types";

const props = defineProps<{ images: PropertyImage[]; title: string }>();

const current = ref(0);
const lightbox = ref(false);

const active = computed<PropertyImage | null>(() => props.images[current.value] ?? null);

watch(
  () => props.images,
  () => {
    current.value = 0;
  },
);

function select(index: number) {
  if (index < 0 || index >= props.images.length) return;
  current.value = index;
}

function previous() {
  select((current.value - 1 + props.images.length) % props.images.length);
}

function next() {
  select((current.value + 1) % props.images.length);
}

function onKeydown(event: KeyboardEvent) {
  if (!props.images.length) return;
  if (event.key === "ArrowLeft") previous();
  if (event.key === "ArrowRight") next();
  if (event.key === "Escape") lightbox.value = false;
}

onMounted(() => window.addEventListener("keydown", onKeydown));
onUnmounted(() => window.removeEventListener("keydown", onKeydown));

function altFor(image: PropertyImage, index: number): string {
  return image.alt || `${props.title}, fotografía ${index + 1}`;
}
</script>

<template>
  <div class="gallery">
    <div class="gallery__main">
      <button
        class="gallery__frame"
        type="button"
        :disabled="!active"
        aria-label="Ampliar fotografía"
        @click="lightbox = true"
      >
        <img
          v-if="active"
          :src="active.url"
          :alt="altFor(active, current)"
          decoding="async"
        />
        <div v-else class="gallery__empty" role="img" :aria-label="`Sin fotografías de ${title}`">
          <span>Esta propiedad todavía no tiene fotografías publicadas</span>
        </div>
      </button>

      <div v-if="images.length > 1" class="gallery__controls">
        <button type="button" class="gallery__arrow" @click="previous">
          <span class="sr-only">Fotografía anterior</span>
          <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" stroke-width="1.8" />
          </svg>
        </button>
        <span class="gallery__counter numeric">{{ current + 1 }} / {{ images.length }}</span>
        <button type="button" class="gallery__arrow" @click="next">
          <span class="sr-only">Fotografía siguiente</span>
          <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="1.8" />
          </svg>
        </button>
      </div>
    </div>

    <div v-if="images.length > 1" class="gallery__thumbs" role="tablist" aria-label="Fotografías">
      <button
        v-for="(image, index) in images"
        :key="image.id"
        type="button"
        role="tab"
        class="gallery__thumb"
        :class="{ 'gallery__thumb--active': index === current }"
        :aria-selected="index === current"
        @click="select(index)"
      >
        <img :src="image.url" :alt="altFor(image, index)" loading="lazy" decoding="async" />
      </button>
    </div>

    <Teleport to="body">
      <div
        v-if="lightbox && active"
        class="lightbox"
        role="dialog"
        aria-modal="true"
        :aria-label="`Fotografía ampliada de ${title}`"
        @click.self="lightbox = false"
      >
        <button type="button" class="lightbox__close" @click="lightbox = false">
          <span class="sr-only">Cerrar visor</span>
          <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="1.8" />
          </svg>
        </button>

        <button v-if="images.length > 1" type="button" class="lightbox__arrow lightbox__arrow--left" @click="previous">
          <span class="sr-only">Anterior</span>
          <svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" stroke-width="1.8" />
          </svg>
        </button>

        <img class="lightbox__image" :src="active.url" :alt="altFor(active, current)" />

        <button v-if="images.length > 1" type="button" class="lightbox__arrow lightbox__arrow--right" @click="next">
          <span class="sr-only">Siguiente</span>
          <svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="1.8" />
          </svg>
        </button>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
.gallery {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.gallery__main {
  position: relative;
}

.gallery__frame {
  display: block;
  width: 100%;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  background: var(--color-bg-alt);
  border-radius: var(--radius-lg);
  cursor: zoom-in;
}

.gallery__frame img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.gallery__empty {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  padding: var(--space-5);
  text-align: center;
  color: var(--color-stone-dark);
  font-size: var(--text-sm);
  background: repeating-linear-gradient(
    45deg,
    var(--color-bg-alt),
    var(--color-bg-alt) 12px,
    #e7e2d8 12px,
    #e7e2d8 24px
  );
}

.gallery__controls {
  position: absolute;
  right: var(--space-3);
  bottom: var(--space-3);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1);
  background: rgba(34, 35, 33, 0.84);
  border-radius: var(--radius-pill);
  color: #fff;
}

.gallery__arrow {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  color: #fff;
}

.gallery__arrow:hover {
  background: rgba(255, 255, 255, 0.16);
}

.gallery__counter {
  font-size: var(--text-xs);
  padding-inline: var(--space-2);
}

.gallery__thumbs {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(76px, 1fr));
  gap: var(--space-2);
}

.gallery__thumb {
  aspect-ratio: 4 / 3;
  overflow: hidden;
  border: 2px solid transparent;
  border-radius: var(--radius-sm);
  padding: 0;
}

.gallery__thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.gallery__thumb--active {
  border-color: var(--color-bronze);
}
</style>

<style>
/* Estilos globales del visor (Teleport a body). */
.lightbox {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: grid;
  place-items: center;
  padding: var(--space-5);
  background: rgba(18, 19, 18, 0.94);
}

.lightbox__image {
  max-width: min(100%, 1400px);
  max-height: 86vh;
  object-fit: contain;
  border-radius: var(--radius-md);
}

.lightbox__close {
  position: absolute;
  top: var(--space-4);
  right: var(--space-4);
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
}

.lightbox__arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  color: #fff;
  background: rgba(255, 255, 255, 0.12);
}

.lightbox__arrow:hover {
  background: rgba(255, 255, 255, 0.24);
}

.lightbox__arrow--left {
  left: var(--space-4);
}

.lightbox__arrow--right {
  right: var(--space-4);
}
</style>
