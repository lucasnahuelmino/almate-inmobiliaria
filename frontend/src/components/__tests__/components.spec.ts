import { beforeEach, describe, expect, it } from "vitest";
import { mount, type VueWrapper } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import PaginationNav from "../PaginationNav.vue";
import StatusBadge from "../StatusBadge.vue";
import FavoriteButton from "../FavoriteButton.vue";
import LoadingBlock from "../LoadingBlock.vue";
import EmptyState from "../EmptyState.vue";
import ErrorState from "../ErrorState.vue";
import PropertyCard from "../PropertyCard.vue";
import { useFavoritesStore } from "../../stores/favorites";
import type { PropertySummary } from "../../api/types";

const routerStub = {
  props: ["to"],
  template: '<a :href="String(to)"><slot /></a>',
};

function mountWithRouter(component: unknown, options = {}): VueWrapper {
  return mount(component as never, {
    global: { stubs: { RouterLink: routerStub } },
    ...options,
  });
}

function makeProperty(overrides: Partial<PropertySummary> = {}): PropertySummary {
  return {
    code: "ALM-D01-26",
    title: "Departamento con balcón",
    operation: "buy",
    property_type: "apartment",
    is_development: false,
    is_featured: false,
    price: "152000",
    currency: "USD",
    price_unit: "total",
    expenses: null,
    commercial_status: "available",
    publication_status: "published",
    country: "Argentina",
    province: "Buenos Aires",
    department: null,
    locality: "Quilmes",
    neighborhood: "Bernal",
    address: null,
    address_is_public: true,
    rooms: 3,
    bedrooms: 2,
    bathrooms: 1,
    garages: 1,
    surface_covered: "68",
    surface_total: "82",
    apto_professional: false,
    published_at: "2026-02-10T12:00:00Z",
    image: {
      id: 1,
      url: "/static/uploads/properties/x/fachada.jpg",
      alt: "Fachada",
      is_main: true,
      sort_order: 0,
    },
    ...overrides,
  };
}

beforeEach(() => {
  setActivePinia(createPinia());
  window.localStorage.clear();
});

describe("PaginationNav", () => {
  it("no se muestra con una sola página", () => {
    const wrapper = mount(PaginationNav, { props: { page: 1, pages: 1, total: 3 } });
    expect(wrapper.find("nav").exists()).toBe(false);
  });

  it("marca la página actual", () => {
    const wrapper = mount(PaginationNav, { props: { page: 2, pages: 5, total: 60 } });
    const current = wrapper.find('button[aria-current="page"]');
    expect(current.exists()).toBe(true);
    expect(current.text()).toBe("2");
  });

  it("desactiva anterior en la primera página y siguiente en la última", () => {
    const first = mount(PaginationNav, { props: { page: 1, pages: 3, total: 30 } });
    const buttons = first.findAll("button");
    expect(buttons[0].attributes("disabled")).toBeDefined();
    expect(buttons[buttons.length - 1].attributes("disabled")).toBeUndefined();
  });

  it("emite el número de página al navegar", async () => {
    const wrapper = mount(PaginationNav, { props: { page: 1, pages: 4, total: 40 } });
    const buttons = wrapper.findAll("button");
    // La última es "Siguiente": pasa de la página 1 a la 2.
    await buttons[buttons.length - 1].trigger("click");
    expect(wrapper.emitted("change")).toEqual([[2]]);
  });

  it("no emite al pulsar la página en la que ya está", async () => {
    const wrapper = mount(PaginationNav, { props: { page: 2, pages: 4, total: 40 } });
    const current = wrapper.find('button[aria-current="page"]');
    await current.trigger("click");
    expect(wrapper.emitted("change")).toBeUndefined();
  });

  it("usa puntos suspensivos cuando hay muchas páginas", () => {
    const wrapper = mount(PaginationNav, { props: { page: 5, pages: 20, total: 240 } });
    expect(wrapper.text()).toContain("…");
    expect(wrapper.text()).toContain("20");
  });
});

describe("StatusBadge", () => {
  it("muestra el estado comercial", () => {
    const wrapper = mount(StatusBadge, { props: { commercial: "reserved" } });
    expect(wrapper.text()).toContain("Reservado");
  });

  it("resalta destacadas y emprendimientos", () => {
    const wrapper = mount(StatusBadge, {
      props: { commercial: "available", featured: true, development: true },
    });
    expect(wrapper.text()).toContain("Destacada");
    expect(wrapper.text()).toContain("Emprendimiento");
  });

  it("muestra el estado de publicación cuando no está publicada", () => {
    const wrapper = mount(StatusBadge, {
      props: { commercial: "available", publication: "draft" },
    });
    expect(wrapper.text()).toContain("Borrador");
  });

  it("no muestra 'Publicada' (ruido innecesario)", () => {
    const wrapper = mount(StatusBadge, {
      props: { commercial: "available", publication: "published" },
    });
    expect(wrapper.text()).not.toContain("Publicada");
  });
});

