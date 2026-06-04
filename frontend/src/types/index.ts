export interface User {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string;
  is_active: boolean;
  is_verified: boolean;
  oauth_provider?: string;
  created_at: string;
  updated_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  description?: string;
  logo_url?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Member {
  id: string;
  user_id: string;
  organization_id: string;
  role: "owner" | "admin" | "analyst" | "viewer";
  created_at: string;
  user_email?: string;
  user_full_name?: string;
}

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  scopes: string;
  is_active: boolean;
  last_used_at?: string;
  expires_at?: string;
  created_at: string;
  full_key?: string;
}

export type WidgetType = "line_chart" | "bar_chart" | "pie_chart" | "kpi_card" | "table";

export interface Widget {
  id: string;
  dashboard_id: string;
  saved_query_id?: string;
  title: string;
  widget_type: WidgetType;
  config: Record<string, unknown>;
  position: { x: number; y: number; w: number; h: number };
  created_at: string;
  updated_at: string;
}

export interface Dashboard {
  id: string;
  organization_id: string;
  created_by_id: string;
  name: string;
  description?: string;
  is_public: boolean;
  public_slug?: string;
  layout: Record<string, unknown>;
  refresh_interval?: number;
  template_type?: string;
  tags: string[];
  widgets?: Widget[];
  created_at: string;
  updated_at: string;
}

export type AlertStatus = "active" | "triggered" | "resolved" | "muted";
export type AlertCondition = "gt" | "lt" | "gte" | "lte" | "eq";

export interface Alert {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  metric_query: Record<string, unknown>;
  condition: AlertCondition;
  threshold: number;
  evaluation_interval_minutes: number;
  status: AlertStatus;
  last_evaluated_at?: string;
  last_triggered_at?: string;
  muted_until?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AlertHistory {
  id: string;
  alert_id: string;
  triggered_at: string;
  resolved_at?: string;
  triggered_value: number;
  threshold: number;
  message?: string;
}

export interface Event {
  id: string;
  organization_id: string;
  event_name: string;
  timestamp: string;
  properties: Record<string, unknown>;
  user_id?: string;
  session_id?: string;
  created_at: string;
}

export interface EventQueryResult {
  data: Array<{ bucket: string; value: number }>;
  total: number;
  query: Record<string, unknown>;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface ApiError {
  code: string;
  message: string;
  details?: unknown;
}
