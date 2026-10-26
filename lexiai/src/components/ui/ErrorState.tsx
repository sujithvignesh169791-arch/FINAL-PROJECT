import { AlertTriangle } from "lucide-react";

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ title = "Something went wrong", message, onRetry }: ErrorStateProps) {
  return (
    <div className="p-6 rounded-2xl border border-burgundy/30 bg-burgundy/10 flex items-start gap-4">
      <div className="p-2 rounded-full bg-burgundy/20 text-burgundy shrink-0">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <div>
        <h3 className="text-lg font-medium text-ivory mb-1">{title}</h3>
        <p className="text-sm text-white/60 mb-4">{message}</p>
        
        {onRetry && (
          <button 
            onClick={onRetry}
            className="px-4 py-2 rounded-lg bg-white/5 border border-white/10 text-ivory text-sm font-medium hover:bg-white/10 transition-colors"
          >
            Try Again
          </button>
        )}
      </div>
    </div>
  );
}
