/**
 * ProcessingProgress - Processing progress bar with percentage and stage
 *
 * Traceability:
 * - Contract: CNT-UI-COMP-003
 * - Binding: UI-BIND-003
 */

import React from 'react';
import clsx from 'clsx';
import type { ProcessingStage } from '@/types';

interface ProcessingProgressProps {
  progress: number;
  stage: ProcessingStage;
  error?: string;
  className?: string;
}

const STAGE_CONFIG: Record<ProcessingStage, { label: string; color: string }> = {
  ingesting: {
    label: 'Extrayendo texto',
    color: 'bg-blue-500',
  },
  detecting: {
    label: 'Detectando PII',
    color: 'bg-yellow-500',
  },
  anonymizing: {
    label: 'Anonimizando',
    color: 'bg-purple-500',
  },
};

export const ProcessingProgress: React.FC<ProcessingProgressProps> = ({
  progress,
  stage,
  error,
  className,
}) => {
  const config = STAGE_CONFIG[stage];
  const clampedProgress = Math.min(100, Math.max(0, progress));

  if (error) {
    return (
      <div className={clsx('p-4 bg-danger-50 dark:bg-danger-900/20 rounded-lg', className)}>
        <div className="flex items-center gap-3">
          <svg
            className="w-6 h-6 text-danger-500 flex-shrink-0"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
          <div>
            <h4 className="text-sm font-medium text-danger-700 dark:text-danger-400">
              Error en el procesamiento
            </h4>
            <p className="text-sm text-danger-600 dark:text-danger-500">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={clsx('p-4', className)}>
      {/* Header with stage and percentage */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {/* Animated spinner */}
          <svg
            className="w-5 h-5 text-primary-500 animate-spin"
            fill="none"
            viewBox="0 0 24 24"
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
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {config.label}
          </span>
        </div>
        <span className="text-sm font-semibold text-gray-900 dark:text-white">
          {Math.round(clampedProgress)}%
        </span>
      </div>

      {/* Progress bar */}
      <div
        role="progressbar"
        aria-valuenow={clampedProgress}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${config.label}: ${Math.round(clampedProgress)}%`}
        className="h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden"
      >
        <div
          className={clsx(
            'h-full transition-all duration-300 ease-out rounded-full',
            config.color
          )}
          style={{ width: `${clampedProgress}%` }}
        />
      </div>

      {/* Stage steps */}
      <div className="flex justify-between mt-4">
        {(['ingesting', 'detecting', 'anonymizing'] as ProcessingStage[]).map(
          (s, index) => {
            const isActive = s === stage;
            const isPast =
              (stage === 'detecting' && s === 'ingesting') ||
              (stage === 'anonymizing' && ['ingesting', 'detecting'].includes(s));

            return (
              <div key={s} className="flex items-center gap-2">
                {/* Step number/check */}
                <div
                  className={clsx(
                    'w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium',
                    {
                      'bg-primary-500 text-white': isActive,
                      'bg-success-500 text-white': isPast,
                      'bg-gray-200 dark:bg-gray-700 text-gray-500': !isActive && !isPast,
                    }
                  )}
                >
                  {isPast ? (
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  ) : (
                    index + 1
                  )}
                </div>
                {/* Step label */}
                <span
                  className={clsx('text-xs hidden sm:inline', {
                    'text-primary-600 dark:text-primary-400 font-medium': isActive,
                    'text-success-600 dark:text-success-400': isPast,
                    'text-gray-500': !isActive && !isPast,
                  })}
                >
                  {STAGE_CONFIG[s].label}
                </span>
              </div>
            );
          }
        )}
      </div>
    </div>
  );
};

export default ProcessingProgress;
