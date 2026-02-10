/**
 * LoadingSpinner - Loading indicator
 *
 * Traceability:
 * - Contract: CNT-UI-COMP-011
 */

import React from 'react';
import clsx from 'clsx';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  label?: string;
  className?: string;
}

const SIZE_CLASSES = {
  sm: 'w-4 h-4',
  md: 'w-8 h-8',
  lg: 'w-12 h-12',
};

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  label,
  className,
}) => {
  return (
    <div
      role="status"
      aria-label={label || 'Cargando'}
      className={clsx('flex flex-col items-center gap-3', className)}
    >
      <svg
        className={clsx('animate-spin text-primary-500', SIZE_CLASSES[size])}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
      {label && (
        <span className="text-sm text-gray-500 dark:text-gray-400">{label}</span>
      )}
      <span className="sr-only">{label || 'Cargando'}</span>
    </div>
  );
};

export default LoadingSpinner;
