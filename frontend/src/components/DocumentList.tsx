/**
 * DocumentList - List of documents with status indicators
 *
 * Traceability:
 * - Contract: CNT-UI-COMP-002
 * - Binding: UI-BIND-002
 */

import React, { useCallback } from 'react';
import clsx from 'clsx';
import type { DocumentListItem, DocumentState } from '@/types';
import { DOCUMENT_STATE_LABELS } from '@/types';
import { LoadingSpinner } from './LoadingSpinner';

interface DocumentListProps {
  documents: DocumentListItem[];
  onSelect: (id: string) => void;
  onDownload?: (id: string) => void;
  onView?: (id: string) => void;
  selectedId?: string;
  isLoading?: boolean;
  variant?: 'default' | 'industrial';
}

const STATE_ICONS: Record<DocumentState, React.ReactNode> = {
  pending: (
    <svg className="w-5 h-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
      <path d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" />
    </svg>
  ),
  ingesting: (
    <svg className="w-5 h-5 text-blue-500 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
      <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
    </svg>
  ),
  detecting: (
    <svg className="w-5 h-5 text-yellow-500 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
      <path d="M9 9a2 2 0 114 0 2 2 0 01-4 0z" />
      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a4 4 0 00-3.446 6.032l-2.261 2.26a1 1 0 101.414 1.415l2.261-2.261A4 4 0 1011 5z" clipRule="evenodd" />
    </svg>
  ),
  anonymizing: (
    <svg className="w-5 h-5 text-purple-500 animate-pulse" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
    </svg>
  ),
  completed: (
    <svg className="w-5 h-5 text-success-500" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
    </svg>
  ),
  failed: (
    <svg className="w-5 h-5 text-danger-500" fill="currentColor" viewBox="0 0 20 20">
      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
    </svg>
  ),
};

const FORMAT_ICONS: Record<string, string> = {
  pdf: '📄',
  docx: '📝',
  txt: '📃',
  png: '🖼️',
  jpg: '🖼️',
  jpeg: '🖼️',
};

// State abbreviations for industrial display
const STATE_ABBREV: Record<DocumentState, string> = {
  pending: 'READY',
  ingesting: 'LOAD',
  detecting: 'SCAN',
  anonymizing: 'PROC',
  completed: 'DONE',
  failed: 'FAIL',
};

