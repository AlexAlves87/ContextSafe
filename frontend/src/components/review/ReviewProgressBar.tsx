/**
 * ReviewProgressBar - Segmented progress bar showing review completion by zone.
 */

import React from 'react';
import type { ReviewSummary } from '@/types';

interface ReviewProgressBarProps {
  summary: ReviewSummary;
}

export const ReviewProgressBar: React.FC<ReviewProgressBarProps> = ({ summary }) => {
  const { total, reviewed, pendingAmberRed, reviewPercentage, canExport } = summary;
  const byZone = summary.byZone ?? { GREEN: 0, AMBER: 0, RED: 0 };

  if (total === 0) return null;

  return (
    <div className="w-full space-y-2">
      {/* Header */}
      <div className="flex items-center justify-between text-xs">
        <span className="font-semibold text-foreground uppercase tracking-wider">
          Progreso de revisión: {reviewed}/{total} ({reviewPercentage}%)
        </span>
        {canExport ? (
          <span className="text-emerald-600 dark:text-emerald-400 font-medium">
            Exportación disponible
          </span>
        ) : (
          <span className="text-amber-600 dark:text-amber-400 font-medium">
            {pendingAmberRed} ámbar/rojo pendientes
          </span>
        )}
      </div>

      {/* Progress bar */}
      <div className="w-full h-2.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden flex">
        {/* Green segment */}
        {byZone.GREEN > 0 && (
          <div
            className="h-full bg-emerald-500 transition-all duration-300"
            style={{ width: `${(byZone.GREEN / total) * 100}%` }}
          />
        )}
        {/* Amber segment */}
        {byZone.AMBER > 0 && (
          <div
            className="h-full bg-amber-500 transition-all duration-300"
            style={{ width: `${(byZone.AMBER / total) * 100}%` }}
          />
        )}
        {/* Red segment */}
        {byZone.RED > 0 && (
          <div
            className="h-full bg-red-500 transition-all duration-300"
            style={{ width: `${(byZone.RED / total) * 100}%` }}
          />
        )}
      </div>

      {/* Zone legend */}
      <div className="flex items-center gap-4 text-[10px] text-muted-foreground">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
          Verde ({byZone.GREEN})
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-amber-500 inline-block" />
          Ámbar ({byZone.AMBER})
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-red-500 inline-block" />
          Rojo ({byZone.RED})
        </span>
      </div>
    </div>
  );
};

export default ReviewProgressBar;
