import { FormEvent, useState } from "react";
import { motion } from "framer-motion";
import { Plus } from "lucide-react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { DataTable } from "../components/DataTable";
import { FormField } from "../components/FormField";
import { Loader } from "../components/Loader";
import { Modal } from "../components/Modal";
import { NotificationToast } from "../components/NotificationToast";
import { useResource } from "../hooks/useResource";
import type { ApiRecord, ResourceConfig } from "../types/api";
import { toApiPayload } from "../utils/format";
import { pageMotion } from "../animations/page";

export function ResourcePage({ config }: { config: ResourceConfig }) {
  const resource = useResource(config.endpoint);
  const [editing, setEditing] = useState<ApiRecord | null>(null);
  const [open, setOpen] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error"; message: string } | null>(null);

  function showToast(type: "success" | "error", message: string) {
    setToast({ type, message });
    window.setTimeout(() => setToast(null), 2600);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const base = toApiPayload(Object.fromEntries(form.entries()));
    for (const field of config.fields) {
      if (field.type === "checkbox") base[field.key] = form.has(field.key);
    }
    try {
      if (editing) await resource.update.mutateAsync({ id: editing.id, payload: base });
      else await resource.create.mutateAsync(base);
      setOpen(false);
      setEditing(null);
      showToast("success", `${config.title} saved.`);
    } catch {
      showToast("error", `${config.title} could not be saved.`);
    }
  }

  async function handleDelete(row: ApiRecord) {
    try {
      await resource.remove.mutateAsync(row.id);
      showToast("success", `${config.title} deleted.`);
    } catch {
      showToast("error", `${config.title} could not be deleted.`);
    }
  }

  return (
    <motion.section {...pageMotion} className="grid gap-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-secondary">Operations</p>
          <h2 className="mt-2 text-3xl font-bold text-white">{config.title}</h2>
        </div>
        <Button
          onClick={() => {
            setEditing(null);
            setOpen(true);
          }}
        >
          <Plus className="h-4 w-4" />
          New
        </Button>
      </div>

      <Card>
        {resource.isLoading ? (
          <Loader label={`Loading ${config.title.toLowerCase()}`} />
        ) : (
          <DataTable
            rows={resource.data ?? []}
            columns={config.columns}
            onEdit={(row) => {
              setEditing(row);
              setOpen(true);
            }}
            onDelete={handleDelete}
          />
        )}
      </Card>

      {open ? (
        <Modal title={editing ? `Edit ${config.title}` : `New ${config.title}`} onClose={() => setOpen(false)}>
          <form onSubmit={handleSubmit} className="grid gap-4 sm:grid-cols-2">
            {config.fields.map((field) => (
              <div key={field.key} className={field.type === "textarea" ? "sm:col-span-2" : ""}>
                <FormField field={field} defaultValue={editing?.[field.key]} />
              </div>
            ))}
            <div className="flex justify-end gap-3 sm:col-span-2">
              <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button loading={resource.create.isPending || resource.update.isPending}>Save</Button>
            </div>
          </form>
        </Modal>
      ) : null}

      {toast ? <NotificationToast {...toast} /> : null}
    </motion.section>
  );
}
