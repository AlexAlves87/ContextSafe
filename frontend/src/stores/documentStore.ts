/**
 * Document Store - Zustand State Management
 *
 * Traceability:
 * - project_context.yaml#presentation.web.state_management: zustand
 * - Bindings: UI-BIND-001, UI-BIND-002, UI-BIND-004, UI-BIND-005
 */

import { create } from 'zustand';
import type {
  Document,
  DocumentListItem,
  DetectedEntity,
  ProcessingProgress,
  GlossaryEntry,
  ReviewSummary,
  ReviewAction,
  ExportValidation,
} from '@/types';
import { documentApi, projectApi, downloadBlob } from '@/services/api';
import {
  createProgressWebSocket,
  ProcessingWebSocket,
  WebSocketStatus,
} from '@/services/websocket';

interface DocumentState {
  // Data
  documents: DocumentListItem[];
  selectedDocument: Document | null;
  entities: DetectedEntity[];
  glossary: GlossaryEntry[];
  anonymizedContent: {
    original: string;
    anonymized: string;
  } | null;

  // Review state
  reviewSummary: ReviewSummary | null;
  isReviewing: boolean;

  // Processing state
  processingProgress: ProcessingProgress | null;
  wsConnection: ProcessingWebSocket | null;
  wsStatus: WebSocketStatus;

  // Loading states
  isLoading: boolean;
  isUploading: boolean;
  isLoadingEntities: boolean;
  isLoadingAnonymized: boolean;
  error: string | null;

  // Actions
  fetchDocuments: (projectId: string) => Promise<void>;
  selectDocument: (documentId: string) => Promise<void>;
  uploadDocument: (projectId: string, file: File) => Promise<Document>;
  deleteDocument: (documentId: string) => Promise<void>;
  fetchEntities: (documentId: string) => Promise<void>;
  fetchAnonymized: (documentId: string) => Promise<void>;
  fetchGlossary: (projectId: string) => Promise<void>;
  exportDocument: (documentId: string, format: 'pdf' | 'docx' | 'txt') => Promise<void>;
  exportGlossary: (projectId: string, format: 'csv' | 'json') => Promise<void>;
  startProcessing: (documentId: string) => Promise<void>;
  batchProcess: (documentIds: string[]) => Promise<{ started: string[]; totalStarted: number }>;
  processAllInProject: (projectId: string) => Promise<{ started: string[]; totalStarted: number }>;
  connectProgress: (documentId: string) => void;
  connectProgressAsync: (documentId: string) => Promise<void>;
  disconnectProgress: () => void;
  updateProgress: (progress: ProcessingProgress) => void;
  pollDocumentState: (documentId: string) => void;
  stopPolling: () => void;
  clearError: () => void;
  // Review actions
  reviewEntity: (documentId: string, entityId: string, action: ReviewAction, options?: {
    newCategory?: string;
    newValue?: string;
    reviewTimeMs?: number;
  }) => Promise<void>;
  batchReviewGreen: (documentId: string) => Promise<void>;
  validateExport: (documentId: string) => Promise<ExportValidation>;
  computeReviewSummary: () => void;
}

// Polling interval reference (outside store for cleanup)
let pollingIntervalId: ReturnType<typeof setInterval> | null = null;

