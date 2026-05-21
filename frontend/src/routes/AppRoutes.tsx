import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "../layouts/AppShell";
import { AuditLogsPage } from "../pages/AuditLogsPage";
import { DashboardPage } from "../pages/DashboardPage";
import { LoginPage } from "../pages/LoginPage";
import { ResourcePage } from "../pages/ResourcePage";
import { ProtectedRoute } from "./ProtectedRoute";
import { resourceConfigs } from "./resourceConfigs";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          {Object.entries(resourceConfigs).map(([key, config]) => (
            <Route key={key} path={key} element={<ResourcePage config={config} />} />
          ))}
          <Route path="audit-logs" element={<AuditLogsPage />} />
          <Route path="analytics" element={<DashboardPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