describe("FavoriteButton", () => {
  it("guarda y quita del almacenamiento local", async () => {
    const wrapper = mount(FavoriteButton, { props: { code: "ALM-D01-26" } });
    expect(wrapper.attributes("aria-pressed")).toBe("false");

    await wrapper.trigger("click");
    expect(wrapper.attributes("aria-pressed")).toBe("true");
    expect(window.localStorage.getItem("almate.favoritos")).toContain("ALM-D01-26");

    await wrapper.trigger("click");
    expect(wrapper.attributes("aria-pressed")).toBe("false");
    expect(window.localStorage.getItem("almate.favoritos")).toBe("[]");
  });

  it("comparte el estado con el store", async () => {
    const store = useFavoritesStore();
    const wrapper = mount(FavoriteButton, { props: { code: "ALM-X" } });
    store.toggle("ALM-X");
    await wrapper.vm.$nextTick();
    expect(wrapper.attributes("aria-pressed")).toBe("true");
  });
});

describe("estados de carga y error", () => {
  it("LoadingBlock anuncia el estado", () => {
    const wrapper = mount(LoadingBlock, { props: { label: "Cargando datos…" } });
    expect(wrapper.attributes("role")).toBe("status");
    expect(wrapper.text()).toContain("Cargando datos…");
  });

  it("ErrorState emite retry", async () => {
    const wrapper = mount(ErrorState, { props: { message: "Fallo de red" } });
    expect(wrapper.text()).toContain("Fallo de red");
    await wrapper.find("button").trigger("click");
    expect(wrapper.emitted("retry")).toBeTruthy();
  });

  it("EmptyState sólo muestra la acción si se indica", () => {
    const withAction = mount(EmptyState, {
      props: { title: "Sin resultados", actionLabel: "Limpiar" },
    });
    expect(withAction.find("button").exists()).toBe(true);

    const withoutAction = mount(EmptyState, { props: { title: "Sin resultados" } });
    expect(withoutAction.find("button").exists()).toBe(false);
  });
});

describe("PropertyCard", () => {
  it("muestra precio, ubicación, superficie y código", () => {
    const wrapper = mountWithRouter(PropertyCard, { props: { property: makeProperty() } });
    expect(wrapper.text()).toContain("U$S 152.000");
    expect(wrapper.text()).toContain("Bernal, Quilmes");
    expect(wrapper.text()).toContain("82 m²");
    expect(wrapper.text()).toContain("ALM-D01-26");
    expect(wrapper.text()).toContain("2 dormitorios");
  });

  it("describe la fotografía con texto alternativo", () => {
    const wrapper = mountWithRouter(PropertyCard, { props: { property: makeProperty() } });
    const image = wrapper.find("img");
    expect(image.attributes("alt")).toBe("Fachada");
    expect(image.attributes("loading")).toBe("lazy");
  });

  it("ofrece un placeholder cuando no hay fotografías", () => {
    const wrapper = mountWithRouter(PropertyCard, {
      props: { property: makeProperty({ image: null }) },
    });
    expect(wrapper.text()).toContain("Sin fotografías");
  });

  it("indica 'Consultar precio' cuando no hay precio", () => {
    const wrapper = mountWithRouter(PropertyCard, {
      props: { property: makeProperty({ price: null }) },
    });
    expect(wrapper.text()).toContain("Consultar precio");
  });

  it("muestra la unidad mensual en alquileres", () => {
    const wrapper = mountWithRouter(PropertyCard, {
      props: {
        property: makeProperty({
          operation: "rent",
          price: "350000",
          currency: "ARS",
          price_unit: "monthly",
        }),
      },
    });
    expect(wrapper.text()).toContain("$ 350.000 / mes");
    expect(wrapper.text()).toContain("Alquilar");
  });

  it("marca estados que no están disponibles", () => {
    const wrapper = mountWithRouter(PropertyCard, {
      props: { property: makeProperty({ commercial_status: "sold" }) },
    });
    expect(wrapper.text()).toContain("Vendido");
  });
});
