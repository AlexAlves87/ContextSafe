/**
 * ConfidenceBadge - Confidence score display with color coding
 *
 * Traceability:
 * - Contract: CNT-UI-COMP-013
 */

import React from 'react';
import clsx from 'clsx';

interface ConfidenceBadgeProps {
  score: number;
  showLabel?: boolean;
  className?: string;
}

function getConfidenceLevel(score: number): {
  label: string;
  color: string;
  bg: string;
} {
  if (score >= 0.9) {
    return {
      label: 'Alto',
      color: 'text-success-700 dark:text-success-300',
      bg: 'bg-success-100 dark:bg-success-900/30',
    };
  }
  if (score >= 0.7) {
    return {
      label: 'Medio',
      color: 'text-warning-700 dark:text-warning-300',
      bg: 'bg-warning-100 dark:bg-warning-900/30',
    };
  }
  return {
    label: 'Bajo',
    color: 'text-danger-700 dark:text-danger-300',
    bg: 'bg-danger-100 dark:bg-danger-900/30',
  };
}

export const ConfidenceBadge: React.FC<ConfidenceBadgeProps> = ({
  score,
  showLabel = false,
  className,
}) => {
  const clampedScore = Math.min(1, Math.max(0, score));
  const percentage = Math.round(clampedScore * 100);
  const { label, color, bg } = getConfidenceLevel(clampedScore);

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium',
        bg,
        color,
        className
      )}
      title={`Confianza: ${percentage}%`}
    >
      {percentage}%
      {showLabel && <span className="opacity-75">({label})</span>}
    </span>
  );
};

export default ConfidenceBadge;
