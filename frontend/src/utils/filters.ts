/**
 * Filtros del catálogo: modelo único compartido entre la URL, el formulario
 * y la query string que viaja a la API.
 */

import type { Operation, SortOption } from "../api/types";

export type CatalogMode = "buy" | "rent" | "temporary_rent" | "development" | "all";

export interface CatalogFilters {
  q: string;
  type: string;
  locality: string;
  minPrice: string;
  maxPrice: string;
  bedrooms: string;
  bathrooms: string;
  minSurface: string;
  maxSurface: string;
  garage: boolean;
  apto: boolean;
  sort: SortOption;
  page: number;
  favoritesOnly: boolean;
}

export const SORT_OPTIONS: { value: SortOption; label: string }[] = [
  { value: "recent", label: "Más recientes" },
  { value: "price_asc", label: "Menor precio" },
  { value: "price_desc", label: "Mayor precio" },
  { value: "oldest", label: "Más antiguas" },
];

export const PAGE_SIZE = 12;

export function defaultFilters(): CatalogFilters {
  return {
    q: "",
    type: "",
    locality: "",
    minPrice: "",
    maxPrice: "",
    bedrooms: "",
    bathrooms: "",
    minSurface: "",
    maxSurface: "",
    garage: false,
    apto: false,
    sort: "recent",
    page: 1,
    favoritesOnly: false,
  };
}

const SORT_VALUES = SORT_OPTIONS.map((option) => option.value);

type QuerySource = Record<string, unknown>;

/** Lee los filtros desde `route.query`. */
export function parseFilters(query: QuerySource): CatalogFilters {
  const read = (key: string): string => {
    const value = query[key];
    return typeof value === "string" ? value : "";
  };
  const sort = read("orden") as SortOption;

  return {
    q: read("q"),
    type: read("tipo"),
    locality: read("localidad"),
    minPrice: read("precio_min"),
    maxPrice: read("precio_max"),
    bedrooms: read("dormitorios"),
    bathrooms: read("banos"),
    minSurface: read("superficie_min"),
    maxSurface: read("superficie_max"),
    garage: read("cochera") === "1",
    apto: read("apto") === "1",
    sort: SORT_VALUES.includes(sort) ? sort : "recent",
    page: Math.max(1, Number.parseInt(read("pagina") || "1", 10) || 1),
    favoritesOnly: read("favoritos") === "1",
  };
}

/** Escribe los filtros en `route.query` (omite valores por defecto). */
export function toRouteQuery(filters: CatalogFilters): Record<string, string> {
  const query: Record<string, string> = {};
  if (filters.q) query.q = filters.q;
  if (filters.type) query.tipo = filters.type;
  if (filters.locality) query.localidad = filters.locality;
  if (filters.minPrice) query.precio_min = filters.minPrice;
  if (filters.maxPrice) query.precio_max = filters.maxPrice;
  if (filters.bedrooms) query.dormitorios = filters.bedrooms;
  if (filters.bathrooms) query.banos = filters.bathrooms;
  if (filters.minSurface) query.superficie_min = filters.minSurface;
  if (filters.maxSurface) query.superficie_max = filters.maxSurface;
  if (filters.garage) query.cochera = "1";
  if (filters.apto) query.apto = "1";
  if (filters.sort !== "recent") query.orden = filters.sort;
  if (filters.page > 1) query.pagina = String(filters.page);
  if (filters.favoritesOnly) query.favoritos = "1";
  return query;
}

/** Convierte los filtros en parámetros de la API pública. */
export function toApiParams(
  filters: CatalogFilters,
  mode: CatalogMode,
  pageSize = PAGE_SIZE,
): Record<string, string | number> {
  const params: Record<string, string | number> = {
    page: filters.page,
    page_size: pageSize,
    sort: filters.sort,
  };

  if (mode === "development") {
    params.development = "true";
  } else if (mode !== "all") {
    params.operation = mode as Operation;
  }

  if (filters.q) params.q = filters.q;
  if (filters.type) params.type = filters.type;
  if (filters.locality) params.locality = filters.locality;
  if (filters.minPrice) params.min_price = filters.minPrice;
  if (filters.maxPrice) params.max_price = filters.maxPrice;
  if (filters.bedrooms) params.bedrooms = filters.bedrooms;
  if (filters.bathrooms) params.bathrooms = filters.bathrooms;
  if (filters.minSurface) params.min_surface = filters.minSurface;
  if (filters.maxSurface) params.max_surface = filters.maxSurface;
  if (filters.garage) params.garage = "true";
  if (filters.apto) params.apto_professional = "true";
  return params;
}

/** Cantidad de filtros activos (para mostrar "limpiar"). */
export function activeFilterCount(filters: CatalogFilters): number {
  return [
    filters.q,
    filters.type,
    filters.locality,
    filters.minPrice,
    filters.maxPrice,
    filters.bedrooms,
    filters.bathrooms,
    filters.minSurface,
    filters.maxSurface,
    filters.garage ? "1" : "",
    filters.apto ? "1" : "",
  ].filter(Boolean).length;
}
