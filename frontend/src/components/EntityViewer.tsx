/**
 * EntityViewer - Highlighted PII entities in text with tooltips
 *
 * Traceability:
 * - Contract: CNT-UI-COMP-004
 * - Binding: UI-BIND-004
 */

import React, { useMemo, useState } from 'react';
import clsx from 'clsx';
import type { DetectedEntity, PiiCategory } from '@/types';
import { PII_CATEGORY_LABELS } from '@/types';
import { CategoryChip } from './CategoryChip';
import { ConfidenceBadge } from './ConfidenceBadge';

interface EntityViewerProps {
  text: string;
  entities: DetectedEntity[];
  onEntityClick?: (entityId: string) => void;
  highlightCategory?: PiiCategory;
  className?: string;
}

const CATEGORY_COLORS: Record<PiiCategory, string> = {
  person_name: 'bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-700',
  organization: 'bg-purple-100 dark:bg-purple-900/30 border-purple-300 dark:border-purple-700',
  address: 'bg-green-100 dark:bg-green-900/30 border-green-300 dark:border-green-700',
  dni: 'bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-700',
  nie: 'bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-700',
  cif: 'bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-700',
  nss: 'bg-amber-100 dark:bg-amber-900/30 border-amber-300 dark:border-amber-700',
  dni_nie: 'bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-700',
  passport: 'bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-700',
  phone: 'bg-yellow-100 dark:bg-yellow-900/30 border-yellow-300 dark:border-yellow-700',
  email: 'bg-cyan-100 dark:bg-cyan-900/30 border-cyan-300 dark:border-cyan-700',
  iban: 'bg-orange-100 dark:bg-orange-900/30 border-orange-300 dark:border-orange-700',
  bank_account: 'bg-orange-100 dark:bg-orange-900/30 border-orange-300 dark:border-orange-700',
  credit_card: 'bg-orange-100 dark:bg-orange-900/30 border-orange-300 dark:border-orange-700',
  date: 'bg-pink-100 dark:bg-pink-900/30 border-pink-300 dark:border-pink-700',
  date_of_birth: 'bg-pink-100 dark:bg-pink-900/30 border-pink-300 dark:border-pink-700',
  location: 'bg-green-100 dark:bg-green-900/30 border-green-300 dark:border-green-700',
  medical_record: 'bg-rose-100 dark:bg-rose-900/30 border-rose-300 dark:border-rose-700',
  license_plate: 'bg-indigo-100 dark:bg-indigo-900/30 border-indigo-300 dark:border-indigo-700',
  social_security: 'bg-amber-100 dark:bg-amber-900/30 border-amber-300 dark:border-amber-700',
  ip_address: 'bg-slate-100 dark:bg-slate-900/30 border-slate-300 dark:border-slate-700',
  url: 'bg-slate-100 dark:bg-slate-900/30 border-slate-300 dark:border-slate-700',
  postal_code: 'bg-teal-100 dark:bg-teal-900/30 border-teal-300 dark:border-teal-700',
};

interface TextSegment {
  type: 'text' | 'entity';
  content: string;
  entity?: DetectedEntity;
}

export const EntityViewer: React.FC<EntityViewerProps> = ({
  text,
  entities,
  onEntityClick,
  highlightCategory,
  className,
}) => {
  const [hoveredEntity, setHoveredEntity] = useState<string | null>(null);

  // Sort entities by start offset and create segments
  const segments = useMemo<TextSegment[]>(() => {
    if (entities.length === 0) {
      return [{ type: 'text', content: text }];
    }

    const sorted = [...entities].sort((a, b) => a.startOffset - b.startOffset);
    const result: TextSegment[] = [];
    let lastEnd = 0;

    for (const entity of sorted) {
      // Add text before entity
      if (entity.startOffset > lastEnd) {
        result.push({
          type: 'text',
          content: text.slice(lastEnd, entity.startOffset),
        });
      }

      // Add entity
      result.push({
        type: 'entity',
        content: text.slice(entity.startOffset, entity.endOffset),
        entity,
      });

      lastEnd = entity.endOffset;
    }

    // Add remaining text
    if (lastEnd < text.length) {
      result.push({
        type: 'text',
        content: text.slice(lastEnd),
      });
    }

    return result;
  }, [text, entities]);

  return (
    <div
      className={clsx(
        'font-mono text-sm leading-relaxed whitespace-pre-wrap',
        'p-4 bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700',
        className
      )}
    >
      {segments.map((segment, index) => {
        if (segment.type === 'text') {
          return <span key={index}>{segment.content}</span>;
        }

        const entity = segment.entity!;
        const isHighlighted =
          !highlightCategory || entity.category === highlightCategory;
        const isHovered = hoveredEntity === entity.id;

        return (
          <span
            key={index}
            className="relative inline"
            onMouseEnter={() => setHoveredEntity(entity.id)}
            onMouseLeave={() => setHoveredEntity(null)}
          >
            <button
              type="button"
              onClick={() => onEntityClick?.(entity.id)}
              className={clsx(
                'inline px-1 py-0.5 rounded border cursor-pointer',
                'transition-all duration-150',
                'focus:outline-none focus:ring-2 focus:ring-primary-500',
                CATEGORY_COLORS[entity.category],
                {
                  'opacity-30': !isHighlighted,
                  'ring-2 ring-primary-500': isHovered,
                }
              )}
              aria-label={`${PII_CATEGORY_LABELS[entity.category]}: ${segment.content}`}
            >
              {segment.content}
            </button>

            {/* Tooltip */}
            {isHovered && (
              <div
                role="tooltip"
                className={clsx(
                  'absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2',
                  'p-3 min-w-[200px]',
                  'bg-white dark:bg-gray-800 rounded-lg shadow-lg',
                  'border border-gray-200 dark:border-gray-700',
                  'text-left'
                )}
              >
                <div className="flex items-center gap-2 mb-2">
                  <CategoryChip category={entity.category} />
                  <ConfidenceBadge score={entity.confidence} />
                </div>

                {entity.alias && (
                  <div className="text-xs">
                    <span className="text-gray-500 dark:text-gray-400">
                      Alias:{' '}
                    </span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {entity.alias}
                    </span>
                  </div>
                )}

                {/* Arrow */}
                <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-white dark:bg-gray-800 border-r border-b border-gray-200 dark:border-gray-700 rotate-45" />
              </div>
            )}
          </span>
        );
      })}
    </div>
  );
};

export default EntityViewer;
