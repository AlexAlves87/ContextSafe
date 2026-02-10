/**
 * ProcessingScreen - Project-level batch processing configuration
 *
 * Traceability:
 * - Contract: CNT-UI-SCREEN-002
 * - Route: /projects/:projectId/process
 *
 * ASCII Layout Reference (from project_context.yaml):
 * ┌─────────────────────────────────────────────────┐
 * │  Configurar Procesamiento                       │
 * ├─────────────────────────────────────────────────┤
 * │  🔧 Hardware detectado:                         │
 * │     ✓ NVIDIA RTX 4060 8GB VRAM                  │
 * │     ✓ 32GB RAM disponible                       │
 * │     → Modo: GPU (recomendado)                   │
 * │        [▼] [GPU] [CPU] [CPU Light]              │
 * │                                                 │
 * │  🎚️ Nivel de anonimización:                     │
 * │     (•) Básico - Solo datos críticos            │
 * │     (•) Intermedio - Todo PII [RECOMENDADO]     │
 * │     ( ) Avanzado - Máxima privacidad            │
 * │                                                 │
 * │  🔍 Opciones avanzadas:                         │
 * │     [✓] Mantener consistencia entre documentos  │
 * │     [✓] Preservar formato original              │
 * │     [ ] Generar informe de auditoría            │
 * │                                                 │
 * │  [🔄 Procesar ahora]  [💾 Programar batch]      │
 * └─────────────────────────────────────────────────┘
 */

import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import {
  LoadingSpinner,
  ProcessingProgress,
} from '@/components';
import { useProjectStore, useDocumentStore, useUIStore } from '@/stores';
import { documentApi, systemApi } from '@/services/api';
import { createProgressWebSocket, ProcessingWebSocket } from '@/services/websocket';
import type { AnonymizationLevel, ComputeMode, HardwareInfo, ProcessingStage } from '@/types';

