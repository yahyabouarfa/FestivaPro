import type { HTMLAttributes } from "react";

export function Card({ className = "", ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={`glass-panel rounded-lg p-5 ${className}`} {...props} />;
}
