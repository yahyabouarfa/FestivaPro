export type ID = number;

export type ApiRecord = Record<string, unknown> & {
  id: ID;
  created_at?: string;
  updated_at?: string;
};

export type User = {
  id: number;
  email: string;
  full_name: string;
  role: string;
};

export type DashboardSummary = {
  metrics: Array<{ label: string; value: number | string; trend: number }>;
  revenue_by_event: Array<{ name: string; profit: number | string }>;
  stock_alerts: Array<Record<string, unknown>>;
  night_activity: Array<Record<string, unknown>>;
};

export type ResourceField = {
  key: string;
  label: string;
  type?: "text" | "number" | "datetime-local" | "textarea" | "checkbox" | "select";
  options?: string[];
  required?: boolean;
};

export type ResourceConfig = {
  title: string;
  endpoint: string;
  fields: ResourceField[];
  columns: string[];
};
