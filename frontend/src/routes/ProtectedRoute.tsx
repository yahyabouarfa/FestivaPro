import { Navigate, Outlet } from "react-router-dom";
import { Loader } from "../components/Loader";
import { useAuth } from "../context/AuthContext";

export function ProtectedRoute() {
  const { user, loading } = useAuth();
  if (loading) return <Loader label="Opening FestivaPro" />;
  if (!user) return <Navigate to="/login" replace />;
  return <Outlet />;
}
