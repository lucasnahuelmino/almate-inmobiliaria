<script setup lang="ts">
/** Bandeja de solicitudes de tasación. */
import LeadsInbox from "../../components/admin/LeadsInbox.vue";
import type { LeadLike, ValuationRequest } from "../../api/types";

function detailFields(item: LeadLike) {
  const valuation = item as ValuationRequest;
  return [
    { label: "Correo", value: valuation.email },
    { label: "Teléfono", value: valuation.phone ?? "No informado" },
    { label: "Tipo de propiedad", value: valuation.property_type },
    { label: "Operación", value: valuation.operation ?? "No informada" },
    {
      label: "Localidad",
      value: valuation.neighborhood
        ? `${valuation.locality} (${valuation.neighborhood})`
        : valuation.locality,
    },
    { label: "Superficie", value: valuation.surface_covered ? `${valuation.surface_covered} m²` : "No informada" },
    { label: "Dormitorios", value: valuation.bedrooms ?? "No informados" },
    { label: "Comentarios", value: valuation.message ?? "—" },
  ];
}
</script>

<template>
  <LeadsInbox
    endpoint="/admin/valuation-requests"
    title="Tasaciones"
    description="solicitudes de tasación recibidas"
    :detail-fields="detailFields"
    empty-title="No hay solicitudes de tasación"
    empty-description="Cuando alguien pida una tasación desde /tasacion aparecerá acá."
  />
</template>
