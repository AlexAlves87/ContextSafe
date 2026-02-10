/**
 * ProcessingModal - Unified modal for document processing
 *
 * Three states (morphing design per REFORMA.md):
 * 1. config - Configuration form (level, hardware, options)
 * 2. processing - Execution with progress bar and terminal
 * 3. finished - Summary with option to view results
 *
 * The modal frame persists across states for visual continuity.
 *
 * @generated for REFORMA.md implementation
 */

import React, { useState, useEffect, useCallback } from 'react';
import clsx from 'clsx';
import { LoadingSpinner } from '@/components/LoadingSpinner';
import { SystemLog } from '@/components/SystemLog';
import { useProcessing } from '@/hooks/useProcessing';
import { systemApi } from '@/services/api';
import type { DocumentListItem, AnonymizationLevel, HardwareInfo, ComputeMode } from '@/types';

// Minimal document info needed for processing
type ProcessableDocument = Pick<DocumentListItem, 'id' | 'filename' | 'state'>;

interface ProcessingModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
  projectName: string;
  documents: ProcessableDocument[];
  onComplete: () => void;
}

// Anonymization level config
const LEVEL_CONFIG = [
  {
    value: 'basic' as const,
    label: 'Básico',
    icon: '🔒',
    desc: 'Máscara: ****',
  },
  {
    value: 'intermediate' as const,
    label: 'Intermedio',
    icon: '🎭',
    desc: 'Pseudónimos',
    recommended: true,
  },
  {
    value: 'advanced' as const,
    label: 'Avanzado',
    icon: '🧬',
    desc: 'Dat. Sintéticos',
  },
];

