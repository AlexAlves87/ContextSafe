/**
 * useProcessing - Hook for document batch processing with WebSocket
 *
 * Handles:
 * - WebSocket connections for multiple documents
 * - Message buffering for smooth UI updates
 * - Log transformation from WS messages
 * - Progress aggregation
 *
 * Architecture: Clean separation of processing logic from UI
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { createProgressWebSocket, ProcessingWebSocket } from '@/services/websocket';
import { documentApi } from '@/services/api';
import type { AnonymizationLevel, ProcessingStage } from '@/types';

// Minimal document info needed for processing
interface ProcessableDocument {
  id: string;
  filename: string;
}
import type { LogEntry } from '@/components/SystemLog';

// Processing state machine
export type ProcessingState = 'idle' | 'processing' | 'finished';

// Progress per document
export interface DocumentProgress {
  documentId: string;
  filename: string;
  stage: ProcessingStage;
  progress: number;
  currentEntity?: string;
}

// Aggregated progress
export interface AggregatedProgress {
  totalDocs: number;
  completedDocs: number;
  currentDoc?: string;
  overallProgress: number; // 0-100
}

// Category label mapping
const CATEGORY_LABELS: Record<string, string> = {
  PERSON_NAME: 'Persona',
  DNI_NIE: 'DNI/NIE',
  DNI: 'DNI',
  NIE: 'NIE',
  PHONE: 'Teléfono',
  EMAIL: 'Email',
  ADDRESS: 'Dirección',
  LOCATION: 'Ubicación',
  ORGANIZATION: 'Organización',
  DATE: 'Fecha',
  IBAN: 'IBAN',
  PROFESSIONAL_ID: 'ID Profesional',
  CASE_NUMBER: 'Nº Expediente',
  OTHER: 'Otro',
};

function formatCategory(raw: string): string {
  return CATEGORY_LABELS[raw] || raw.replace(/_/g, ' ');
}

// Generate unique log ID
let logIdCounter = 0;
function generateLogId(): string {
  return `log-${Date.now()}-${++logIdCounter}`;
}

// Transform WebSocket message to LogEntry
function wsMessageToLog(
  currentEntity: string | undefined,
  docName: string,
  stage: ProcessingStage
): LogEntry | null {
  if (!currentEntity) return null;

  const timestamp = new Date();

  // Completion message
  if (currentEntity === 'Completado') {
    return {
      id: generateLogId(),
      timestamp,
      level: 'success',
      message: `${docName}: Etapa ${stage} completada`,
    };
  }

  // System messages (Guardando, Actualizando, etc.)
  if (
    currentEntity.startsWith('Guardando') ||
    currentEntity.startsWith('Actualizando') ||
    currentEntity.startsWith('Iniciando')
  ) {
    return {
      id: generateLogId(),
      timestamp,
      level: 'info',
      message: `${docName}: ${currentEntity}`,
    };
  }

  // PII entity: PiiCategoryEnum.PERSON_NAME: Carlos López...
  const match = currentEntity.match(/PiiCategoryEnum\.(\w+): (.+)/);
  if (match) {
    const category = formatCategory(match[1]);
    const value = match[2].length > 40 ? match[2].slice(0, 40) + '...' : match[2];
    return {
      id: generateLogId(),
      timestamp,
      level: 'info',
      message: `${docName}: [${category}] ${value}`,
    };
  }

  // Fallback
  return {
    id: generateLogId(),
    timestamp,
    level: 'info',
    message: `${docName}: ${currentEntity}`,
  };
}

interface UseProcessingOptions {
  onComplete?: () => void;
  onError?: (error: string) => void;
  maxLogs?: number;
  logThrottleMs?: number;
  minVisualDurationMs?: number; // Minimum time to show progress animation
}

export function useProcessing(options: UseProcessingOptions = {}) {
  const { onComplete, onError, maxLogs = 200, logThrottleMs = 100, minVisualDurationMs = 1500 } = options;

  // State
  const [state, setState] = useState<ProcessingState>('idle');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [, setDocumentProgress] = useState<Map<string, DocumentProgress>>(
    new Map()
  );
  const [aggregatedProgress, setAggregatedProgress] = useState<AggregatedProgress>({
    totalDocs: 0,
    completedDocs: 0,
    overallProgress: 0,
  });
  const [hasErrors, setHasErrors] = useState(false);

  // Refs
  const wsConnectionsRef = useRef<Map<string, ProcessingWebSocket>>(new Map());
  const logBufferRef = useRef<LogEntry[]>([]);
  const lastLogFlushRef = useRef<number>(0);
  const totalDocsRef = useRef<number>(0);
  const completedDocsRef = useRef<Set<string>>(new Set());
  const processingStartTimeRef = useRef<number>(0);
  const visualProgressAnimationRef = useRef<number | null>(null);

  // Add log with throttling
  const addLog = useCallback(
    (entry: LogEntry) => {
      logBufferRef.current.push(entry);

      const now = Date.now();
      if (now - lastLogFlushRef.current >= logThrottleMs) {
        lastLogFlushRef.current = now;
        const newLogs = [...logBufferRef.current];
        logBufferRef.current = [];

        setLogs((prev) => {
          const updated = [...prev, ...newLogs];
          // Keep only last maxLogs
          return updated.slice(-maxLogs);
        });
      }
    },
    [logThrottleMs, maxLogs]
  );

  // Flush remaining logs
  const flushLogs = useCallback(() => {
    if (logBufferRef.current.length > 0) {
      const remaining = [...logBufferRef.current];
      logBufferRef.current = [];
      setLogs((prev) => [...prev, ...remaining].slice(-maxLogs));
    }
  }, [maxLogs]);

  // Update aggregated progress - called directly with current progress map
  const updateAggregatedProgress = useCallback((currentProgress: Map<string, DocumentProgress>) => {
    const total = totalDocsRef.current;
    const completed = completedDocsRef.current.size;

    if (total === 0) {
      setAggregatedProgress({ totalDocs: 0, completedDocs: 0, overallProgress: 0 });
      return;
    }

    // Calculate overall progress from individual documents
    let progressSum = 0;
    currentProgress.forEach((dp) => {
      progressSum += dp.progress;
    });
    // Add 100% for completed docs not in current progress map
    progressSum += completed * 100;

    const overallProgress = Math.min(100, progressSum / total);

    setAggregatedProgress({
      totalDocs: total,
      completedDocs: completed,
      overallProgress,
    });
  }, []);

  // Smooth completion with minimum visual duration
  const finishWithAnimation = useCallback(() => {
    const elapsed = Date.now() - processingStartTimeRef.current;
    const remaining = minVisualDurationMs - elapsed;

    if (remaining <= 0) {
      // Enough time passed, finish immediately
      flushLogs();
      setAggregatedProgress(prev => ({ ...prev, overallProgress: 100 }));
      setState('finished');
      onComplete?.();
      return;
    }

    // Animate progress to 100% over remaining time
    const startProgress = aggregatedProgress.overallProgress;
    const animationStart = Date.now();

    const animate = () => {
      const animElapsed = Date.now() - animationStart;
      const fraction = Math.min(1, animElapsed / remaining);
      const currentProgress = startProgress + (100 - startProgress) * fraction;

      setAggregatedProgress(prev => ({ ...prev, overallProgress: currentProgress }));

      if (fraction < 1) {
        visualProgressAnimationRef.current = requestAnimationFrame(animate);
      } else {
        flushLogs();
        setState('finished');
        onComplete?.();
      }
    };

    visualProgressAnimationRef.current = requestAnimationFrame(animate);
  }, [minVisualDurationMs, flushLogs, onComplete, aggregatedProgress.overallProgress]);

  // Start processing
  const startProcessing = useCallback(
    async (documents: ProcessableDocument[], level: AnonymizationLevel) => {
      if (documents.length === 0) return;

      // Reset state
      setState('processing');
      setLogs([]);
      setHasErrors(false);
      setDocumentProgress(new Map());
      totalDocsRef.current = documents.length;
      completedDocsRef.current = new Set();
      logBufferRef.current = [];
      processingStartTimeRef.current = Date.now();
      if (visualProgressAnimationRef.current) {
        cancelAnimationFrame(visualProgressAnimationRef.current);
        visualProgressAnimationRef.current = null;
      }

      // Initial log
      addLog({
        id: generateLogId(),
        timestamp: new Date(),
        level: 'info',
        message: `Iniciando procesamiento de ${documents.length} documento(s)...`,
      });

      const connections = new Map<string, ProcessingWebSocket>();

      try {
        for (const doc of documents) {
          // Initialize progress
          setDocumentProgress((prev) => {
            const next = new Map(prev);
            next.set(doc.id, {
              documentId: doc.id,
              filename: doc.filename,
              stage: 'ingesting',
              progress: 0,
            });
            return next;
          });

          // Create WebSocket
          const ws = createProgressWebSocket(doc.id);

          ws.setOnProgress((progress) => {
            console.log(`[WS Progress] ${doc.filename}: ${(progress.progress * 100).toFixed(1)}% - ${progress.stage}`);
            // Update document progress and aggregated progress atomically
            setDocumentProgress((prev) => {
              const next = new Map(prev);
              next.set(progress.documentId, {
                documentId: progress.documentId,
                filename: doc.filename,
                stage: progress.stage,
                progress: progress.progress * 100,
                currentEntity: progress.currentEntity,
              });
              // Update aggregated progress with new map
              updateAggregatedProgress(next);
              return next;
            });

            // Add log entry
            const logEntry = wsMessageToLog(progress.currentEntity, doc.filename, progress.stage);
            if (logEntry) {
              addLog(logEntry);
            }
          });

          ws.setOnComplete((docId) => {
            completedDocsRef.current.add(docId);

            // Remove from progress map and update aggregated
            setDocumentProgress((prev) => {
              const next = new Map(prev);
              next.delete(docId);
              // Update aggregated progress with new map
              updateAggregatedProgress(next);
              return next;
            });

            addLog({
              id: generateLogId(),
              timestamp: new Date(),
              level: 'success',
              message: `${doc.filename}: Procesamiento completado`,
            });

            // Check if all done
            if (completedDocsRef.current.size >= totalDocsRef.current) {
              finishWithAnimation();
            }
          });

          ws.setOnError((_docId, error) => {
            setHasErrors(true);
            addLog({
              id: generateLogId(),
              timestamp: new Date(),
              level: 'error',
              message: `${doc.filename}: ${error}`,
            });
            onError?.(error);
          });

          // Connect WebSocket FIRST, then start processing
          try {
            await ws.connect();
            console.log(`[WS] Connected for ${doc.filename}`);
          } catch {
            console.log(`[WS] Failed to connect for ${doc.filename}, continuing anyway`);
          }
          connections.set(doc.id, ws);

          // Start processing via API (after WebSocket is ready)
          await documentApi.process(doc.id, level);

          addLog({
            id: generateLogId(),
            timestamp: new Date(),
            level: 'info',
            message: `${doc.filename}: Procesamiento iniciado`,
          });
        }

        wsConnectionsRef.current = connections;
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Error desconocido';
        addLog({
          id: generateLogId(),
          timestamp: new Date(),
          level: 'error',
          message: `Error al iniciar procesamiento: ${errorMsg}`,
        });
        setHasErrors(true);
        setState('finished');
        onError?.(errorMsg);

        // Cleanup connections
        connections.forEach((ws) => ws.disconnect());
      }
    },
    [addLog, finishWithAnimation, onError, updateAggregatedProgress]
  );

  // Cancel processing
  const cancelProcessing = useCallback(() => {
    wsConnectionsRef.current.forEach((ws) => ws.disconnect());
    wsConnectionsRef.current.clear();

    addLog({
      id: generateLogId(),
      timestamp: new Date(),
      level: 'warning',
      message: 'Procesamiento cancelado por el usuario',
    });

    flushLogs();
    setState('finished');
  }, [addLog, flushLogs]);

  // Reset to idle
  const reset = useCallback(() => {
    wsConnectionsRef.current.forEach((ws) => ws.disconnect());
    wsConnectionsRef.current.clear();
    if (visualProgressAnimationRef.current) {
      cancelAnimationFrame(visualProgressAnimationRef.current);
      visualProgressAnimationRef.current = null;
    }
    setState('idle');
    setLogs([]);
    setDocumentProgress(new Map());
    setAggregatedProgress({ totalDocs: 0, completedDocs: 0, overallProgress: 0 });
    setHasErrors(false);
    totalDocsRef.current = 0;
    completedDocsRef.current = new Set();
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      wsConnectionsRef.current.forEach((ws) => ws.disconnect());
      if (visualProgressAnimationRef.current) {
        cancelAnimationFrame(visualProgressAnimationRef.current);
      }
    };
  }, []);

  return {
    // State
    state,
    logs,
    progress: aggregatedProgress,
    hasErrors,

    // Actions
    startProcessing,
    cancelProcessing,
    reset,
  };
}

export default useProcessing;
