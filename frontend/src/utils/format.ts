/** Formateo de importes, superficies y fechas (es-AR). */

import type { Currency, Operation, PriceUnit, PropertyType } from "../api/types";

const integerFormat = new Intl.NumberFormat("es-AR", {
  maximumFractionDigits: 0,
});

const decimalFormat = new Intl.NumberFormat("es-AR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const dateFormat = new Intl.DateTimeFormat("es-AR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

export const OPERATION_LABELS: Record<Operation, string> = {
  buy: "Comprar",
  rent: "Alquilar",
  temporary_rent: "Alquiler temporal",
};

export const TYPE_LABELS: Record<PropertyType, string> = {
  apartment: "Departamento",
  house: "Casa",
  ph: "PH",
  land: "Terreno",
  commercial: "Local comercial",
  office: "Oficina",
  garage: "Cochera",
};

export const COMMERCIAL_LABELS: Record<string, string> = {
  available: "Disponible",
  reserved: "Reservado",
  sold: "Vendido",
  rented: "Alquilado",
};

export const PUBLICATION_LABELS: Record<string, string> = {
  draft: "Borrador",
  published: "Publicada",
  archived: "Archivada",
};

export const UNIT_SUFFIX: Record<PriceUnit, string> = {
  total: "",
  monthly: " / mes",
  daily: " / noche",
};

export const CURRENCY_SYMBOLS: Record<Currency | string, string> = {
  ARS: "$",
  USD: "U$S",
  EUR: "€",
};

/** `152000.50` → `"152.000,50"`; los enteros se muestran sin decimales. */
export function formatAmount(value: string | number | null | undefined): string {
  if (value === null || value === undefined || value === "") return "—";
  const parsed = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(parsed)) return String(value);
  return Number.isInteger(parsed) ? integerFormat.format(parsed) : decimalFormat.format(parsed);
}

/** Precio completo con moneda y unidad: `"U$S 152.000"`. */
export function formatPrice(
  price: string | null,
  currency: string,
  unit: PriceUnit = "total",
): string {
  if (price === null) return "Consultar precio";
  const symbol = CURRENCY_SYMBOLS[currency] ?? currency;
  return `${symbol} ${formatAmount(price)}${UNIT_SUFFIX[unit]}`;
}

/** Superficie: `"68"` → `"68 m²"`. */
export function formatSurface(value: string | null, label = "m²"): string {
  if (!value) return "";
  const amount = formatAmount(value);
  return `${amount} ${label}`;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "—" : dateFormat.format(date);
}

/** Etiqueta de operación para el dominio público. */
export function operationLabel(operation: Operation): string {
  return OPERATION_LABELS[operation] ?? operation;
}

export function typeLabel(type: PropertyType): string {
  return TYPE_LABELS[type] ?? type;
}

/** Localidad / barrio más específico disponible. */
export function locationLabel(item: {
  neighborhood: string | null;
  locality: string | null;
  province: string | null;
}): string {
  const parts = [item.neighborhood, item.locality, item.province].filter(
    (part): part is string => Boolean(part),
  );
  return parts.join(", ");
}
