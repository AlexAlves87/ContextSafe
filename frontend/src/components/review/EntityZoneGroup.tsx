/**
 * EntityZoneGroup - Groups entities by confidence zone with review actions.
 * Includes category correction dropdown for reclassifying mistyped entities.
 */

import React, { useState, useRef, useEffect } from 'react';
import type { DetectedEntity, ConfidenceZone, ReviewAction, PiiCategory } from '@/types';
import { PII_CATEGORY_LABELS } from '@/types';
import clsx from 'clsx';

const ZONE_CONFIG: Record<ConfidenceZone, {
  bg: string;
  border: string;
  text: string;
  dot: string;
  headerBg: string;
}> = {
  GREEN: {
    bg: 'bg-emerald-50 dark:bg-emerald-900/20',
    border: 'border-emerald-200 dark:border-emerald-800',
    text: 'text-emerald-700 dark:text-emerald-300',
    dot: 'bg-emerald-500',
    headerBg: 'bg-emerald-100 dark:bg-emerald-900/40',
  },
  AMBER: {
    bg: 'bg-amber-50 dark:bg-amber-900/20',
    border: 'border-amber-200 dark:border-amber-800',
    text: 'text-amber-700 dark:text-amber-300',
    dot: 'bg-amber-500',
    headerBg: 'bg-amber-100 dark:bg-amber-900/40',
  },
  RED: {
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-800',
    text: 'text-red-700 dark:text-red-300',
    dot: 'bg-red-500',
    headerBg: 'bg-red-100 dark:bg-red-900/40',
  },
};

interface EntityZoneGroupProps {
  zone: ConfidenceZone;
  entities: DetectedEntity[];
  onReviewEntity: (entityId: string, action: ReviewAction, newCategory?: string) => void;
  onBatchApprove?: () => void;
  isReviewing: boolean;
}

