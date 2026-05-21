import type { ButtonHTMLAttributes } from "react";
import { Loader2 } from "lucide-react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost" | "danger";
  loading?: boolean;
};

const variants = {
  primary: "bg-[image:var(--gradient-neon)] text-white shadow-glow",
  ghost: "border border-white/10 bg-white/5 text-slate-100 hover:bg-white/10",
  danger: "border border-rose-400/30 bg-rose-500/15 text-rose-100 hover:bg-rose-500/25"
};

export function Button({ children, className = "", variant = "primary", loading, disabled, ...props }: ButtonProps) {
  return (
    <button
      className={`focus-ring inline-flex min-h-10 items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition duration-200 hover:translate-y-[-1px] disabled:cursor-not-allowed disabled:opacity-60 ${variants[variant]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
      {children}
    </button>
  );
}
