/**
 * DiffViewer - Text diff visualization
 *
 * Traceability:
 * - Contract: CNT-UI-COMP-015
 */

import React, { useMemo } from 'react';
import clsx from 'clsx';

interface DiffViewerProps {
  original: string;
  modified: string;
  className?: string;
}

interface DiffSegment {
  type: 'unchanged' | 'removed' | 'added';
  text: string;
}

/**
 * Simple word-level diff algorithm
 */
function computeDiff(original: string, modified: string): DiffSegment[] {
  const originalWords = original.split(/(\s+)/);
  const modifiedWords = modified.split(/(\s+)/);
  const segments: DiffSegment[] = [];

  let i = 0;
  let j = 0;

  while (i < originalWords.length || j < modifiedWords.length) {
    const origWord = originalWords[i] || '';
    const modWord = modifiedWords[j] || '';

    if (origWord === modWord) {
      // Unchanged
      if (origWord) {
        segments.push({ type: 'unchanged', text: origWord });
      }
      i++;
      j++;
    } else if (origWord && !modifiedWords.slice(j).includes(origWord)) {
      // Removed (not found ahead in modified)
      segments.push({ type: 'removed', text: origWord });
      i++;
    } else if (modWord && !originalWords.slice(i).includes(modWord)) {
      // Added (not found ahead in original)
      segments.push({ type: 'added', text: modWord });
      j++;
    } else {
      // Different words - show as removed then added
      if (origWord) {
        segments.push({ type: 'removed', text: origWord });
        i++;
      }
      if (modWord) {
        segments.push({ type: 'added', text: modWord });
        j++;
      }
    }
  }

  return segments;
}

export const DiffViewer: React.FC<DiffViewerProps> = ({
  original,
  modified,
  className,
}) => {
  const diffSegments = useMemo(
    () => computeDiff(original, modified),
    [original, modified]
  );

  const stats = useMemo(() => {
    let added = 0;
    let removed = 0;
    diffSegments.forEach((seg) => {
      if (seg.type === 'added') added++;
      if (seg.type === 'removed') removed++;
    });
    return { added, removed };
  }, [diffSegments]);

  return (
    <div className={clsx('space-y-4', className)}>
      {/* Stats header */}
      <div className="flex items-center gap-4 text-sm">
        <span className="text-gray-500 dark:text-gray-400">Cambios:</span>
        <span className="flex items-center gap-1 text-danger-600 dark:text-danger-400">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
              clipRule="evenodd"
            />
          </svg>
          {stats.removed} eliminados
        </span>
        <span className="flex items-center gap-1 text-success-600 dark:text-success-400">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
              clipRule="evenodd"
            />
          </svg>
          {stats.added} agregados
        </span>
      </div>

      {/* Diff content */}
      <div
        className={clsx(
          'p-4 rounded-lg border',
          'bg-gray-50 dark:bg-gray-800',
          'border-gray-200 dark:border-gray-700'
        )}
      >
        <pre className="text-sm whitespace-pre-wrap font-mono leading-relaxed">
          {diffSegments.map((segment, index) => {
            switch (segment.type) {
              case 'removed':
                return (
                  <span
                    key={index}
                    className="bg-danger-100 dark:bg-danger-900/30 text-danger-700 dark:text-danger-300 line-through"
                  >
                    {segment.text}
                  </span>
                );
              case 'added':
                return (
                  <span
                    key={index}
                    className="bg-success-100 dark:bg-success-900/30 text-success-700 dark:text-success-300"
                  >
                    {segment.text}
                  </span>
                );
              default:
                return (
                  <span
                    key={index}
                    className="text-gray-700 dark:text-gray-300"
                  >
                    {segment.text}
                  </span>
                );
            }
          })}
        </pre>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-6 text-xs text-gray-500 dark:text-gray-400">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded bg-danger-100 dark:bg-danger-900/30 border border-danger-300" />
          <span>Eliminado (original)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded bg-success-100 dark:bg-success-900/30 border border-success-300" />
          <span>Agregado (anonimizado)</span>
        </div>
      </div>
    </div>
  );
};

export default DiffViewer;
