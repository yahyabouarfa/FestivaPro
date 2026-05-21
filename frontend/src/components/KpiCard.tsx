import { motion } from "framer-motion";
import { TrendingUp } from "lucide-react";
import { Card } from "./Card";
import { formatValue } from "../utils/format";

export function KpiCard({ label, value, trend }: { label: string; value: number | string; trend: number }) {
  return (
    <motion.div whileHover={{ y: -3 }} transition={{ type: "spring", stiffness: 260, damping: 18 }}>
      <Card className="min-h-32">
        <div className="flex items-start justify-between gap-3">
          <p className="text-sm font-medium text-slate-400">{label}</p>
          <span className="rounded-lg border border-white/10 bg-white/5 p-2 text-secondary">
            <TrendingUp className="h-4 w-4" />
          </span>
        </div>
        <p className="mt-5 text-2xl font-bold text-white sm:text-3xl">{formatValue(value)}</p>
        <p className="mt-2 text-sm text-slate-400">{trend > 0 ? `+${trend}%` : `${trend}%`}</p>
      </Card>
    </motion.div>
  );
}
