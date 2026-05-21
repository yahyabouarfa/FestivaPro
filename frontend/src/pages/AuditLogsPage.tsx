import { motion } from "framer-motion";
import { Card } from "../components/Card";
import { DataTable } from "../components/DataTable";
import { Loader } from "../components/Loader";
import { useResource } from "../hooks/useResource";
import { pageMotion } from "../animations/page";

export function AuditLogsPage() {
  const resource = useResource("/audit-logs");

  return (
    <motion.section {...pageMotion} className="grid gap-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.22em] text-secondary">Governance</p>
        <h2 className="mt-2 text-3xl font-bold text-white">Audit Logs</h2>
      </div>
      <Card>
        {resource.isLoading ? (
          <Loader label="Loading audit logs" />
        ) : (
          <DataTable
            rows={resource.data ?? []}
            columns={["action", "entity", "entity_id", "user_id", "created_at"]}
          />
        )}
      </Card>
    </motion.section>
  );
}
