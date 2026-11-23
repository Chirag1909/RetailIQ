import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorAlertProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  title = 'Data Retrieval Error',
  message,
  onRetry,
}) => {
  return (
    <div className="bg-rose-950/40 border border-rose-800/60 rounded-lg p-5 text-rose-200 my-4 flex items-start gap-4">
      <AlertTriangle className="w-5 h-5 text-rose-400 mt-0.5 shrink-0" />
      <div className="flex-1">
        <h4 className="text-sm font-semibold text-rose-100">{title}</h4>
        <p className="text-xs text-rose-300 mt-1 leading-relaxed">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-rose-900/60 hover:bg-rose-800/80 text-rose-100 rounded border border-rose-700/50 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Retry Request
          </button>
        )}
      </div>
    </div>
  );
};
