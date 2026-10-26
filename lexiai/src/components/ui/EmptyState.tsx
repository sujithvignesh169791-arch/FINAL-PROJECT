import { LucideIcon } from "lucide-react";
import { motion } from "framer-motion";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-12 glass rounded-2xl border border-white/5 border-dashed bg-white/5 text-center">
      <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4 border border-white/10">
        <Icon className="w-8 h-8 text-white/30" />
      </div>
      <h3 className="text-lg font-medium text-ivory mb-2">{title}</h3>
      <p className="text-sm text-white/50 max-w-sm mx-auto mb-6">{description}</p>
      
      {action && (
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={action.onClick}
          className="bg-gold text-charcoal font-medium px-6 py-2.5 rounded-lg hover:bg-gold/90 transition-colors shadow-[0_0_15px_rgba(212,175,55,0.2)]"
        >
          {action.label}
        </motion.button>
      )}
    </div>
  );
}
