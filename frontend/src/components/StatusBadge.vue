<script setup lang="ts">
import { computed } from "vue";
import { COMMERCIAL_LABELS, PUBLICATION_LABELS } from "../utils/format";

const props = withDefaults(
  defineProps<{
    commercial?: string;
    publication?: string;
    featured?: boolean;
    development?: boolean;
  }>(),
  { commercial: "", publication: "", featured: false, development: false },
);

const badges = computed(() => {
  const items: { label: string; className: string }[] = [];
  if (props.commercial && props.commercial !== "available") {
    items.push({
      label: COMMERCIAL_LABELS[props.commercial] ?? props.commercial,
      className: `badge--${props.commercial}`,
    });
  } else if (props.commercial) {
    items.push({
      label: COMMERCIAL_LABELS[props.commercial] ?? props.commercial,
      className: "badge--available",
    });
  }
  if (props.publication && props.publication !== "published") {
    items.push({
      label: PUBLICATION_LABELS[props.publication] ?? props.publication,
      className: `badge--${props.publication}`,
    });
  }
  if (props.development) {
    items.push({ label: "Emprendimiento", className: "badge--bronze" });
  }
  if (props.featured) {
    items.push({ label: "Destacada", className: "badge--featured" });
  }
  return items;
});
</script>

<template>
  <div class="badges">
    <span v-for="badge in badges" :key="badge.label" class="badge" :class="badge.className">
      {{ badge.label }}
    </span>
  </div>
</template>

<style scoped>
.badges {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}
</style>
