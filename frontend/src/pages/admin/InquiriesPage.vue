<script setup lang="ts">
/** Bandeja de consultas (generales y por propiedad). */
import LeadsInbox from "../../components/admin/LeadsInbox.vue";
import type { Inquiry, LeadLike } from "../../api/types";

function detailFields(item: LeadLike) {
  const inquiry = item as Inquiry;
  return [
    { label: "Correo", value: inquiry.email },
    { label: "Teléfono", value: inquiry.phone ?? "No informado" },
    { label: "Tipo", value: inquiry.kind === "property" ? "Por propiedad" : "Consulta general" },
    {
      label: "Propiedad",
      value: inquiry.property_code
        ? `${inquiry.property_code}${inquiry.property_title ? ` — ${inquiry.property_title}` : ""}`
        : "—",
    },
    { label: "Mensaje", value: inquiry.message },
  ];
}
</script>

<template>
  <LeadsInbox
    endpoint="/admin/inquiries"
    title="Consultas"
    description="enviadas desde el sitio y desde las fichas"
    :detail-fields="detailFields"
    empty-title="Todavía no hay consultas"
    empty-description="Las consultas del formulario de contacto y de las fichas aparecerán acá."
  />
</template>