export const useDocumentStore = create<DocumentState>((set, get) => ({
  // Initial state
  documents: [],
  selectedDocument: null,
  entities: [],
  glossary: [],
  anonymizedContent: null,
  reviewSummary: null,
  isReviewing: false,
  processingProgress: null,
  wsConnection: null,
  wsStatus: 'disconnected',
  isLoading: false,
  isUploading: false,
  isLoadingEntities: false,
  isLoadingAnonymized: false,
  error: null,

  // Actions
  fetchDocuments: async (projectId: string) => {
    set({ isLoading: true, error: null });
    try {
      const documents = await documentApi.listByProject(projectId);
      set({ documents, isLoading: false });
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : 'Failed to fetch documents',
        isLoading: false,
      });
    }
  },

  selectDocument: async (documentId: string) => {
    set({ isLoading: true, error: null });
    try {
      const document = await documentApi.getById(documentId);
      set({ selectedDocument: document, isLoading: false });
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : 'Failed to fetch document',
        isLoading: false,
      });
    }
  },

  uploadDocument: async (projectId: string, file: File) => {
    set({ isUploading: true, error: null });
    try {
      const document = await documentApi.upload(projectId, file);
      set((state) => ({
        documents: [
          ...state.documents,
          {
            id: document.id,
            filename: document.filename,
            format: document.format,
            state: document.state,
            entityCount: 0,
            createdAt: document.createdAt,
          },
        ],
        isUploading: false,
      }));
      return document;
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : 'Failed to upload document',
        isUploading: false,
      });
      throw e;
    }
  },

  deleteDocument: async (documentId: string) => {
    try {
      await documentApi.delete(documentId);
      set((state) => ({
        documents: state.documents.filter((d) => d.id !== documentId),
        selectedDocument:
          state.selectedDocument?.id === documentId ? null : state.selectedDocument,
      }));
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : 'Failed to delete document',
      });
      throw e;
    }
  },

  fetchEntities: async (documentId: string) => {
    set({ isLoadingEntities: true, error: null });
    try {
      const entities = await documentApi.getEntities(documentId);
      set({ entities, isLoadingEntities: false });
      get().computeReviewSummary();
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : 'Failed to fetch entities',
        isLoadingEntities: false,
      });
    }
  },

  fetchAnonymized: async (documentId: string) => {
    set({ isLoadingAnonymized: true, error: null });
    try {
      const result = await documentApi.getAnonymized(documentId);
      set({
        anonymizedContent: {
          original: result.originalText,
          anonymized: result.anonymizedText,
        },
        isLoadingAnonymized: false,
      });
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : 'Failed to fetch anonymized',
        isLoadingAnonymized: false,
      });
    }
  },

  fetchGlossary: async (projectId: string) => {
    try {
      const glossary = await projectApi.getGlossary(projectId);
      set({ glossary });
    } catch (e) {
      console.error('Failed to fetch glossary:', e);
    }
  },

  exportDocument: async (documentId: string, format: 'pdf' | 'docx' | 'txt') => {
    try {
      const blob = await documentApi.export(documentId, format);
      const { selectedDocument, documents } = get();
      const doc = selectedDocument || documents.find((d) => d.id === documentId);
      const baseName = doc?.filename?.replace(/\.[^/.]+$/, '') || 'document';
      downloadBlob(blob, `${baseName}_anonimizado.${format}`);
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : 'Failed to export document',
      });
      throw e;
    }
  },

  exportGlossary: async (projectId: string, format: 'csv' | 'json') => {
    try {
      const blob = await projectApi.exportGlossary(projectId, format);
      downloadBlob(blob, `glosario.${format}`);
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : 'Failed to export glossary',
      });
      throw e;
    }
  },

  startProcessing: async (documentId: string) => {
    let usePolling = false;

    try {
      // Update UI immediately to show processing started
      set((state) => ({
        documents: state.documents.map((d) =>
          d.id === documentId ? { ...d, state: 'ingesting' as const } : d
        ),
        processingProgress: {
          documentId,
          stage: 'ingesting',
          progress: 0,
        },
      }));

      // Try to connect WebSocket FIRST and WAIT for connection
      try {
        console.log('[PROCESS] Connecting WebSocket before processing...');
        await get().connectProgressAsync(documentId);
        console.log('[PROCESS] WebSocket connected, starting processing');
      } catch (wsError) {
        console.warn('[PROCESS] WebSocket failed, will use polling:', wsError);
        usePolling = true;
      }

      // NOW start processing on backend (WebSocket is ready to receive)
      await documentApi.process(documentId);

      // If WebSocket failed, use polling as fallback
      if (usePolling) {
        console.log('[PROCESS] Using polling fallback');
        get().pollDocumentState(documentId);
      }

    } catch (e) {
      get().disconnectProgress();
      set({
        error: e instanceof Error ? e.message : 'Failed to start processing',
        processingProgress: null,
      });
    }
  },

  batchProcess: async (documentIds: string[]) => {
    set({ error: null });
    try {
      const result = await documentApi.batchProcess(documentIds);

      // Update document states for started documents
      set((state) => ({
        documents: state.documents.map((d) =>
          result.started.includes(d.id)
            ? { ...d, state: 'ingesting' as const }
            : d
        ),
      }));

      return {
        started: result.started,
        totalStarted: result.totalStarted,
      };
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : 'Failed to batch process',
      });
      return { started: [], totalStarted: 0 };
    }
  },

  processAllInProject: async (projectId: string) => {
    set({ error: null });
    try {
      const result = await documentApi.processAllInProject(projectId);

      // Update document states for started documents
      set((state) => ({
        documents: state.documents.map((d) =>
          result.started.includes(d.id)
            ? { ...d, state: 'ingesting' as const }
            : d
        ),
      }));

      return {
        started: result.started,
        totalStarted: result.totalStarted,
      };
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : 'Failed to process all documents',
      });
      return { started: [], totalStarted: 0 };
    }
  },

  connectProgress: (documentId: string) => {
    // Fire-and-forget version (legacy)
    get().connectProgressAsync(documentId).catch(console.error);
  },

  connectProgressAsync: async (documentId: string): Promise<void> => {
    const { wsConnection } = get();
    if (wsConnection) {
      wsConnection.disconnect();
    }

    const ws = createProgressWebSocket(documentId);

    ws.setOnProgress((progress) => {
      console.log('[WS] Progress update:', progress);
      get().updateProgress(progress);
    });

    ws.setOnComplete((docId) => {
      console.log('[WS] Processing complete:', docId);
      set((state) => ({
        documents: state.documents.map((d) =>
          d.id === docId ? { ...d, state: 'completed' as const } : d
        ),
        processingProgress: null,
      }));
    });

    ws.setOnError((docId, error) => {
      console.error('[WS] Processing error:', docId, error);
      set((state) => ({
        documents: state.documents.map((d) =>
          d.id === docId ? { ...d, state: 'failed' as const } : d
        ),
        processingProgress: { ...state.processingProgress!, error },
      }));
    });

    ws.setOnStatusChange((status) => {
      set({ wsStatus: status });
    });

    // WAIT for connection before returning
    await ws.connect();
    set({ wsConnection: ws });
  },

  disconnectProgress: () => {
    // Stop polling
    get().stopPolling();
    // Also handle WebSocket if it exists
    const { wsConnection } = get();
    if (wsConnection) {
      wsConnection.disconnect();
      set({ wsConnection: null, wsStatus: 'disconnected' });
    }
  },

  updateProgress: (progress: ProcessingProgress) => {
    set((state) => ({
      processingProgress: progress,
      documents: state.documents.map((d) =>
        d.id === progress.documentId
          ? { ...d, state: progress.stage, progress: progress.progress }
          : d
      ),
    }));
  },

  clearError: () => set({ error: null }),

  pollDocumentState: (documentId: string) => {
    // Stop any existing polling
    if (pollingIntervalId) {
      clearInterval(pollingIntervalId);
    }

    const pollFn = async () => {
      try {
        const document = await documentApi.getById(documentId);
        set({ selectedDocument: document });

        // Use ACTUAL progress from backend, not fixed values
        // Backend sends: progress (0.0-1.0), currentEntity, state
        const actualProgress = (document as any).progress ?? 0;
        const currentEntity = (document as any).currentEntity ?? '';

        // Map state to stage for display
        const stageFromState: Record<string, string> = {
          pending: 'ingesting',
          ingesting: 'ingesting',
          detecting: 'detecting',
          anonymizing: 'anonymizing',
          completed: 'anonymizing',
          error: 'anonymizing',
        };

        const stage = stageFromState[document.state] || 'ingesting';
        // Convert 0.0-1.0 to 0-100 for display
        const progressPercent = document.state === 'completed' ? 100 : Math.round(actualProgress * 100);

        console.log(`[POLL] doc=${documentId} state=${document.state} progress=${progressPercent}% entity=${currentEntity}`);

        set({
          processingProgress: {
            documentId,
            stage: stage as any,
            progress: progressPercent,
            currentEntity: currentEntity,
          },
          wsStatus: 'connected',
        });

        // Update document in list with actual progress
        set((state) => ({
          documents: state.documents.map((d) =>
            d.id === documentId
              ? { ...d, state: document.state as any, progress: progressPercent }
              : d
          ),
        }));

        // Stop polling if completed or failed
        if (document.state === 'completed' || document.state === 'failed') {
          console.log(`[POLL] Stopping - document ${document.state}`);
          get().stopPolling();
        }
      } catch (e) {
        console.error('Polling error:', e);
      }
    };

    // Poll immediately and then every 300ms for smoother updates
    pollFn();
    pollingIntervalId = setInterval(pollFn, 300);
  },

  stopPolling: () => {
    if (pollingIntervalId) {
      clearInterval(pollingIntervalId);
      pollingIntervalId = null;
    }
    set({ wsStatus: 'disconnected' });
  },

  // Review actions
  reviewEntity: async (documentId, entityId, action, options = {}) => {
    set({ isReviewing: true });
    try {
      const result = await documentApi.reviewEntity(documentId, entityId, action, options);
      // Update entity locally (including category and alias if corrected)
      const entities = get().entities.map(e => {
        if (e.id !== entityId) return e;
        const updated = { ...e, reviewed: true, reviewAction: action };
        if (action === 'CORRECTED') {
          if (result.newCategory) {
            updated.category = result.newCategory.toLowerCase() as typeof e.category;
          }
          if (result.newAlias) {
            updated.alias = result.newAlias;
          }
        }
        return updated;
      });
      set({ entities, isReviewing: false });
      get().computeReviewSummary();
      // Re-fetch anonymized text if category was corrected (alias changed in backend)
      if (action === 'CORRECTED' && result.newAlias) {
        get().fetchAnonymized(documentId);
      }
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : 'Failed to review entity',
        isReviewing: false,
      });
    }
  },

  batchReviewGreen: async (documentId) => {
    set({ isReviewing: true });
    try {
      await documentApi.batchReview(documentId, 'GREEN', 'APPROVED');
      // Mark all GREEN entities as reviewed
      const entities = get().entities.map(e =>
        e.zone === 'GREEN'
          ? { ...e, reviewed: true, reviewAction: 'APPROVED' as const }
          : e
      );
      set({ entities, isReviewing: false });
      get().computeReviewSummary();
    } catch (e) {
      // If backend endpoint not ready, do it client-side
      const entities = get().entities.map(e =>
        e.zone === 'GREEN'
          ? { ...e, reviewed: true, reviewAction: 'APPROVED' as const }
          : e
      );
      set({ entities, isReviewing: false });
      get().computeReviewSummary();
    }
  },

  validateExport: async (documentId) => {
    try {
      return await documentApi.validateExport(documentId);
    } catch {
      // Fallback: compute from local state
      const { entities } = get();
      const total = entities.length;
      const reviewed = entities.filter(e => e.reviewed).length;
      const pendingAmberRed = entities.filter(
        e => !e.reviewed && (e.zone === 'AMBER' || e.zone === 'RED')
      ).length;
      const canExport = pendingAmberRed === 0;
      return {
        canExport,
        pendingReviews: pendingAmberRed,
        totalEntities: total,
        reviewedEntities: reviewed,
        reviewPercentage: total === 0 ? 100 : Math.round((reviewed / total) * 100),
        validationResults: [],
        warnings: [],
      };
    }
  },

  computeReviewSummary: () => {
    const entities = get().entities;
    const total = entities.length;
    const reviewed = entities.filter(e => e.reviewed).length;
    const pending = total - reviewed;
    const pendingAmberRed = entities.filter(
      e => !e.reviewed && (e.zone === 'AMBER' || e.zone === 'RED')
    ).length;
    const greenCount = entities.filter(e => e.zone === 'GREEN').length;
    const amberCount = entities.filter(e => e.zone === 'AMBER').length;
    const redCount = entities.filter(e => e.zone === 'RED').length;

    set({
      reviewSummary: {
        total,
        reviewed,
        pending,
        pendingAmberRed,
        byZone: { GREEN: greenCount, AMBER: amberCount, RED: redCount },
        reviewPercentage: total === 0 ? 100 : Math.round((reviewed / total) * 100),
        canExport: pendingAmberRed === 0,
        exportBlockedReason: pendingAmberRed > 0
          ? `${pendingAmberRed} entidades (ámbar/rojo) pendientes de revisión`
          : '',
      },
    });
  },
}));
