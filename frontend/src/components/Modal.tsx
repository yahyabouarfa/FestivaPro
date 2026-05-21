import type { ReactNode } from "react";
import { X } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "./Button";

export function Modal({
  title,
  children,
  onClose
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 12 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        className="glass-panel max-h-[90vh] w-full max-w-2xl overflow-auto rounded-lg p-5"
      >
        <div className="mb-5 flex items-center justify-between gap-4">
          <h2 className="text-lg font-semibold text-white">{title}</h2>
          <Button variant="ghost" onClick={onClose} aria-label="Close" className="h-10 w-10 p-0">
            <X className="h-4 w-4" />
          </Button>
        </div>
        {children}
      </motion.div>
    </div>
  );
}
