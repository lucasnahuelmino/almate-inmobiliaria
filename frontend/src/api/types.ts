/**
 * Tipos del dominio: reflejan los esquemas que devuelve la API FastAPI.
 * Los importes viajan como cadenas decimales (ej. `"152000.50"`).
 */

export type Operation = "buy" | "rent" | "temporary_rent";
export type PropertyType =
  | "apartment"
  | "house"
  | "ph"
  | "land"
  | "commercial"
  | "office"
  | "garage";
export type CommercialStatus = "available" | "reserved" | "sold" | "rented";
export type PublicationStatus = "draft" | "published" | "archived";
export type PriceUnit = "total" | "monthly" | "daily";
export type Currency = "ARS" | "USD" | "EUR";
export type SortOption = "recent" | "oldest" | "price_asc" | "price_desc";
export type LeadStatus = "new" | "following" | "answered" | "archived";
export type UserRole = "admin" | "editor";

export interface PropertyImage {
  id: number;
  url: string;
  alt: string;
  is_main: boolean;
  sort_order: number;
}

export interface PropertyImageAdmin extends PropertyImage {
  filename: string;
  mime_type: string;
  size_bytes: number;
  created_at: string;
}

export interface PropertySummary {
  code: string;
  title: string;
  operation: Operation;
  property_type: PropertyType;
  is_development: boolean;
  is_featured: boolean;
  price: string | null;
  currency: Currency;
  price_unit: PriceUnit;
  expenses: string | null;
  commercial_status: CommercialStatus;
  publication_status: PublicationStatus;
  country: string;
  province: string;
  department: string | null;
  locality: string | null;
  neighborhood: string | null;
  address: string | null;
  address_is_public: boolean;
  rooms: number | null;
  bedrooms: number | null;
  bathrooms: number | null;
  garages: number | null;
  surface_covered: string | null;
  surface_total: string | null;
  apto_professional: boolean;
  published_at: string | null;
  image: PropertyImage | null;
}

export interface PropertyDetail extends PropertySummary {
  description: string;
  toilets: number | null;
  antiquity_years: number | null;
  surface_semicovered: string | null;
  services: string[];
  images: PropertyImage[];
  created_at: string | null;
  updated_at: string | null;
}

export interface PropertyAdmin extends PropertyDetail {
  id: string;
  created_by: number | null;
  created_at: string;
  updated_at: string;
  images: PropertyImageAdmin[];
}

export interface PropertyPage {
  items: PropertySummary[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface LabeledValue {
  value: string;
  label: string;
}

export interface CatalogMeta {
  operations: LabeledValue[];
  property_types: LabeledValue[];
  commercial_statuses: LabeledValue[];
  currencies: string[];
  localities: string[];
  sort_options: LabeledValue[];
}

export interface PublicSettings {
  brand_name: string;
  brand_descriptor: string;
  tagline: string;
  logo_path: string | null;
  phone: string;
  whatsapp: string;
  whatsapp_is_demo: boolean;
  email: string;
  address_line: string;
  city: string;
  office_hours: string;
  instagram: string | null;
  facebook: string | null;
  linkedin: string | null;
  institutional_text: string;
  footer_note: string;
  developer_credit: string;
  default_currency: Currency;
  show_expenses: boolean;
}

export interface AuthUser {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  last_login_at: string | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}

export interface Note {
  id: number;
  body: string;
  author_id: number | null;
  created_at: string;
}

export interface Inquiry {
  id: number;
  kind: "property" | "general";
  status: LeadStatus;
  name: string;
  email: string;
  phone: string | null;
  message: string;
  property_id: string | null;
  property_code: string | null;
  property_title: string | null;
  created_at: string;
  updated_at: string | null;
  notes: Note[];
}

export interface ValuationRequest {
  id: number;
  status: LeadStatus;
  name: string;
  email: string;
  phone: string | null;
  property_type: string;
  operation: string | null;
  locality: string;
  neighborhood: string | null;
  surface_covered: string | null;
  bedrooms: string | null;
  message: string | null;
  created_at: string;
  updated_at: string | null;
  notes: Note[];
}

export interface ListingRequest {
  id: number;
  status: LeadStatus;
  name: string;
  email: string;
  phone: string | null;
  operation: string;
  property_type: string;
  locality: string;
  neighborhood: string | null;
  surface_covered: string | null;
  bedrooms: string | null;
  expected_price: string | null;
  message: string | null;
  created_at: string;
  updated_at: string | null;
  notes: Note[];
}

export interface LeadPage<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

/** Campos comunes a los tres tipos de leads del panel. */
export interface LeadLike {
  id: number;
  status: LeadStatus;
  name: string;
  email: string;
  phone: string | null;
  message: string | null;
  created_at: string;
  updated_at: string | null;
  notes: Note[];
}

export interface DashboardCounts {
  properties_total: number;
  published: number;
  draft: number;
  archived: number;
  available: number;
  reserved: number;
  sold: number;
  rented: number;
  inquiries_total: number;
  inquiries_new: number;
  valuations_pending: number;
  listings_pending: number;
  featured: number;
}

export interface Dashboard {
  counts: DashboardCounts;
  inquiries_by_status: Record<string, number>;
  last_inquiries: Inquiry[];
  last_properties: PropertySummary[];
}

export interface AcceptedResponse {
  ok: boolean;
  message: string;
  id: number;
}

/** Payload de alta/edición de propiedad (campos del formulario del panel). */
export interface PropertyPayload {
  title: string;
  description: string;
  operation: Operation;
  property_type: PropertyType;
  is_development: boolean;
  price: string | null;
  currency: string;
  price_unit?: PriceUnit | null;
  expenses: string | null;
  commercial_status: CommercialStatus;
  publication_status: PublicationStatus;
  is_featured: boolean;
  country: string;
  province: string;
  department: string | null;
  locality: string | null;
  neighborhood: string | null;
  address: string | null;
  address_is_public: boolean;
  rooms: number | null;
  bedrooms: number | null;
  bathrooms: number | null;
  toilets: number | null;
  garages: number | null;
  antiquity_years: number | null;
  surface_covered: string | null;
  surface_semicovered: string | null;
  surface_total: string | null;
  apto_professional: boolean;
  services: string[];
}
