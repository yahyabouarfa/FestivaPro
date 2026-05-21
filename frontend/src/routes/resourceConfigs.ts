import type { ResourceConfig } from "../types/api";

export const resourceConfigs: Record<string, ResourceConfig> = {
  events: {
    title: "Events",
    endpoint: "/events",
    columns: ["name", "venue", "city", "starts_at", "status", "expected_guests", "budget_mad"],
    fields: [
      { key: "name", label: "Name", required: true },
      { key: "slug", label: "Slug", required: true },
      { key: "venue", label: "Venue", required: true },
      { key: "city", label: "City", required: true },
      { key: "starts_at", label: "Starts At", type: "datetime-local", required: true },
      { key: "ends_at", label: "Ends At", type: "datetime-local" },
      { key: "status", label: "Status", type: "select", options: ["planning", "live", "closed"], required: true },
      { key: "expected_guests", label: "Expected Guests", type: "number" },
      { key: "budget_mad", label: "Budget MAD", type: "number" },
      { key: "notes", label: "Notes", type: "textarea" }
    ]
  },
  bars: {
    title: "Bars",
    endpoint: "/bars",
    columns: ["name", "event_id", "location", "manager_name", "opening_cash_mad", "closing_cash_mad", "status"],
    fields: [
      { key: "event_id", label: "Event ID", type: "number", required: true },
      { key: "name", label: "Name", required: true },
      { key: "location", label: "Location", required: true },
      { key: "manager_name", label: "Manager" },
      { key: "opening_cash_mad", label: "Opening Cash MAD", type: "number" },
      { key: "closing_cash_mad", label: "Closing Cash MAD", type: "number" },
      { key: "status", label: "Status", type: "select", options: ["ready", "open", "closed"], required: true }
    ]
  },
  employees: {
    title: "Employees",
    endpoint: "/employees",
    columns: ["full_name", "phone", "role", "daily_rate_mad", "is_active"],
    fields: [
      { key: "full_name", label: "Full Name", required: true },
      { key: "phone", label: "Phone" },
      { key: "role", label: "Role", type: "select", options: ["manager", "bartender", "cashier", "runner", "security", "logistics"], required: true },
      { key: "daily_rate_mad", label: "Daily Rate MAD", type: "number" },
      { key: "is_active", label: "Active", type: "checkbox" },
      { key: "emergency_contact", label: "Emergency Contact" }
    ]
  },
  stock: {
    title: "Stock",
    endpoint: "/stock",
    columns: ["name", "category", "unit", "current_quantity", "reorder_level", "unit_cost_mad"],
    fields: [
      { key: "event_id", label: "Event ID", type: "number" },
      { key: "bar_id", label: "Bar ID", type: "number" },
      { key: "name", label: "Name", required: true },
      { key: "category", label: "Category", type: "select", options: ["alcohol", "soft_drink", "garnish", "consumable"], required: true },
      { key: "unit", label: "Unit", required: true },
      { key: "opening_quantity", label: "Opening Quantity", type: "number" },
      { key: "current_quantity", label: "Current Quantity", type: "number" },
      { key: "reorder_level", label: "Reorder Level", type: "number" },
      { key: "unit_cost_mad", label: "Unit Cost MAD", type: "number" }
    ]
  },
  equipment: {
    title: "Equipment",
    endpoint: "/equipment",
    columns: ["name", "category", "quantity", "condition", "assigned_to"],
    fields: [
      { key: "event_id", label: "Event ID", type: "number" },
      { key: "name", label: "Name", required: true },
      { key: "category", label: "Category", required: true },
      { key: "quantity", label: "Quantity", type: "number" },
      { key: "condition", label: "Condition", type: "select", options: ["new", "good", "repair", "missing"], required: true },
      { key: "assigned_to", label: "Assigned To" }
    ]
  },
  logistics: {
    title: "Event Logistics",
    endpoint: "/equipment",
    columns: ["name", "category", "quantity", "condition", "assigned_to", "event_id"],
    fields: [
      { key: "event_id", label: "Event ID", type: "number" },
      { key: "name", label: "Logistics Item", required: true },
      { key: "category", label: "Category", type: "select", options: ["sound", "lights", "bar", "stage", "transport", "security"], required: true },
      { key: "quantity", label: "Quantity", type: "number" },
      { key: "condition", label: "Status", type: "select", options: ["new", "good", "repair", "missing"], required: true },
      { key: "assigned_to", label: "Owner" }
    ]
  },
  salaries: {
    title: "Salaries",
    endpoint: "/salaries",
    columns: ["employee_id", "event_id", "amount_mad", "status", "paid_at"],
    fields: [
      { key: "employee_id", label: "Employee ID", type: "number", required: true },
      { key: "event_id", label: "Event ID", type: "number" },
      { key: "amount_mad", label: "Amount MAD", type: "number", required: true },
      { key: "status", label: "Status", type: "select", options: ["pending", "paid", "cancelled"], required: true },
      { key: "paid_at", label: "Paid At", type: "datetime-local" }
    ]
  },
  contributions: {
    title: "Bartender Contributions",
    endpoint: "/contributions",
    columns: ["employee_id", "bar_id", "sales_mad", "tips_mad", "transactions_count"],
    fields: [
      { key: "employee_id", label: "Employee ID", type: "number", required: true },
      { key: "bar_id", label: "Bar ID", type: "number", required: true },
      { key: "sales_mad", label: "Sales MAD", type: "number" },
      { key: "tips_mad", label: "Tips MAD", type: "number" },
      { key: "transactions_count", label: "Transactions", type: "number" }
    ]
  },
  profits: {
    title: "Profits",
    endpoint: "/profits",
    columns: ["event_id", "label", "revenue_mad", "cost_mad", "notes"],
    fields: [
      { key: "event_id", label: "Event ID", type: "number", required: true },
      { key: "label", label: "Label", required: true },
      { key: "revenue_mad", label: "Revenue MAD", type: "number" },
      { key: "cost_mad", label: "Cost MAD", type: "number" },
      { key: "notes", label: "Notes", type: "textarea" }
    ]
  },
  "night-management": {
    title: "Night Management",
    endpoint: "/night-management",
    columns: ["event_id", "severity", "title", "resolved", "created_at"],
    fields: [
      { key: "event_id", label: "Event ID", type: "number", required: true },
      { key: "severity", label: "Severity", type: "select", options: ["info", "warning", "critical"], required: true },
      { key: "title", label: "Title", required: true },
      { key: "details", label: "Details", type: "textarea" },
      { key: "resolved", label: "Resolved", type: "checkbox" }
    ]
  },
  reports: {
    title: "Reports",
    endpoint: "/reports",
    columns: ["title", "report_type", "event_id", "created_at"],
    fields: [
      { key: "event_id", label: "Event ID", type: "number" },
      { key: "title", label: "Title", required: true },
      { key: "report_type", label: "Type", type: "select", options: ["financial", "stock", "staff", "night"], required: true }
    ]
  },
  notifications: {
    title: "Notifications",
    endpoint: "/notifications",
    columns: ["title", "level", "is_read", "created_at"],
    fields: [
      { key: "title", label: "Title", required: true },
      { key: "message", label: "Message", type: "textarea", required: true },
      { key: "level", label: "Level", type: "select", options: ["info", "success", "warning", "critical"], required: true },
      { key: "is_read", label: "Read", type: "checkbox" }
    ]
  }
};
