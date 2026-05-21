import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { AlertTriangle, Activity, CalendarDays } from "lucide-react";
import { AdaptiveBarChart } from "../charts/AdaptiveBarChart";
import { Card } from "../components/Card";
import { KpiCard } from "../components/KpiCard";
import { Loader } from "../components/Loader";
import { api } from "../services/api";
import type { DashboardSummary } from "../types/api";
import { formatValue } from "../utils/format";
import { pageMotion } from "../animations/page";

export function DashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => {
      const response = await api.get<DashboardSummary>("/dashboard");
      return response.data;
    }
  });

  if (isLoading) return <Loader label="Loading dashboard" />;

  if (error || !data) {
    return <Card className="text-rose-100">Dashboard data could not be loaded.</Card>;
  }

  return (
    <motion.section {...pageMotion} className="grid gap-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.22em] text-secondary">FestivaPro Command Center</p>
          <h2 className="mt-2 text-3xl font-bold text-white sm:text-4xl">Nightlife Operations</h2>
        </div>
        <div className="rounded-lg border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-300">
          <CalendarDays className="mr-2 inline h-4 w-4 text-accent" />
          Live event logistics
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {data.metrics.map((metric) => (
          <KpiCard key={metric.label} {...metric} />
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.4fr_0.9fr]">
        <Card>
          <div className="mb-5 flex items-center gap-3">
            <Activity className="h-5 w-5 text-secondary" />
            <h3 className="text-lg font-semibold text-white">Profit Analytics</h3>
          </div>
          <AdaptiveBarChart data={data.revenue_by_event} />
        </Card>

        <Card>
          <div className="mb-5 flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-accent" />
            <h3 className="text-lg font-semibold text-white">Stock Alerts</h3>
          </div>
          <div className="grid gap-3">
            {data.stock_alerts.length === 0 ? (
              <p className="rounded-lg border border-dashed border-white/15 p-6 text-center text-sm text-slate-400">No stock alerts.</p>
            ) : (
              data.stock_alerts.map((item) => (
                <div key={String(item.id)} className="rounded-lg border border-white/10 bg-white/5 p-3">
                  <p className="font-medium text-white">{formatValue(item.name)}</p>
                  <p className="text-sm text-slate-400">
                    {formatValue(item.current_quantity)} / reorder {formatValue(item.reorder_level)}
                  </p>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      <Card>
        <h3 className="mb-5 text-lg font-semibold text-white">Night Activity</h3>
        <div className="grid gap-3 md:grid-cols-2">
          {data.night_activity.length === 0 ? (
            <p className="rounded-lg border border-dashed border-white/15 p-6 text-center text-sm text-slate-400 md:col-span-2">
              No night logs yet.
            </p>
          ) : (
            data.night_activity.map((item, index) => (
              <div key={`${item.title}-${index}`} className="rounded-lg border border-white/10 bg-white/5 p-4">
                <p className="font-medium text-white">{formatValue(item.title)}</p>
                <p className="mt-1 text-sm text-slate-400">{formatValue(item.severity)}</p>
              </div>
            ))
          )}
        </div>
      </Card>
    </motion.section>
  );
}
