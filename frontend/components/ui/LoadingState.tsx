import React from 'react';
import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  label?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ label = 'Processing safety dataset...' }) => {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center">
      <Loader2 className="w-6 h-6 text-industrial-400 animate-spin mb-3" />
      <span className="text-xs font-sans font-bold text-industrial-500 tracking-wider uppercase">
        {label}
      </span>
    </div>
  );
};
