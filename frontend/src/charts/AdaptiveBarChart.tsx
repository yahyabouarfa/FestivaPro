import { motion } from "framer-motion";
import { formatValue } from "../utils/format";

export function AdaptiveBarChart({ data }: { data: Array<{ name: string; profit: number | string }> }) {
  const numeric = data.map((item) => ({ ...item, profit: Number(item.profit) || 0 }));
  const max = Math.max(...numeric.map((item) => Math.abs(item.profit)), 1);

  if (numeric.length === 0) {
    return <div className="rounded-lg border border-dashed border-white/15 p-8 text-center text-sm text-slate-400">No analytics yet.</div>;
  }

  return (
    <div className="grid gap-4">
      {numeric.map((item, index) => (
        <div key={item.name} className="grid gap-2">
          <div className="flex items-center justify-between gap-4 text-sm">
            <span className="font-medium text-slate-200">{item.name}</span>
            <span className="text-slate-400">{formatValue(item.profit)} MAD</span>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-white/10">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${Math.max(6, (Math.abs(item.profit) / max) * 100)}%` }}
              transition={{ delay: index * 0.05, duration: 0.6 }}
              className="h-full rounded-full bg-[image:var(--gradient-neon)] shadow-glow"
            />
          </div>
        </div>
      ))}
    </div>
  );
}
