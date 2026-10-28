import { describe, expect, it } from "vitest";
import {
  activeFilterCount,
  defaultFilters,
  PAGE_SIZE,
  parseFilters,
  toApiParams,
  toRouteQuery,
  type CatalogFilters,
} from "../filters";

function filters(overrides: Partial<CatalogFilters> = {}): CatalogFilters {
  return { ...defaultFilters(), ...overrides };
}

describe("parseFilters", () => {
  it("lee los parámetros de la URL con sus nombres en español", () => {
    const parsed = parseFilters({
      q: "balcon",
      tipo: "apartment",
      localidad: "Quilmes",
      precio_min: "50000",
      precio_max: "150000",
      dormitorios: "2",
      banos: "1",
      superficie_min: "60",
      superficie_max: "200",
      cochera: "1",
      apto: "1",
      orden: "price_desc",
      pagina: "3",
      favoritos: "1",
    });

    expect(parsed).toMatchObject({
      q: "balcon",
      type: "apartment",
      locality: "Quilmes",
      minPrice: "50000",
      maxPrice: "150000",
      bedrooms: "2",
      bathrooms: "1",
      minSurface: "60",
      maxSurface: "200",
      garage: true,
      apto: true,
      sort: "price_desc",
      page: 3,
      favoritesOnly: true,
    });
  });

  it("devuelve filtros por defecto ante una URL vacía", () => {
    expect(parseFilters({})).toEqual(defaultFilters());
  });

  it("descarta parámetros desconocidos o inválidos", () => {
    const parsed = parseFilters({ orden: "no-existe", pagina: "abc" });
    expect(parsed.sort).toBe("recent");
    expect(parsed.page).toBe(1);
  });

  it("no arranca en página 0 ni negativa", () => {
    expect(parseFilters({ pagina: "-4" }).page).toBe(1);
    expect(parseFilters({ pagina: "0" }).page).toBe(1);
  });

  it("ignora arreglos (query repetida)", () => {
    expect(parseFilters({ q: ["a", "b"] }).q).toBe("");
  });
});

describe("toRouteQuery", () => {
  it("omite los valores por defecto para mantener URLs limpias", () => {
    expect(toRouteQuery(defaultFilters())).toEqual({});
  });

  it("escribe sólo los filtros activos", () => {
    const query = toRouteQuery(
      filters({ q: "casa", garage: true, sort: "price_asc", page: 2 }),
    );
    expect(query).toEqual({ q: "casa", cochera: "1", orden: "price_asc", pagina: "2" });
  });
});

describe("ida y vuelta URL <-> filtros", () => {
  it("no pierde información", () => {
    const original = filters({
      q: "pool",
      type: "house",
      locality: "Bernal",
      minPrice: "100",
      maxPrice: "900",
      bedrooms: "3",
      bathrooms: "2",
      minSurface: "80",
      maxSurface: "400",
      garage: true,
      apto: true,
      sort: "oldest",
      page: 4,
      favoritesOnly: true,
    });

    expect(parseFilters(toRouteQuery(original))).toEqual(original);
  });
});

describe("toApiParams", () => {
  it("siempre envía página, tamaño y orden", () => {
    const params = toApiParams(defaultFilters(), "all");
    expect(params).toMatchObject({ page: 1, page_size: PAGE_SIZE, sort: "recent" });
  });

  it("fija la operación según el catálogo", () => {
    expect(toApiParams(defaultFilters(), "rent").operation).toBe("rent");
    expect(toApiParams(defaultFilters(), "temporary_rent").operation).toBe("temporary_rent");
    expect(toApiParams(defaultFilters(), "buy").operation).toBe("buy");
  });

  it("en emprendimientos usa development y no operation", () => {
    const params = toApiParams(defaultFilters(), "development");
    expect(params.development).toBe("true");
    expect(params.operation).toBeUndefined();
  });

  it("en 'all' no filtra por operación", () => {
    expect(toApiParams(defaultFilters(), "all").operation).toBeUndefined();
  });

  it("omite los filtros vacíos", () => {
    const params = toApiParams(defaultFilters(), "buy");
    expect(params.q).toBeUndefined();
    expect(params.type).toBeUndefined();
    expect(params.min_price).toBeUndefined();
    expect(params.garage).toBeUndefined();
  });

  it("traduce los nombres de los filtros a los de la API", () => {
    const params = toApiParams(
      filters({
        q: "pool",
        type: "house",
        locality: "Quilmes",
        minPrice: "10",
        maxPrice: "20",
        bedrooms: "2",
        bathrooms: "1",
        minSurface: "30",
        maxSurface: "90",
        garage: true,
        apto: true,
      }),
      "buy",
    );

    expect(params).toMatchObject({
      q: "pool",
      type: "house",
      locality: "Quilmes",
      min_price: "10",
      max_price: "20",
      bedrooms: "2",
      bathrooms: "1",
      min_surface: "30",
      max_surface: "90",
      garage: "true",
      apto_professional: "true",
    });
  });

  it("respeta el tamaño de página personalizado", () => {
    expect(toApiParams(defaultFilters(), "all", 60).page_size).toBe(60);
  });
});

describe("activeFilterCount", () => {
  it("cuenta cero cuando no hay filtros", () => {
    expect(activeFilterCount(defaultFilters())).toBe(0);
  });

  it("cuenta cada filtro activo", () => {
    expect(
      activeFilterCount(filters({ q: "a", type: "house", garage: true })),
    ).toBe(3);
  });

  it("no cuenta el orden ni la página", () => {
    expect(activeFilterCount(filters({ sort: "price_desc", page: 7 }))).toBe(0);
  });
});