export const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  onSelect,
  onDownload,
  onView,
  selectedId,
  isLoading = false,
  variant = 'default',
}) => {
  const isIndustrial = variant === 'industrial';
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent, index: number) => {
      if (e.key === 'ArrowDown' && index < documents.length - 1) {
        e.preventDefault();
        onSelect(documents[index + 1].id);
      } else if (e.key === 'ArrowUp' && index > 0) {
        e.preventDefault();
        onSelect(documents[index - 1].id);
      } else if (e.key === 'Enter') {
        onSelect(documents[index].id);
      }
    },
    [documents, onSelect]
  );

  if (isLoading) {
    return (
      <div className={clsx('flex items-center justify-center', isIndustrial ? 'py-8' : 'py-12')}>
        <LoadingSpinner size={isIndustrial ? 'sm' : 'lg'} label={isIndustrial ? 'CARGANDO...' : 'Cargando documentos...'} />
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className={clsx('text-center', isIndustrial ? 'py-8' : 'py-12')}>
        {isIndustrial ? (
          <p className="text-[10px] uppercase tracking-wider text-muted-foreground">
            SIN DOCUMENTOS
          </p>
        ) : (
          <>
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-semibold text-gray-900 dark:text-white">
              No hay documentos
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Sube un documento para comenzar
            </p>
          </>
        )}
      </div>
    );
  }

  // Industrial variant - Table
  if (isIndustrial) {
    return (
      <table className="table-industrial">
        <thead>
          <tr>
            <th className="w-14">EXT</th>
            <th>NOMBRE</th>
            <th className="w-16 text-center">ENTID</th>
            <th className="w-16 text-center">ESTADO</th>
            <th className="w-16 text-center">ACCIÓN</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc, index) => (
            <tr
              key={doc.id}
              onClick={() => onSelect(doc.id)}
              onKeyDown={(e) => handleKeyDown(e, index)}
              tabIndex={0}
              className={clsx(
                'cursor-pointer',
                doc.id === selectedId && 'bg-primary/10'
              )}
            >
              <td>
                <span className="ext-badge">
                  {(doc.format || 'UNK').toUpperCase()}
                </span>
              </td>
              <td className="truncate max-w-[200px]" title={doc.filename}>
                {doc.filename}
              </td>
              <td className="text-center text-muted-foreground">
                {doc.entityCount}
              </td>
              <td className="text-center">
                {doc.state !== 'completed' && doc.state !== 'failed' && doc.progress !== undefined ? (
                  <span className="state-badge state-badge-processing">
                    {Math.round(doc.progress)}%
                  </span>
                ) : (
                  <span className={clsx(
                    'state-badge',
                    doc.state === 'completed' && 'state-badge-done',
                    doc.state === 'failed' && 'state-badge-fail',
                    doc.state === 'pending' && 'state-badge-ready',
                    (doc.state === 'ingesting' || doc.state === 'detecting' || doc.state === 'anonymizing') && 'state-badge-processing'
                  )}>
                    {STATE_ABBREV[doc.state]}
                  </span>
                )}
              </td>
              <td className="text-center">
                <div className="flex items-center justify-center gap-1">
                  {doc.state === 'completed' && onView && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onView(doc.id);
                      }}
                      className="p-1 text-muted-foreground hover:text-primary"
                      title="Ver"
                    >
                      👁
                    </button>
                  )}
                  {doc.state === 'completed' && onDownload && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDownload(doc.id);
                      }}
                      className="p-1 text-muted-foreground hover:text-primary"
                      title="Descargar"
                    >
                      ↓
                    </button>
                  )}
                  {doc.state === 'pending' && (
                    <span className="text-muted-foreground/50">—</span>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    );
  }

  // Default variant - List
  return (
    <ul
      role="listbox"
      aria-activedescendant={selectedId ? `doc-${selectedId}` : undefined}
      className="divide-y divide-gray-200 dark:divide-gray-700"
    >
      {documents.map((doc, index) => (
        <li
          key={doc.id}
          id={`doc-${doc.id}`}
          role="option"
          aria-selected={doc.id === selectedId}
          tabIndex={0}
          onClick={() => onSelect(doc.id)}
          onKeyDown={(e) => handleKeyDown(e, index)}
          className={clsx(
            'flex items-center gap-4 p-4 cursor-pointer',
            'transition-colors duration-150',
            'focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500',
            {
              'bg-primary-50 dark:bg-primary-900/20': doc.id === selectedId,
              'hover:bg-gray-50 dark:hover:bg-gray-800': doc.id !== selectedId,
            }
          )}
        >
          {/* Format icon */}
          <span className="text-2xl" aria-hidden="true">
            {FORMAT_ICONS[doc.format] || '📄'}
          </span>

          {/* Document info */}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
              {doc.filename}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {doc.entityCount} entidades · {new Date(doc.createdAt).toLocaleDateString('es')}
            </p>
          </div>

          {/* Progress (if processing) */}
          {doc.progress !== undefined && doc.state !== 'completed' && doc.state !== 'failed' && (
            <div className="w-16">
              <div className="text-xs text-gray-500 text-right mb-1">
                {Math.round(doc.progress)}%
              </div>
              <div className="h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary-500 transition-all duration-300"
                  style={{ width: `${doc.progress}%` }}
                />
              </div>
            </div>
          )}

          {/* Status icon */}
          <div
            title={DOCUMENT_STATE_LABELS[doc.state]}
            aria-label={DOCUMENT_STATE_LABELS[doc.state]}
          >
            {STATE_ICONS[doc.state]}
          </div>

          {/* Action buttons for completed documents */}
          {doc.state === 'completed' && (
            <div className="flex items-center gap-1">
              {onDownload && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDownload(doc.id);
                  }}
                  className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  title="Descargar"
                  aria-label="Descargar documento"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
              )}
              {onView && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onView(doc.id);
                  }}
                  className="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                  title="Ver"
                  aria-label="Ver documento"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                    <path
                      fillRule="evenodd"
                      d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
              )}
            </div>
          )}
        </li>
      ))}
    </ul>
  );
};

export default DocumentList;
