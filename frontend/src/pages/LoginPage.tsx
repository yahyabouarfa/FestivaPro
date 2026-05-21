import { FormEvent, useState } from "react";
import { motion } from "framer-motion";
import { Navigate, useNavigate } from "react-router-dom";
import { LogIn } from "lucide-react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { useAuth } from "../context/AuthContext";

export function LoginPage() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    const form = new FormData(event.currentTarget);
    try {
      await login(String(form.get("email")), String(form.get("password")));
      navigate("/", { replace: true });
    } catch {
      setError("Invalid email or password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center p-4">
      <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-md">
        <div className="mb-8 flex justify-center">
          <img src="/FestivaPro.png" alt="FestivaPro" className="h-24 w-24 rounded-lg object-contain shadow-glow" />
        </div>
        <Card>
          <h1 className="text-center text-2xl font-bold text-white">FESTIVAPRO EVENT MANAGEMENT</h1>
          <form onSubmit={handleSubmit} className="mt-8 grid gap-4">
            <label className="grid gap-2 text-sm text-slate-300">
              Email
              <input
                name="email"
                type="email"
                autoComplete="email"
                required
                className="focus-ring rounded-lg border border-white/10 bg-night/70 px-3 py-3 text-white"
              />
            </label>
            <label className="grid gap-2 text-sm text-slate-300">
              Password
              <input
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="focus-ring rounded-lg border border-white/10 bg-night/70 px-3 py-3 text-white"
              />
            </label>
            {error ? <p className="rounded-lg border border-rose-400/30 bg-rose-500/10 p-3 text-sm text-rose-100">{error}</p> : null}
            <Button loading={loading} className="mt-2 w-full">
              <LogIn className="h-4 w-4" />
              Sign in
            </Button>
          </form>
        </Card>
      </motion.div>
    </main>
  );
}
