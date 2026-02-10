/**
 * ExportDialog - Export format selection dialog
 *
 * Traceability:
 * - Contract: CNT-UI-COMP-009
 * - Binding: UI-BIND-009
 */

import React, { useState, useEffect, useRef } from 'react';
import clsx from 'clsx';
import type { ExportFormat } from '@/types';

interface ExportDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onExport: (format: ExportFormat) => void;
  isExporting?: boolean;
  documentName?: string;
  canExport?: boolean;
  exportBlockedReason?: string;
}

const FORMAT_OPTIONS: { format: ExportFormat; label: string; icon: string }[] = [
  { format: 'pdf', label: 'PDF', icon: '📄' },
  { format: 'docx', label: 'Word (DOCX)', icon: '📝' },
  { format: 'txt', label: 'Texto plano', icon: '📃' },
];

export const ExportDialog: React.FC<ExportDialogProps> = ({
  isOpen,
  onClose,
  onExport,
  isExporting = false,
  documentName,
  canExport = true,
  exportBlockedReason,
}) => {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>('pdf');
  const dialogRef = useRef<HTMLDivElement>(null);

  // Focus trap and escape handling
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Focus dialog on open
  useEffect(() => {
    if (isOpen && dialogRef.current) {
      dialogRef.current.focus();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleExport = () => {
    onExport(selectedFormat);
  };

  return (
    <div
      className="fixed inset-0 z-50 overflow-y-auto"
      aria-labelledby="export-dialog-title"
      role="dialog"
      aria-modal="true"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Dialog positioning */}
      <div className="flex min-h-full items-center justify-center p-4">
        {/* Dialog content */}
        <div
          ref={dialogRef}
          tabIndex={-1}
          className={clsx(
            'relative w-full max-w-md',
            'bg-white dark:bg-gray-800 rounded-lg shadow-2xl',
            'transform transition-all'
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
            <h2
              id="export-dialog-title"
              className="text-lg font-semibold text-gray-900 dark:text-white"
            >
              Exportar documento
            </h2>
            <button
              type="button"
              onClick={onClose}
              className={clsx(
                'p-1 rounded-lg',
                'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300',
                'hover:bg-gray-100 dark:hover:bg-gray-700',
                'focus:outline-none focus:ring-2 focus:ring-primary-500'
              )}
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>

          {/* Body */}
          <div className="p-4 space-y-4">
            {documentName && (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Archivo: <span className="font-medium">{documentName}</span>
              </p>
            )}

            {/* Safety Latch Warning */}
            {!canExport && exportBlockedReason && (
              <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-sm">
                <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <span>{exportBlockedReason}</span>
              </div>
            )}

            <div>
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">
                Formato de exportación
              </label>
              <div className="space-y-2">
                {FORMAT_OPTIONS.map(({ format, label, icon }) => (
                  <label
                    key={format}
                    className={clsx(
                      'flex items-center gap-3 p-3 rounded-lg border cursor-pointer',
                      'transition-colors duration-150',
                      {
                        'border-primary-500 bg-primary-50 dark:bg-primary-900/20':
                          selectedFormat === format,
                        'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700':
                          selectedFormat !== format,
                      }
                    )}
                  >
                    <input
                      type="radio"
                      name="exportFormat"
                      value={format}
                      checked={selectedFormat === format}
                      onChange={() => setSelectedFormat(format)}
                      className="sr-only"
                    />
                    <span className="text-xl">{icon}</span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {label}
                    </span>
                    {selectedFormat === format && (
                      <svg
                        className="w-5 h-5 text-primary-500 ml-auto"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="flex items-center justify-end gap-3 p-4 border-t border-gray-200 dark:border-gray-700">
            <button
              type="button"
              onClick={onClose}
              disabled={isExporting}
              className={clsx(
                'px-4 py-2 text-sm font-medium rounded-lg',
                'border border-gray-300 dark:border-gray-600',
                'text-gray-700 dark:text-gray-300',
                'hover:bg-gray-50 dark:hover:bg-gray-700',
                'focus:outline-none focus:ring-2 focus:ring-primary-500',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={handleExport}
              disabled={isExporting || !canExport}
              className={clsx(
                'flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg',
                'bg-primary-500 text-white',
                'hover:bg-primary-600',
                'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
                'disabled:opacity-50 disabled:cursor-not-allowed'
              )}
            >
              {isExporting ? (
                <>
                  <svg
                    className="w-4 h-4 animate-spin"
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
                  Exportando...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm3.293-7.707a1 1 0 011.414 0L9 10.586V3a1 1 0 112 0v7.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                  Descargar
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExportDialog;
