import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'System Error',
  message = 'An unexpected error occurred while communicating with the backend safety engine.',
  onRetry,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center border border-industrial-800 rounded-sm bg-transparent">
      <AlertTriangle className="w-8 h-8 text-black mb-2" />
      <h4 className="text-sm font-sans font-bold text-black uppercase tracking-wide">
        {title}
      </h4>
      <p className="text-xs text-industrial-500 max-w-md mt-1 mb-4 font-sans">
        {message}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-sm text-xs font-sans bg-white hover:bg-industrial-900 text-black border border-industrial-800 transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry Connection
        </button>
      )}
    </div>
  );
};
