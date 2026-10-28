<script setup lang="ts">
import { computed } from "vue";
import type { PropertySummary } from "../api/types";
import { formatPrice, formatSurface, locationLabel, operationLabel } from "../utils/format";
import StatusBadge from "./StatusBadge.vue";
import FavoriteButton from "./FavoriteButton.vue";

const props = defineProps<{ property: PropertySummary }>();

const image = computed(() => props.property.image?.url ?? "");
const alt = computed(
  () => props.property.image?.alt || `Fotografía de ${props.property.title}`,
);
const location = computed(() => locationLabel(props.property));
const specs = computed(() => {
  const items: string[] = [];
  if (props.property.bedrooms) {
    items.push(`${props.property.bedrooms} ${props.property.bedrooms === 1 ? "dormitorio" : "dormitorios"}`);
  }
  if (props.property.bathrooms) {
    items.push(`${props.property.bathrooms} ${props.property.bathrooms === 1 ? "baño" : "baños"}`);
  }
  if (props.property.garages) {
    items.push(`${props.property.garages} ${props.property.garages === 1 ? "cochera" : "cocheras"}`);
  }
  const surface = formatSurface(props.property.surface_total);
  if (surface) items.push(surface);
  return items;
});
</script>

<template>
  <article class="property-card card">
    <RouterLink
      class="property-card__media"
      :to="`/propiedades/${property.code}`"
      :aria-label="`Ver ${property.title}`"
    >
      <img v-if="image" :src="image" :alt="alt" loading="lazy" decoding="async" />
      <div v-else class="property-card__placeholder" role="img" :aria-label="alt">
        <span>Sin fotografías</span>
      </div>
      <span class="property-card__operation">{{ operationLabel(property.operation) }}</span>
      <StatusBadge
        v-if="property.commercial_status !== 'available'"
        class="property-card__status"
        :commercial="property.commercial_status"
      />
    </RouterLink>

    <div class="property-card__body">
      <div class="property-card__top">
        <div>
          <h3 class="property-card__title">
            <RouterLink :to="`/propiedades/${property.code}`">{{ property.title }}</RouterLink>
          </h3>
          <p class="property-card__location">
            <svg width="13" height="13" viewBox="0 0 24 24" aria-hidden="true">
              <path
                d="M12 21s7-5.6 7-11a7 7 0 1 0-14 0c0 5.4 7 11 7 11Z"
                fill="none"
                stroke="currentColor"
                stroke-width="1.6"
              />
              <circle cx="12" cy="10" r="2.4" fill="none" stroke="currentColor" stroke-width="1.6" />
            </svg>
            {{ location }}
          </p>
        </div>
        <FavoriteButton :code="property.code" />
      </div>

      <p class="property-card__price numeric">
        {{ formatPrice(property.price, property.currency, property.price_unit) }}
      </p>

      <ul v-if="specs.length" class="property-card__specs">
        <li v-for="spec in specs" :key="spec">{{ spec }}</li>
      </ul>

      <div class="property-card__footer">
        <StatusBadge
          :commercial="property.commercial_status"
          :development="property.is_development"
          :featured="property.is_featured"
        />
        <span class="property-card__code">Cód. {{ property.code }}</span>
      </div>
    </div>
  </article>
</template>

<style scoped>
.property-card {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition:
    transform var(--fast),
    box-shadow var(--fast);
}

.property-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-md);
}

.property-card__media {
  position: relative;
  display: block;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  background: var(--color-bg-alt);
}

.property-card__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform var(--slow);
}

.property-card:hover .property-card__media img {
  transform: scale(1.04);
}

.property-card__placeholder {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
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

.property-card__operation {
  position: absolute;
  left: var(--space-3);
  top: var(--space-3);
  padding: 0.2rem 0.7rem;
  background: rgba(34, 35, 33, 0.86);
  color: var(--color-bronze-light);
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  font-weight: 600;
  letter-spacing: 0.04em;
}

.property-card__status {
  position: absolute;
  right: var(--space-3);
  bottom: var(--space-3);
}

.property-card__body {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-4);
  flex: 1;
}

.property-card__top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.property-card__title {
  font-size: var(--text-md);
  line-height: 1.3;
}

.property-card__title a {
  text-decoration: none;
}

.property-card__title a:hover {
  color: var(--color-bronze-dark);
}

.property-card__location {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  margin-top: var(--space-1);
  font-size: var(--text-sm);
  color: var(--color-stone-dark);
}

.property-card__price {
  font-family: var(--font-display);
  font-size: var(--text-lg);
  color: var(--color-ink);
}

.property-card__specs {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2) var(--space-3);
  padding: 0;
  margin: 0;
  list-style: none;
  font-size: var(--text-xs);
  color: var(--color-stone-dark);
}

.property-card__specs li {
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.property-card__specs li:not(:last-child)::after {
  content: "·";
  margin-left: var(--space-2);
  color: var(--color-line-strong);
}

.property-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  margin-top: auto;
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-line);
}

.property-card__code {
  font-size: var(--text-xs);
  letter-spacing: 0.06em;
  color: var(--color-stone-dark);
}
</style>
