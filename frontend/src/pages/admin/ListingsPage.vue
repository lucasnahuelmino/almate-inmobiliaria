<script setup lang="ts">
/** Bandeja de solicitudes de publicación de propiedades. */
import LeadsInbox from "../../components/admin/LeadsInbox.vue";
import type { LeadLike, ListingRequest } from "../../api/types";

function detailFields(item: LeadLike) {
  const listing = item as ListingRequest;
  return [
    { label: "Correo", value: listing.email },
    { label: "Teléfono", value: listing.phone ?? "No informado" },
    { label: "Operación", value: listing.operation },
    { label: "Tipo de propiedad", value: listing.property_type },
    {
      label: "Localidad",
      value: listing.neighborhood ? `${listing.locality} (${listing.neighborhood})` : listing.locality,
    },
    { label: "Superficie", value: listing.surface_covered ? `${listing.surface_covered} m²` : "No informada" },
    { label: "Dormitorios", value: listing.bedrooms ?? "No informados" },
    { label: "Precio esperado", value: listing.expected_price ?? "No informado" },
    { label: "Mensaje", value: listing.message ?? "—" },
  ];
}
</script>

<template>
  <LeadsInbox
    endpoint="/admin/listing-requests"
    title="Publicaciones"
    description="propietarios que quieren publicar su propiedad"
    :detail-fields="detailFields"
    empty-title="No hay solicitudes de publicación"
    empty-description="Las solicitudes enviadas desde /publicar-propiedad aparecerán acá."
  />
</template>
