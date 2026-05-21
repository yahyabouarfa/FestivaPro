import { Edit3, Trash2 } from "lucide-react";
import type { ApiRecord } from "../types/api";
import { formatValue } from "../utils/format";
import { Button } from "./Button";

export function DataTable({
  rows,
  columns,
  onEdit,
  onDelete
}: {
  rows: ApiRecord[];
  columns: string[];
  onEdit?: (row: ApiRecord) => void;
  onDelete?: (row: ApiRecord) => void;
}) {
  const hasActions = Boolean(onEdit || onDelete);

  if (rows.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-white/15 p-8 text-center text-sm text-slate-400">
        No records yet.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-white/10">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-white/10 text-left text-sm">
          <thead className="bg-white/5 text-xs uppercase tracking-[0.18em] text-slate-400">
            <tr>
              {columns.map((column) => (
                <th key={column} className="px-4 py-3 font-semibold">
                  {column.replaceAll("_", " ")}
                </th>
              ))}
              {hasActions ? <th className="px-4 py-3 text-right font-semibold">Actions</th> : null}
            </tr>
          </thead>
          <tbody className="divide-y divide-white/10">
            {rows.map((row) => (
              <tr key={row.id} className="transition hover:bg-white/[0.04]">
                {columns.map((column) => (
                  <td key={column} className="max-w-[18rem] px-4 py-3 text-slate-200">
                    <span className="line-clamp-2">{formatValue(row[column])}</span>
                  </td>
                ))}
                {hasActions ? (
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-2">
                      {onEdit ? (
                        <Button variant="ghost" onClick={() => onEdit(row)} aria-label="Edit" className="h-9 w-9 p-0">
                          <Edit3 className="h-4 w-4" />
                        </Button>
                      ) : null}
                      {onDelete ? (
                        <Button variant="danger" onClick={() => onDelete(row)} aria-label="Delete" className="h-9 w-9 p-0">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      ) : null}
                    </div>
                  </td>
                ) : null}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
