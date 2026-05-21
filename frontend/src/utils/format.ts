export function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") return new Intl.NumberFormat("en-US").format(value);
  if (typeof value === "string" && /^\d{4}-\d{2}-\d{2}T/.test(value)) {
    return new Intl.DateTimeFormat("en-US", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
  }
  return String(value);
}

export function toApiPayload(payload: Record<string, FormDataEntryValue>): Record<string, unknown> {
  return Object.fromEntries(
    Object.entries(payload).map(([key, value]) => {
      if (value === "") return [key, null];
      if (value === "on") return [key, true];
      const numeric = Number(value);
      if (/(_mad|quantity|count|guests|level|rate|cost|revenue|tips|sales|cash|event_id|bar_id|employee_id)$/.test(key)) {
        return [key, Number.isNaN(numeric) ? value : numeric];
      }
      return [key, value];
    })
  );
}
