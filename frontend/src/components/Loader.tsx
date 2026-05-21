import { Loader2 } from "lucide-react";

export function Loader({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex min-h-40 items-center justify-center gap-3 text-slate-300">
      <Loader2 className="h-5 w-5 animate-spin text-secondary" />
      <span>{label}</span>
    </div>
  );
}
