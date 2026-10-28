import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError, getStoredUser, getToken, setSession, toQuery } from "../client";

afterEach(() => {
  vi.unstubAllGlobals();
  window.localStorage.clear();
});

describe("toQuery", () => {
  it("omite vacíos, nulos y falsos", () => {
    expect(toQuery({ q: "", page: 1, active: false, missing: null, ok: true })).toBe(
      "?page=1&ok=true",
    );
  });

  it("devuelve cadena vacía si no hay parámetros", () => {
    expect(toQuery({})).toBe("");
    expect(toQuery({ q: "" })).toBe("");
  });
});

describe("ApiError", () => {
  it("conserva estado y mensajes del backend", () => {
    const error = new ApiError(422, "Datos inválidos", [
      { loc: ["body", "email"], msg: "Correo inválido" },
    ]);
    expect(error.status).toBe(422);
    expect(error.message).toBe("Datos inválidos");
    expect(error.fieldError("email")).toBe("Correo inválido");
    expect(error.fieldError("phone")).toBeUndefined();
  });
});

describe("sesión", () => {
  it("guarda y limpia el token junto al usuario", () => {
    expect(getToken()).toBeNull();

    setSession("abc", JSON.stringify({ id: 1 }));
    expect(getToken()).toBe("abc");
    expect(getStoredUser<{ id: number }>()).toEqual({ id: 1 });

    setSession(null, null);
    expect(getToken()).toBeNull();
    expect(getStoredUser()).toBeNull();
  });

  it("tolera usuarios corruptos en almacenamiento", () => {
    window.localStorage.setItem("almate.user", "{esto no es json");
    expect(getStoredUser()).toBeNull();
  });
});

describe("request", () => {
  it("convierte fallos del backend en ApiError con su mensaje", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ message: "Credenciales inválidas." }),
      }),
    );

    const { api } = await import("../client");
    await expect(api.get("/auth/me")).rejects.toMatchObject({
      status: 401,
      message: "Credenciales inválidas.",
    });
  });

  it("ofrece un mensaje claro cuando el servidor no responde", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
    );

    const { api } = await import("../client");
    await expect(api.get("/properties")).rejects.toMatchObject({ status: 0 });
  });
});