export const ProcessingModal: React.FC<ProcessingModalProps> = ({
  isOpen,
  onClose,
  projectId: _projectId,
  projectName,
  documents,
  onComplete,
}) => {
  // projectId reserved for future use (e.g., compute mode per project)
  void _projectId;
  // Configuration state
  const [anonymizationLevel, setAnonymizationLevel] = useState<AnonymizationLevel>('intermediate');
  const [computeMode, setComputeMode] = useState<ComputeMode>('cpu');
  const [hardwareInfo, setHardwareInfo] = useState<HardwareInfo | null>(null);
  const [hardwareLoading, setHardwareLoading] = useState(true);
  const [options, setOptions] = useState({
    maintainConsistency: true,
    preserveFormatting: true,
  });

  // Processing hook
  const {
    state: processingState,
    logs,
    progress,
    hasErrors,
    startProcessing,
    cancelProcessing,
    reset,
  } = useProcessing({
    onComplete: () => {
      // Don't auto-close, let user review
    },
    onError: (error) => {
      console.error('Processing error:', error);
    },
  });

  // Timer for elapsed time
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [startTime, setStartTime] = useState<Date | null>(null);

  // Load hardware info on mount
  useEffect(() => {
    if (!isOpen) return;

    const loadHardware = async () => {
      try {
        const info = await systemApi.getHardware();
        setHardwareInfo(info);
        setComputeMode(info.current_mode);
      } catch (error) {
        console.error('Failed to load hardware:', error);
      } finally {
        setHardwareLoading(false);
      }
    };
    loadHardware();
  }, [isOpen]);

  // Timer effect
  useEffect(() => {
    if (processingState !== 'processing' || !startTime) return;

    const interval = setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startTime.getTime()) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [processingState, startTime]);

  // Reset when modal closes
  useEffect(() => {
    if (!isOpen) {
      reset();
      setElapsedSeconds(0);
      setStartTime(null);
    }
  }, [isOpen, reset]);

  // Handle start processing
  const handleStartProcessing = useCallback(async () => {
    setStartTime(new Date());
    setElapsedSeconds(0);
    await startProcessing(documents, anonymizationLevel);
  }, [documents, anonymizationLevel, startProcessing]);

  // Handle view results (close modal and refresh)
  const handleViewResults = useCallback(() => {
    onComplete();
    onClose();
  }, [onComplete, onClose]);

  // Handle cancel
  const handleCancel = useCallback(() => {
    if (processingState === 'processing') {
      cancelProcessing();
    } else {
      onClose();
    }
  }, [processingState, cancelProcessing, onClose]);

  // Format elapsed time
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Get modal title based on state
  const getTitle = (): string => {
    switch (processingState) {
      case 'idle':
        return 'Configurar Procesamiento';
      case 'processing':
        return `Ejecutando: ${projectName}`;
      case 'finished':
        return hasErrors ? 'Procesamiento con Errores' : 'Procesamiento Completado';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div
        className={clsx(
          'bg-card border border-border rounded-lg shadow-2xl w-full max-w-2xl mx-4',
          'transform transition-all duration-300',
          'flex flex-col max-h-[90vh]'
        )}
      >
        {/* Header - Always visible */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="text-lg font-semibold text-foreground">{getTitle()}</h2>
          {processingState === 'idle' && (
            <button
              onClick={onClose}
              className="p-1 rounded hover:bg-muted transition-colors"
            >
              <svg className="w-5 h-5 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        {/* Content - Changes based on state */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* STATE: CONFIG (idle) */}
          {processingState === 'idle' && (
            <div className="space-y-6 animate-fade-in">
              {/* Project info */}
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <span>📂</span>
                <span>Proyecto: <strong className="text-foreground">{projectName}</strong></span>
                <span className="mx-2">·</span>
                <span>{documents.length} documento(s)</span>
              </div>

              {/* Anonymization Level */}
              <div>
                <h3 className="text-sm font-medium text-foreground mb-3">
                  1. Nivel de Anonimización
                </h3>
                <div className="grid grid-cols-3 gap-3">
                  {LEVEL_CONFIG.map((level) => (
                    <button
                      key={level.value}
                      onClick={() => setAnonymizationLevel(level.value)}
                      className={clsx(
                        'flex flex-col items-center p-4 rounded-lg border-2 transition-all',
                        anonymizationLevel === level.value
                          ? 'border-primary bg-primary/10'
                          : 'border-border hover:border-muted-foreground'
                      )}
                    >
                      <span className="text-2xl mb-1">{level.icon}</span>
                      <span className="text-sm font-medium text-foreground">{level.label}</span>
                      <span className="text-xs text-muted-foreground">{level.desc}</span>
                      {level.recommended && (
                        <span className="mt-1 text-xs px-2 py-0.5 bg-primary/20 text-primary rounded">
                          Recomendado
                        </span>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Options */}
              <div>
                <h3 className="text-sm font-medium text-foreground mb-3">
                  2. Parámetros de Salida
                </h3>
                <div className="space-y-2">
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={options.maintainConsistency}
                      onChange={(e) => setOptions((prev) => ({ ...prev, maintainConsistency: e.target.checked }))}
                      className="w-4 h-4 text-primary rounded focus:ring-primary"
                    />
                    <span className="text-sm text-foreground">
                      Mantener consistencia de IDs (Cross-document)
                    </span>
                  </label>
                  <label className="flex items-center gap-3 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={options.preserveFormatting}
                      onChange={(e) => setOptions((prev) => ({ ...prev, preserveFormatting: e.target.checked }))}
                      className="w-4 h-4 text-primary rounded focus:ring-primary"
                    />
                    <span className="text-sm text-foreground">
                      Preservar formato original
                    </span>
                  </label>
                </div>
              </div>

              {/* Hardware */}
              <div>
                <h3 className="text-sm font-medium text-foreground mb-3">
                  3. Recursos de Hardware
                </h3>
                {hardwareLoading ? (
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <LoadingSpinner size="sm" />
                    <span>Detectando hardware...</span>
                  </div>
                ) : hardwareInfo ? (
                  <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                    <div className="flex items-center gap-2">
                      <span>🚀</span>
                      <span className="text-sm text-foreground">
                        {hardwareInfo.gpu.available
                          ? `GPU (${hardwareInfo.gpu.name})`
                          : 'CPU'}
                      </span>
                    </div>
                    {hardwareInfo.gpu.available && (
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">Modo:</span>
                        <div className="flex rounded border border-border overflow-hidden">
                          <button
                            onClick={() => setComputeMode('gpu')}
                            className={clsx(
                              'px-3 py-1 text-xs font-medium transition-colors',
                              computeMode === 'gpu'
                                ? 'bg-primary text-primary-foreground'
                                : 'bg-card text-muted-foreground hover:bg-muted'
                            )}
                          >
                            GPU
                          </button>
                          <button
                            onClick={() => setComputeMode('cpu')}
                            className={clsx(
                              'px-3 py-1 text-xs font-medium transition-colors border-l border-border',
                              computeMode === 'cpu'
                                ? 'bg-primary text-primary-foreground'
                                : 'bg-card text-muted-foreground hover:bg-muted'
                            )}
                          >
                            CPU
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-sm text-muted-foreground">
                    No se pudo detectar el hardware
                  </div>
                )}
              </div>
            </div>
          )}

          {/* STATE: PROCESSING */}
          {processingState === 'processing' && (
            <div className="space-y-4 animate-fade-in">
              {/* Progress bar */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-foreground">
                    Progreso del Lote
                  </span>
                  <span className="text-sm text-muted-foreground">
                    Docs: {progress.completedDocs} / {progress.totalDocs}
                  </span>
                </div>
                <div
                  className="h-4 bg-muted rounded-full overflow-hidden"
                  style={{ position: 'relative' }}
                >
                  <div
                    style={{
                      position: 'absolute',
                      left: 0,
                      top: 0,
                      height: '100%',
                      width: `${progress.overallProgress}%`,
                      backgroundColor: 'hsl(var(--primary))',
                      borderRadius: '9999px',
                      transition: 'width 0.3s ease-out'
                    }}
                  />
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs text-muted-foreground">
                    {Math.round(progress.overallProgress)}% completado (raw: {progress.overallProgress.toFixed(2)})
                  </span>
                </div>
              </div>

              {/* System Log */}
              <SystemLog entries={logs} maxHeight={300} />
            </div>
          )}

          {/* STATE: FINISHED */}
          {processingState === 'finished' && (
            <div className="space-y-4 animate-fade-in">
              {/* Final progress bar (100% green or with error indicator) */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-foreground">
                    {hasErrors ? 'Completado con errores' : 'Procesamiento Completado'}
                  </span>
                  <span className="text-sm text-muted-foreground">
                    Docs: {progress.completedDocs} / {progress.totalDocs}
                  </span>
                </div>
                <div className="h-4 bg-muted rounded-full overflow-hidden relative">
                  <div
                    className={clsx(
                      'h-full absolute left-0 top-0 w-full',
                      hasErrors ? 'bg-warning' : 'bg-success'
                    )}
                  />
                </div>
              </div>

              {/* System Log - scrollable to review errors */}
              <SystemLog entries={logs} maxHeight={300} />
            </div>
          )}
        </div>

        {/* Footer - Buttons based on state */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-border bg-muted/20">
          {/* Left: Timer (only during processing/finished) */}
          <div className="flex items-center gap-2">
            {(processingState === 'processing' || processingState === 'finished') && (
              <>
                <span className="text-muted-foreground">⏱️</span>
                <span className="text-sm font-mono text-muted-foreground">
                  T: {formatTime(elapsedSeconds)}
                </span>
              </>
            )}
          </div>

          {/* Right: Action buttons */}
          <div className="flex items-center gap-3">
            {processingState === 'idle' && (
              <>
                <button
                  onClick={onClose}
                  className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleStartProcessing}
                  disabled={documents.length === 0}
                  className={clsx(
                    'px-6 py-2 text-sm font-medium rounded-lg transition-colors',
                    'bg-primary text-primary-foreground hover:bg-primary/90',
                    'disabled:opacity-50 disabled:cursor-not-allowed'
                  )}
                >
                  Procesar
                </button>
              </>
            )}

            {processingState === 'processing' && (
              <button
                onClick={handleCancel}
                className="px-6 py-2 text-sm font-medium rounded-lg bg-destructive text-destructive-foreground hover:bg-destructive/90 transition-colors"
              >
                Cancelar Operación
              </button>
            )}

            {processingState === 'finished' && (
              <button
                onClick={handleViewResults}
                className={clsx(
                  'px-6 py-2 text-sm font-medium rounded-lg transition-colors',
                  hasErrors
                    ? 'bg-warning text-warning-foreground hover:bg-warning/90'
                    : 'bg-success text-success-foreground hover:bg-success/90'
                )}
              >
                Ver Resultados
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProcessingModal;
