import type { ResourceField } from "../types/api";

export function FormField({ field, defaultValue }: { field: ResourceField; defaultValue?: unknown }) {
  const base =
    "focus-ring w-full rounded-lg border border-white/10 bg-night/70 px-3 py-2.5 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-secondary";

  if (field.type === "textarea") {
    return (
      <label className="grid gap-2 text-sm text-slate-300">
        {field.label}
        <textarea name={field.key} defaultValue={String(defaultValue ?? "")} required={field.required} className={`${base} min-h-28`} />
      </label>
    );
  }

  if (field.type === "select") {
    return (
      <label className="grid gap-2 text-sm text-slate-300">
        {field.label}
        <select name={field.key} defaultValue={String(defaultValue ?? field.options?.[0] ?? "")} required={field.required} className={base}>
          {field.options?.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
    );
  }

  if (field.type === "checkbox") {
    return (
      <label className="flex items-center gap-3 rounded-lg border border-white/10 bg-night/60 px-3 py-2.5 text-sm text-slate-300">
        <input name={field.key} type="checkbox" defaultChecked={Boolean(defaultValue)} className="h-4 w-4 accent-pink-500" />
        {field.label}
      </label>
    );
  }

  const normalizedValue =
    field.type === "datetime-local" && typeof defaultValue === "string" ? defaultValue.slice(0, 16) : String(defaultValue ?? "");

  return (
    <label className="grid gap-2 text-sm text-slate-300">
      {field.label}
      <input
        name={field.key}
        type={field.type ?? "text"}
        defaultValue={normalizedValue}
        required={field.required}
        className={base}
      />
    </label>
  );
}