export const ProcessingScreen: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const { selectedProject, selectProject } = useProjectStore();
  const {
    documents,
    fetchDocuments,
    isLoading,
  } = useDocumentStore();
  const { addToast } = useUIStore();

  // Local state
  const [computeMode, setComputeMode] = useState<ComputeMode>('cpu');
  const [anonymizationLevel, setAnonymizationLevel] = useState<AnonymizationLevel>('intermediate');
  const [options, setOptions] = useState({
    maintainConsistency: true,
    preserveFormatting: true,
    generateAuditReport: false,
  });
  const [isProcessing, setIsProcessing] = useState(false);
  const [hardwareLoading, setHardwareLoading] = useState(true);
  const [hardwareInfo, setHardwareInfo] = useState<HardwareInfo | null>(null);
  const [isChangingMode, setIsChangingMode] = useState(false);
  const [documentProgress, setDocumentProgress] = useState<Record<string, {
    stage: ProcessingStage;
    progress: number;
    currentEntity?: string;
  }>>({});
  const wsConnectionsRef = useRef<Map<string, ProcessingWebSocket>>(new Map());
  const [includeCompleted, setIncludeCompleted] = useState(false);

  // Load hardware info
  useEffect(() => {
    const loadHardware = async () => {
      try {
        const info = await systemApi.getHardware();
        setHardwareInfo(info);
        setComputeMode(info.current_mode);
      } catch (error) {
        console.error('Failed to load hardware info:', error);
        // Keep defaults
      } finally {
        setHardwareLoading(false);
      }
    };
    loadHardware();
  }, []);

  // Change compute mode
  const handleSetComputeMode = async (mode: ComputeMode) => {
    if (mode === computeMode || !hardwareInfo) return;

    setIsChangingMode(true);
    try {
      const result = await systemApi.setComputeMode(mode);
      setComputeMode(result.effective);
      addToast({
        type: 'success',
        message: `Modo cambiado a ${mode.toUpperCase()}`,
      });
    } catch (error) {
      addToast({
        type: 'error',
        message: 'Error al cambiar modo de cómputo',
      });
    } finally {
      setIsChangingMode(false);
    }
  };

  // Load project and documents
  useEffect(() => {
    if (projectId) {
      selectProject(projectId);
      fetchDocuments(projectId);
    }
  }, [projectId, selectProject, fetchDocuments]);

  // Auto-enable reprocessing if no pending docs but have processable docs
  useEffect(() => {
    const pendingCount = documents.filter(d => d.state === 'pending').length;
    const processableCount = documents.filter(d =>
      !['ingesting', 'detecting', 'anonymizing'].includes(d.state)
    ).length;

    if (pendingCount === 0 && processableCount > 0) {
      setIncludeCompleted(true);
    }
  }, [documents]);

  // Limpiar conexiones WebSocket cuando se desmonta el componente
  useEffect(() => {
    return () => {
      wsConnectionsRef.current.forEach(ws => ws.disconnect());
    };
  }, []);

  // Detectar cuando todos los documentos terminan
  useEffect(() => {
    const processingCount = documents.filter(d =>
      ['ingesting', 'detecting', 'anonymizing'].includes(d.state)
    ).length;

    const allComplete = processingCount === 0 &&
      Object.values(documentProgress).every(p => p.progress >= 100);

    if (isProcessing && allComplete && wsConnectionsRef.current.size > 0) {
      setIsProcessing(false);
      wsConnectionsRef.current.forEach(ws => ws.disconnect());
      wsConnectionsRef.current = new Map();
      addToast({ type: 'success', message: 'Todos los documentos han sido procesados' });
    }
  }, [documents, documentProgress, isProcessing, addToast]);

  // Get documents by state (DESPUÉS de todos los hooks)
  const pendingDocs = documents.filter(d => d.state === 'pending');

  // ALL documents that can be (re)processed = everything not currently processing
  const processableDocs = documents.filter(d =>
    !['ingesting', 'detecting', 'anonymizing'].includes(d.state)
  );

  // Documents to process
  const docsToProcess = includeCompleted ? processableDocs : pendingDocs;

  // Delete a document
  const handleDeleteDocument = useCallback(async (docId: string, docName: string) => {
    if (!confirm(`¿Eliminar "${docName}"? Esta acción no se puede deshacer.`)) return;

    try {
      await documentApi.delete(docId);
      addToast({
        type: 'success',
        message: `Documento "${docName}" eliminado`,
      });
      if (projectId) {
        fetchDocuments(projectId);
      }
    } catch (error) {
      addToast({
        type: 'error',
        message: `Error al eliminar "${docName}"`,
      });
    }
  }, [addToast, fetchDocuments, projectId]);

  // Process all selected documents (pending + optionally completed)
  const handleProcessAll = useCallback(async () => {
    if (!projectId || docsToProcess.length === 0) return;

    setIsProcessing(true);
    const connections = new Map<string, ProcessingWebSocket>();

    try {
      for (const doc of docsToProcess) {
        // Iniciar con progreso 0
        setDocumentProgress(prev => ({
          ...prev,
          [doc.id]: { stage: 'ingesting' as ProcessingStage, progress: 0, currentEntity: 'Iniciando...' }
        }));

        // Crear conexión WebSocket
        const ws = createProgressWebSocket(doc.id);

        ws.setOnProgress((progress) => {
          setDocumentProgress(prev => ({
            ...prev,
            [progress.documentId]: {
              stage: progress.stage,
              progress: progress.progress * 100,
              currentEntity: progress.currentEntity,
            }
          }));
        });

        ws.setOnComplete((docId) => {
          setDocumentProgress(prev => {
            const next = { ...prev };
            delete next[docId];
            return next;
          });
          fetchDocuments(projectId);
        });

        ws.setOnError((docId, error) => {
          console.error(`Error processing ${docId}:`, error);
          setDocumentProgress(prev => {
            const next = { ...prev };
            delete next[docId];
            return next;
          });
          addToast({ type: 'error', message: error });
        });

        // Conectar WebSocket (no esperar, es async)
        ws.connect().catch(() => {
          console.log('[WS] Connection failed, using polling');
        });
        connections.set(doc.id, ws);

        // Iniciar procesamiento
        await documentApi.process(doc.id, anonymizationLevel);
      }

      wsConnectionsRef.current = connections;
      addToast({
        type: 'success',
        message: `Procesamiento iniciado para ${docsToProcess.length} documentos`,
      });

    } catch (error) {
      addToast({
        type: 'error',
        message: 'Error al iniciar el procesamiento',
      });
      setIsProcessing(false);
      // Cerrar conexiones en caso de error
      connections.forEach(ws => ws.disconnect());
    }
  }, [projectId, docsToProcess, anonymizationLevel, documents, fetchDocuments, addToast]);

  if (isLoading || !selectedProject) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" label="Cargando proyecto..." />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(`/projects/${projectId}`)}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
          <div>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              Configurar Procesamiento
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {selectedProject.name} · {pendingDocs.length} documentos pendientes
            </p>
          </div>
        </div>
      </div>

      {/* Hardware Detection */}
      <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <span>🔧</span> Hardware detectado
        </h2>
        {hardwareLoading ? (
          <div className="flex items-center gap-2 text-gray-500">
            <LoadingSpinner size="sm" />
            <span>Detectando hardware...</span>
          </div>
        ) : hardwareInfo ? (
        <div className="space-y-4">
          {/* Hardware Info */}
          <div className="space-y-2 text-sm">
            {hardwareInfo.gpu.available ? (
              <p className="flex items-center gap-2 text-success-600 dark:text-success-400">
                <span>✓</span> GPU: {hardwareInfo.gpu.name} ({hardwareInfo.gpu.vram_gb}GB VRAM, {hardwareInfo.gpu.vram_free_gb.toFixed(1)}GB libres)
              </p>
            ) : (
              <p className="flex items-center gap-2 text-gray-500">
                <span>✗</span> No se detectó GPU compatible
              </p>
            )}
            <p className="flex items-center gap-2 text-success-600 dark:text-success-400">
              <span>✓</span> CPU: {hardwareInfo.cpu.name} ({hardwareInfo.cpu.cores} cores)
            </p>
            <p className="flex items-center gap-2 text-success-600 dark:text-success-400">
              <span>✓</span> RAM: {hardwareInfo.ram.total_gb.toFixed(1)}GB total, {hardwareInfo.ram.available_gb.toFixed(1)}GB disponible
            </p>
          </div>

          {/* Compute Mode Selector */}
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600 dark:text-gray-400">Modo de cómputo:</span>
            <div className="flex rounded-lg border border-gray-300 dark:border-gray-600 overflow-hidden">
              <button
                onClick={() => handleSetComputeMode('gpu')}
                disabled={!hardwareInfo.gpu.available || isChangingMode}
                className={clsx(
                  'px-4 py-2 text-sm font-medium transition-colors',
                  computeMode === 'gpu'
                    ? 'bg-primary-500 text-white'
                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700',
                  !hardwareInfo.gpu.available && 'opacity-50 cursor-not-allowed'
                )}
              >
                GPU
                {hardwareInfo.recommended_mode === 'gpu' && hardwareInfo.gpu.available && (
                  <span className="ml-1 text-xs">✨</span>
                )}
              </button>
              <button
                onClick={() => handleSetComputeMode('cpu')}
                disabled={isChangingMode}
                className={clsx(
                  'px-4 py-2 text-sm font-medium transition-colors border-l border-gray-300 dark:border-gray-600',
                  computeMode === 'cpu'
                    ? 'bg-primary-500 text-white'
                    : 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
                )}
              >
                CPU
                {hardwareInfo.recommended_mode === 'cpu' && (
                  <span className="ml-1 text-xs">✨</span>
                )}
              </button>
            </div>
            {hardwareInfo.recommended_mode && (
              <span className="text-xs text-gray-500 dark:text-gray-400">
                (✨ = recomendado)
              </span>
            )}
          </div>
        </div>
        ) : null}
      </div>

      {/* Anonymization Level */}
      <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <span>🎚️</span> Nivel de anonimización
        </h2>
        <div className="space-y-3">
          {([
            { value: 'basic', label: 'Básico', desc: 'Enmascaramiento con asteriscos (****). Rápido pero irreversible.' },
            { value: 'intermediate', label: 'Intermedio', desc: 'Pseudónimos consistentes (Persona_001). Reversible.', recommended: true },
            { value: 'advanced', label: 'Avanzado', desc: 'Datos sintéticos con IA. Máxima naturalidad, reversible.' },
          ] as const).map((level) => (
            <label
              key={level.value}
              className={clsx(
                'flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-colors',
                anonymizationLevel === level.value
                  ? 'bg-primary-50 dark:bg-primary-900/20 border border-primary-200 dark:border-primary-800'
                  : 'hover:bg-gray-50 dark:hover:bg-gray-800 border border-transparent'
              )}
            >
              <input
                type="radio"
                name="anonymizationLevel"
                value={level.value}
                checked={anonymizationLevel === level.value}
                onChange={() => setAnonymizationLevel(level.value)}
                className="mt-1 text-primary-500 focus:ring-primary-500"
              />
              <div>
                <span className="font-medium text-gray-900 dark:text-white">
                  {level.label}
                  {'recommended' in level && level.recommended && (
                    <span className="ml-2 text-xs px-2 py-0.5 bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 rounded">
                      RECOMENDADO
                    </span>
                  )}
                </span>
                <p className="text-sm text-gray-500 dark:text-gray-400">{level.desc}</p>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Advanced Options */}
      <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <span>🔍</span> Opciones avanzadas
        </h2>
        <div className="space-y-3">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={options.maintainConsistency}
              onChange={(e) => setOptions(prev => ({ ...prev, maintainConsistency: e.target.checked }))}
              className="w-4 h-4 text-primary-500 rounded focus:ring-primary-500"
            />
            <span className="text-gray-700 dark:text-gray-300">Mantener consistencia entre documentos</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={options.preserveFormatting}
              onChange={(e) => setOptions(prev => ({ ...prev, preserveFormatting: e.target.checked }))}
              className="w-4 h-4 text-primary-500 rounded focus:ring-primary-500"
            />
            <span className="text-gray-700 dark:text-gray-300">Preservar formato original</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={options.generateAuditReport}
              onChange={(e) => setOptions(prev => ({ ...prev, generateAuditReport: e.target.checked }))}
              className="w-4 h-4 text-primary-500 rounded focus:ring-primary-500"
            />
            <span className="text-gray-700 dark:text-gray-300">Generar informe de auditoría</span>
          </label>
          {processableDocs.length > 0 && (
            <label className="flex items-center gap-3 cursor-pointer mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <input
                type="checkbox"
                checked={includeCompleted}
                onChange={(e) => setIncludeCompleted(e.target.checked)}
                className="w-4 h-4 text-warning-500 rounded focus:ring-warning-500"
              />
              <span className="text-gray-700 dark:text-gray-300">
                <strong>Reprocesar</strong> todos los documentos ({processableDocs.length} disponibles)
              </span>
            </label>
          )}
        </div>
      </div>

      {/* Documents to Process - with delete option */}
      {docsToProcess.length > 0 && (
        <div className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <span>📄</span> Documentos a procesar ({docsToProcess.length})
          </h2>
          <div className="space-y-2">
            {docsToProcess.map((doc) => (
              <div
                key={doc.id}
                className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-800 rounded-lg"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <svg className="w-5 h-5 text-gray-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                  </svg>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {doc.filename}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {doc.state === 'completed' ? 'Completado - se reprocesará' : 'Pendiente'}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleDeleteDocument(doc.id, doc.filename)}
                  disabled={isProcessing}
                  className="flex items-center gap-1 px-3 py-1.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors disabled:opacity-50"
                  title="Eliminar documento"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  Eliminar
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Processing Status - Only show when actively processing */}
      {Object.entries(documentProgress).filter(([_, p]) => p.progress < 100).length > 0 && (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Procesando...
          </h2>
          <div className="space-y-4">
            {Object.entries(documentProgress)
              .filter(([_, progress]) => progress.progress < 100)
              .map(([docId, progress]) => {
                const doc = documents.find(d => d.id === docId);
                const filename = doc?.filename || `Documento ${docId.slice(0, 8)}`;

                return (
                  <div key={docId}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {filename}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400 truncate max-w-[200px]">
                        {progress?.currentEntity || ''}
                      </span>
                    </div>
                    <ProcessingProgress
                      progress={progress?.progress || 0}
                      stage={progress?.stage || 'ingesting'}
                    />
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center gap-4">
        <button
          onClick={handleProcessAll}
          disabled={isProcessing || docsToProcess.length === 0}
          className={clsx(
            'flex items-center gap-2 px-6 py-3 rounded-lg font-medium transition-colors',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
            isProcessing || docsToProcess.length === 0
              ? 'bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed'
              : includeCompleted
                ? 'bg-warning-500 text-white hover:bg-warning-600'
                : 'bg-primary-500 text-white hover:bg-primary-600'
          )}
        >
          {isProcessing ? (
            <>
              <LoadingSpinner size="sm" />
              Procesando...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1z"
                  clipRule="evenodd"
                />
              </svg>
              {includeCompleted ? 'Reprocesar' : 'Procesar'} ahora ({docsToProcess.length} docs)
            </>
          )}
        </button>
        <button
          onClick={() => navigate(`/projects/${projectId}`)}
          className="px-6 py-3 rounded-lg font-medium border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
        >
          Volver al proyecto
        </button>
      </div>
    </div>
  );
};

export default ProcessingScreen;
