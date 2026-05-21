import { AlertCircle, CheckCircle2 } from "lucide-react";

export function NotificationToast({ type, message }: { type: "success" | "error"; message: string }) {
  const Icon = type === "success" ? CheckCircle2 : AlertCircle;
  return (
    <div className="fixed bottom-5 right-5 z-50 flex max-w-sm items-center gap-3 rounded-lg border border-white/10 bg-surface/95 p-4 text-sm text-white shadow-glass">
      <Icon className={type === "success" ? "h-5 w-5 text-emerald-400" : "h-5 w-5 text-rose-400"} />
      <span>{message}</span>
    </div>
  );
}
