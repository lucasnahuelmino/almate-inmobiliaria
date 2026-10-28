/**
 * Enlaces de WhatsApp con mensaje precargado.
 *
 * El número se toma de la configuración del negocio (panel administrativo).
 * La demo usa un número ficticio: `whatsapp_is_demo` lo indica para mostrar
 * un aviso al usuario. Nunca se envía nada automáticamente: sólo se abre la
 * conversación con el texto sugerido.
 */

import type { Operation, PublicSettings } from "../api/types";
import { OPERATION_LABELS } from "./format";

export interface WhatsAppContext {
  code?: string;
  title?: string;
  operation?: Operation;
  location?: string;
  url?: string;
  intent?: string;
}

/** Limpia el número y devuelve sólo dígitos (formato internacional). */
export function normalizePhone(phone: string): string {
  return phone.replace(/\D/g, "");
}

export function buildWhatsAppMessage(context: WhatsAppContext): string {
  const lines: string[] = [];

  if (context.intent) {
    lines.push(`Hola, quiero ${context.intent}.`);
  } else {
    lines.push("Hola, quiero hacer una consulta.");
  }

  if (context.code) {
    const details = [
      context.title,
      context.operation ? OPERATION_LABELS[context.operation] : undefined,
      context.location,
    ]
      .filter(Boolean)
      .join(" · ");
    lines.push(`Propiedad: ${context.code}${details ? ` (${details})` : ""}`);
  }

  if (context.url) lines.push(context.url);
  lines.push("Gracias.");
  return lines.join("\n");
}

export function whatsappLink(settings: PublicSettings, context: WhatsAppContext): string {
  const number = normalizePhone(settings.whatsapp || "");
  const text = encodeURIComponent(buildWhatsAppMessage(context));
  return number ? `https://wa.me/${number}?text=${text}` : "";
}