export const EntityZoneGroup: React.FC<EntityZoneGroupProps> = ({
  zone,
  entities,
  onReviewEntity,
  onBatchApprove,
  isReviewing,
}) => {
  const config = ZONE_CONFIG[zone];
  const [collapsed, setCollapsed] = useState(zone === 'GREEN' && entities.length > 5);
  const [correctingEntityId, setCorrectingEntityId] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const pendingCount = entities.filter(e => !e.reviewed).length;

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setCorrectingEntityId(null);
      }
    }
    if (correctingEntityId) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [correctingEntityId]);

  const handleCorrectCategory = (entityId: string, newCategory: string) => {
    onReviewEntity(entityId, 'CORRECTED', newCategory);
    setCorrectingEntityId(null);
  };

  // Categories grouped for the dropdown
  const categoryGroups: { label: string; categories: PiiCategory[] }[] = [
    { label: 'Identidad', categories: ['person_name', 'organization'] },
    { label: 'Ubicación', categories: ['address', 'location', 'postal_code'] },
    { label: 'Documentos', categories: ['dni', 'nie', 'dni_nie', 'passport', 'social_security'] },
    { label: 'Contacto', categories: ['phone', 'email'] },
    { label: 'Financiero', categories: ['iban', 'bank_account', 'credit_card'] },
    { label: 'Temporal', categories: ['date'] },
    { label: 'Otros', categories: ['medical_record', 'license_plate', 'ip_address', 'url'] },
  ];
  const zoneLabel =
    zone === 'GREEN' ? 'Verde'
    : zone === 'AMBER' ? 'Ámbar'
    : 'Rojo';
  const zoneDesc =
    zone === 'GREEN' ? 'Alta confianza'
    : zone === 'AMBER' ? 'Revisión crítica necesaria'
    : 'Debe confirmar si es PII';

  if (entities.length === 0) return null;

  return (
    <div className={clsx('rounded-lg border', config.border, 'overflow-hidden')}>
      {/* Zone header */}
      <div
        className={clsx(
          'flex items-center justify-between px-3 py-2 cursor-pointer select-none',
          config.headerBg
        )}
        onClick={() => setCollapsed(!collapsed)}
      >
        <div className="flex items-center gap-2">
          <span className={clsx('w-2.5 h-2.5 rounded-full', config.dot)} />
          <span className={clsx('text-xs font-bold uppercase tracking-wider', config.text)}>
            {zoneLabel} ({entities.length})
          </span>
          <span className="text-[10px] text-muted-foreground">{zoneDesc}</span>
        </div>
        <div className="flex items-center gap-2">
          {zone === 'GREEN' && onBatchApprove && pendingCount > 0 && (
            <button
              onClick={(e) => { e.stopPropagation(); onBatchApprove(); }}
              disabled={isReviewing}
              className={clsx(
                'px-2 py-0.5 text-[10px] font-semibold uppercase rounded',
                'bg-emerald-600 text-white hover:bg-emerald-700',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              Aprobar todas ({pendingCount})
            </button>
          )}
          <span className="text-xs text-muted-foreground">{collapsed ? '▸' : '▾'}</span>
        </div>
      </div>

      {/* Entity list */}
      {!collapsed && (
        <div className="divide-y divide-gray-100 dark:divide-gray-800">
          {entities.map((entity) => (
            <div
              key={entity.id}
              className={clsx(
                'flex items-center justify-between px-3 py-2 text-xs',
                entity.reviewed ? 'opacity-60' : '',
                config.bg
              )}
            >
              <div className="flex items-center gap-2 min-w-0 flex-1">
                <span className={clsx(
                  'px-1.5 py-0.5 rounded text-[10px] font-mono uppercase',
                  'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                )}>
                  {entity.category.replace(/_/g, ' ')}
                </span>
                <span className="font-medium text-foreground truncate">
                  "{entity.originalText}"
                </span>
                <span className="text-muted-foreground">
                  {entity.alias && <>&#8594; {entity.alias}</>}
                </span>
                <span className="text-muted-foreground">
                  {Math.round(entity.confidence * 100)}%
                </span>
              </div>

              {/* Review actions */}
              <div className="flex items-center gap-1 flex-shrink-0 ml-2 relative">
                {entity.reviewed ? (
                  <span className={clsx(
                    'px-2 py-0.5 rounded text-[10px] font-semibold uppercase',
                    entity.reviewAction === 'APPROVED' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-800 dark:text-emerald-200' :
                    entity.reviewAction === 'REJECTED' ? 'bg-red-100 text-red-700 dark:bg-red-800 dark:text-red-200' :
                    'bg-blue-100 text-blue-700 dark:bg-blue-800 dark:text-blue-200'
                  )}>
                    {entity.reviewAction === 'APPROVED' ? '✓' : entity.reviewAction === 'REJECTED' ? '✗' : '✎'}
                  </span>
                ) : (
                  <>
                    <button
                      onClick={() => onReviewEntity(entity.id, 'APPROVED')}
                      disabled={isReviewing}
                      className="px-1.5 py-0.5 text-[10px] font-semibold uppercase rounded bg-emerald-100 text-emerald-700 hover:bg-emerald-200 dark:bg-emerald-800 dark:text-emerald-200 dark:hover:bg-emerald-700 disabled:opacity-50"
                      title="Aprobar"
                    >
                      ✓
                    </button>
                    {(zone === 'AMBER' || zone === 'RED') && (
                      <button
                        onClick={() => onReviewEntity(entity.id, 'REJECTED')}
                        disabled={isReviewing}
                        className="px-1.5 py-0.5 text-[10px] font-semibold uppercase rounded bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-800 dark:text-red-200 dark:hover:bg-red-700 disabled:opacity-50"
                        title="Rechazar"
                      >
                        ✗
                      </button>
                    )}
                    <button
                      onClick={() => setCorrectingEntityId(
                        correctingEntityId === entity.id ? null : entity.id
                      )}
                      disabled={isReviewing}
                      className="px-1.5 py-0.5 text-[10px] font-semibold uppercase rounded bg-blue-100 text-blue-700 hover:bg-blue-200 dark:bg-blue-800 dark:text-blue-200 dark:hover:bg-blue-700 disabled:opacity-50"
                      title="Corregir categoría"
                    >
                      ✎
                    </button>
                  </>
                )}

                {/* Category correction dropdown */}
                {correctingEntityId === entity.id && (
                  <div
                    ref={dropdownRef}
                    className="absolute right-0 top-full mt-1 z-50 w-56 max-h-64 overflow-y-auto rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-lg"
                  >
                    <div className="px-2 py-1.5 text-[10px] font-bold uppercase text-muted-foreground border-b border-gray-100 dark:border-gray-700">
                      Seleccionar categoría
                    </div>
                    {categoryGroups.map((group) => (
                      <div key={group.label}>
                        <div className="px-2 py-1 text-[9px] font-semibold uppercase text-muted-foreground bg-gray-50 dark:bg-gray-900/50">
                          {group.label}
                        </div>
                        {group.categories.map((cat) => {
                          const isCurrentCategory = entity.category === cat;
                          return (
                            <button
                              key={cat}
                              onClick={() => handleCorrectCategory(entity.id, cat.toUpperCase())}
                              disabled={isCurrentCategory}
                              className={clsx(
                                'w-full text-left px-3 py-1.5 text-xs hover:bg-blue-50 dark:hover:bg-blue-900/30',
                                isCurrentCategory && 'opacity-40 cursor-not-allowed bg-gray-50 dark:bg-gray-900/30'
                              )}
                            >
                              <span className="font-mono text-[10px] text-muted-foreground mr-1.5">
                                {cat.toUpperCase().replace(/_/g, ' ')}
                              </span>
                              <span className="text-foreground">
                                {PII_CATEGORY_LABELS[cat] || cat}
                              </span>
                            </button>
                          );
                        })}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default EntityZoneGroup;
