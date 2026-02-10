/**
 * SafetyLatchIndicator - Shows lock/unlock status for export.
 */

import React from 'react';
import clsx from 'clsx';

interface SafetyLatchIndicatorProps {
  canExport: boolean;
  blockedReason?: string;
  compact?: boolean;
}

export const SafetyLatchIndicator: React.FC<SafetyLatchIndicatorProps> = ({
  canExport,
  blockedReason,
  compact = false,
}) => {
  if (compact) {
    return (
      <span
        className={clsx(
          'inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold uppercase',
          canExport
            ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-800 dark:text-emerald-200'
            : 'bg-red-100 text-red-700 dark:bg-red-800 dark:text-red-200'
        )}
        title={canExport ? 'Exportación disponible' : blockedReason}
      >
        {canExport ? (
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z" />
          </svg>
        ) : (
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        )}
        {canExport ? 'OK' : 'BLOQUEADO'}
      </span>
    );
  }

  return (
    <div className={clsx(
      'flex items-center gap-2 px-3 py-2 rounded-lg border text-xs',
      canExport
        ? 'bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-900/20 dark:border-emerald-800 dark:text-emerald-300'
        : 'bg-red-50 border-red-200 text-red-700 dark:bg-red-900/20 dark:border-red-800 dark:text-red-300'
    )}>
      {canExport ? (
        <>
          <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 11V7a4 4 0 118 0m-4 8v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2z" />
          </svg>
          <span className="font-medium">Revisión completada — Exportación disponible</span>
        </>
      ) : (
        <>
          <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          <span className="font-medium">{blockedReason || 'Exportación bloqueada hasta completar la revisión'}</span>
        </>
      )}
    </div>
  );
};

export default SafetyLatchIndicator;
