import { describe, expect, it } from "vitest";
import {
  COMMERCIAL_LABELS,
  CURRENCY_SYMBOLS,
  formatAmount,
  formatDate,
  formatPrice,
  formatSurface,
  locationLabel,
  operationLabel,
  PUBLICATION_LABELS,
  typeLabel,
} from "../format";

describe("formatAmount", () => {
  it("formatea con separadores argentinos", () => {
    expect(formatAmount("152000.50")).toBe("152.000,50");
    expect(formatAmount("152000")).toBe("152.000");
    expect(formatAmount(900)).toBe("900");
  });

  it("marca ausencias con un guion", () => {
    expect(formatAmount(null)).toBe("—");
    expect(formatAmount(undefined)).toBe("—");
    expect(formatAmount("")).toBe("—");
  });

  it("no rompe con texto no numérico", () => {
    expect(formatAmount("consultar")).toBe("consultar");
  });

  it("acepta centavos exactos", () => {
    expect(formatAmount("88550.25")).toBe("88.550,25");
  });
});

describe("formatPrice", () => {
  it("usa el símbolo de la moneda", () => {
    expect(formatPrice("152000", "USD")).toBe("U$S 152.000");
    expect(formatPrice("350000", "ARS")).toBe("$ 350.000");
    expect(formatPrice("9000", "EUR")).toBe("€ 9.000");
    expect(CURRENCY_SYMBOLS.USD).toBe("U$S");
  });

  it("agrega la unidad del precio", () => {
    expect(formatPrice("350000", "ARS", "monthly")).toBe("$ 350.000 / mes");
    expect(formatPrice("65000", "ARS", "daily")).toBe("$ 65.000 / noche");
    expect(formatPrice("152000", "USD", "total")).toBe("U$S 152.000");
  });

  it("informa cuando no hay precio publicado", () => {
    expect(formatPrice(null, "USD")).toBe("Consultar precio");
  });
});

describe("formatSurface", () => {
  it("expresa en metros cuadrados", () => {
    expect(formatSurface("68.5")).toBe("68,50 m²");
    expect(formatSurface("68")).toBe("68 m²");
  });

  it("devuelve vacío si no hay dato", () => {
    expect(formatSurface(null)).toBe("");
    expect(formatSurface("")).toBe("");
  });
});

describe("formatDate", () => {
  it("formatea fechas ISO en es-AR", () => {
    expect(formatDate("2026-03-15T12:00:00Z")).toMatch(/15\/03\/2026|14\/03\/2026/);
  });

  it("usa guiones ante fechas ausentes o inválidas", () => {
    expect(formatDate(null)).toBe("—");
    expect(formatDate("no-fecha")).toBe("—");
  });
});

describe("etiquetas del dominio", () => {
  it("traduce operaciones y tipos", () => {
    expect(operationLabel("buy")).toBe("Comprar");
    expect(operationLabel("temporary_rent")).toBe("Alquiler temporal");
    expect(typeLabel("apartment")).toBe("Departamento");
    expect(typeLabel("ph")).toBe("PH");
  });

  it("traduce estados comerciales y de publicación", () => {
    expect(COMMERCIAL_LABELS.available).toBe("Disponible");
    expect(COMMERCIAL_LABELS.reserved).toBe("Reservado");
    expect(COMMERCIAL_LABELS.sold).toBe("Vendido");
    expect(PUBLICATION_LABELS.draft).toBe("Borrador");
    expect(PUBLICATION_LABELS.archived).toBe("Archivada");
  });
});

describe("locationLabel", () => {
  it("muestra lo más específico disponible", () => {
    expect(
      locationLabel({ neighborhood: "Bernal", locality: "Quilmes", province: "Buenos Aires" }),
    ).toBe("Bernal, Quilmes, Buenos Aires");
  });

  it("omite los campos vacíos", () => {
    expect(locationLabel({ neighborhood: null, locality: "Wilde", province: "Buenos Aires" })).toBe(
      "Wilde, Buenos Aires",
    );
    expect(locationLabel({ neighborhood: null, locality: null, province: null })).toBe("");
  });
});
