import { describe, expect, it } from "vitest";
import type { PublicSettings } from "../../api/types";
import { buildWhatsAppMessage, normalizePhone, whatsappLink } from "../whatsapp";

const settings = {
  whatsapp: "+54 9 11 5555-0000",
  whatsapp_is_demo: true,
} as PublicSettings;

describe("normalizePhone", () => {
  it("deja sólo dígitos", () => {
    expect(normalizePhone("+54 9 11 5555-0000")).toBe("5491155550000");
    expect(normalizePhone("(011) 4444 2222")).toBe("01144442222");
  });
});

describe("buildWhatsAppMessage", () => {
  it("incluye la intención inicial", () => {
    const text = buildWhatsAppMessage({ intent: "consultar por un departamento" });
    expect(text).toBe("Hola, quiero consultar por un departamento.\nGracias.");
  });

  it("incluye código, título, operación, ubicación y URL", () => {
    const text = buildWhatsAppMessage({
      intent: "agendar una visita",
      code: "ALM-D01-26",
      title: "Departamento con balcón",
      operation: "buy",
      location: "Bernal, Quilmes",
      url: "https://almate.demo/propiedades/ALM-D01-26",
    });

    expect(text).toContain("Hola, quiero agendar una visita.");
    expect(text).toContain("Propiedad: ALM-D01-26 (Departamento con balcón · Comprar · Bernal, Quilmes)");
    expect(text).toContain("https://almate.demo/propiedades/ALM-D01-26");
    expect(text.endsWith("Gracias.")).toBe(true);
  });

  it("funciona sin intención ni propiedad", () => {
    const text = buildWhatsAppMessage({});
    expect(text).toBe("Hola, quiero hacer una consulta.\nGracias.");
  });
});

describe("whatsappLink", () => {
  it("arma un enlace wa.me con el mensaje codificado", () => {
    const link = whatsappLink(settings, { code: "ALM-D02-26", operation: "rent" });
    expect(link.startsWith("https://wa.me/5491155550000?text=")).toBe(true);
    expect(decodeURIComponent(link.split("?text=")[1])).toContain("ALM-D02-26");
  });

  it("devuelve vacío si no hay número configurado", () => {
    const empty = { ...settings, whatsapp: "" } as PublicSettings;
    expect(whatsappLink(empty, { code: "X" })).toBe("");
  });
});
