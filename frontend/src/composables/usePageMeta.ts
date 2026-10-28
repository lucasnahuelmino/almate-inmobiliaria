/**
 * SEO por ruta: título, descripción, Open Graph, canonical y robots.
 * Se ejecuta en el `afterEach` del router y también puede llamarse en un
 * componente cuando el contenido depende de datos (ej. ficha de propiedad).
 */

export interface PageMeta {
  title: string;
  description?: string;
  robots?: string;
  image?: string;
  url?: string;
}

const SITE_NAME = "ALMATE Propiedades";

function setTag(selector: string, attribute: string, value: string, create: () => HTMLElement) {
  let element = document.head.querySelector<HTMLElement>(selector);
  if (!element) {
    element = create();
    document.head.appendChild(element);
  }
  element.setAttribute(attribute, value);
}

function metaByName(name: string, content: string, isProperty = false) {
  const attribute = isProperty ? "property" : "name";
  setTag(`meta[${attribute}="${name}"]`, "content", content, () => {
    const element = document.createElement("meta");
    element.setAttribute(attribute, name);
    return element;
  });
}

export function usePageMeta() {
  function apply(meta: PageMeta) {
    document.title = meta.title.includes(SITE_NAME) ? meta.title : `${meta.title} | ${SITE_NAME}`;

    if (meta.description) metaByName("description", meta.description);

    const robots = meta.robots ?? "index, follow";
    metaByName("robots", robots);
    metaByName("googlebot", robots);

    const canonical = meta.url ?? window.location.href;
    setTag('link[rel="canonical"]', "href", canonical, () => {
      const link = document.createElement("link");
      link.rel = "canonical";
      return link;
    });

    metaByName("og:site_name", SITE_NAME, true);
    metaByName("og:title", meta.title, true);
    if (meta.description) metaByName("og:description", meta.description, true);
    metaByName("og:type", "website", true);
    metaByName("og:locale", "es_AR", true);
    metaByName("og:url", canonical, true);
    metaByName("og:image", meta.image ?? "/favicon.svg", true);
    metaByName("twitter:card", "summary_large_image");
    metaByName("twitter:title", meta.title);
    if (meta.description) metaByName("twitter:description", meta.description);
  }

  return { apply };
}
