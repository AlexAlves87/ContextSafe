/**
 * API Service - REST Client
 *
 * Traceability:
 * - Binding Contracts: UI-BIND-001 to UI-BIND-009
 * - Endpoints defined in tier4_api_contracts.yaml
 */

import type {
  Project,
  Document,
  DocumentListItem,
  DetectedEntity,
  GlossaryEntry,
  ProjectSettings,
  ExportFormat,
  HardwareInfo,
  ComputeModeResponse,
  ComputeMode,
  ReviewAction,
  ReviewSummary,
  ExportValidation,
  ConfidenceZone,
} from '@/types';

const API_BASE = '/api/v1';

/**
 * Get auth token from localStorage (zustand persist)
 */
function getAuthToken(): string | null {
  try {
    const stored = localStorage.getItem('contextsafe-auth');
    if (stored) {
      const parsed = JSON.parse(stored);
      return parsed?.state?.token || null;
    }
  } catch {
    // Ignore parsing errors
  }
  return null;
}

/**
 * Handle auth errors (401) - logout user
 */
function handleAuthError() {
  // Aplicacion local: no hay login, solo limpiar estado
  localStorage.removeItem('contextsafe-auth');
}

/**
 * Generic fetch wrapper with error handling and auth
 */
async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const token = getAuthToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options?.headers as Record<string, string>),
  };

  // Add auth token if available
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  // Handle 401 Unauthorized
  if (response.status === 401) {
    handleAuthError();
    throw new Error('Session expired');
  }

  // Handle 403 Forbidden (doc limit during login)
  if (response.status === 403) {
    const error = await response.json().catch(() => ({
      detail: 'Límite de documentos alcanzado',
    }));
    // Create a specific error type for doc limit
    const limitError = new Error(error.detail || 'Límite de documentos alcanzado');
    (limitError as any).status = 403;
    (limitError as any).isDocLimitReached = true;
    throw limitError;
  }

  // Handle 429 Too Many Requests (doc limit)
  if (response.status === 429) {
    const error = await response.json().catch(() => ({
      detail: 'Límite de documentos alcanzado',
    }));
    const limitError = new Error(error.detail || 'Límite alcanzado');
    (limitError as any).status = 429;
    (limitError as any).isDocLimitReached = true;
    throw limitError;
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      code: 'UNKNOWN_ERROR',
      message: 'An unexpected error occurred',
    }));
    throw new Error(error.message || error.detail || 'Request failed');
  }

  return response.json();
}

// ============================================================================
// AXIOS-LIKE API OBJECT
// ============================================================================
export const api = {
  async get<T = unknown>(url: string, config?: { responseType?: string; params?: Record<string, string> }): Promise<{ data: T }> {
    let fullUrl = url.startsWith('/api') ? url : `${API_BASE}${url}`;

    // Add query params
    if (config?.params) {
      const params = new URLSearchParams(config.params);
      fullUrl += (fullUrl.includes('?') ? '&' : '?') + params.toString();
    }

    const token = getAuthToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(fullUrl, { headers });

    if (response.status === 401) {
      handleAuthError();
      throw new Error('Session expired');
    }

    if (!response.ok) {
      throw new Error('Request failed');
    }

    if (config?.responseType === 'blob') {
      return { data: await response.blob() as T };
    }

    return { data: await response.json() };
  },

  async post<T = unknown>(url: string, data?: unknown): Promise<{ data: T }> {
    const fullUrl = url.startsWith('/api') ? url : `${API_BASE}${url}`;
    const token = getAuthToken();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(fullUrl, {
      method: 'POST',
      headers,
      body: data ? JSON.stringify(data) : undefined,
    });

    if (response.status === 401) {
      handleAuthError();
      throw new Error('Session expired');
    }

    // Handle 403 Forbidden (doc limit during login)
    if (response.status === 403) {
      const error = await response.json().catch(() => ({
        detail: 'Límite de documentos alcanzado',
      }));
      const limitError = new Error(error.detail || 'Límite de documentos alcanzado');
      (limitError as any).status = 403;
      (limitError as any).isDocLimitReached = true;
      throw limitError;
    }

    // Handle 429 Too Many Requests (doc limit)
    if (response.status === 429) {
      const error = await response.json().catch(() => ({
        detail: 'Límite de documentos alcanzado',
      }));
      const limitError = new Error(error.detail || 'Límite de documentos alcanzado');
      (limitError as any).status = 429;
      (limitError as any).isDocLimitReached = true;
      throw limitError;
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || error.message || 'Request failed');
    }

    return { data: await response.json() };
  },
};

// ============================================================================
// PROJECT API
// ============================================================================

export const projectApi = {
  /**
   * List all projects
   * Binding: UI-BIND-007
   * Response format: {data: Project[], meta: {total, limit, offset}}
   */
  async list(): Promise<Project[]> {
    const response = await apiFetch<{data: Project[], meta: {total: number}}>('/projects');
    return response.data;
  },

  /**
   * Get project by ID
   * Response format: {data: Project}
   */
  async getById(projectId: string): Promise<Project> {
    const response = await apiFetch<{data: Project}>(
      `/projects/${projectId}`
    );
    return response.data;
  },

  /**
   * Create new project
   * Binding: UI-BIND-007 (onCreate)
   * Response format: {data: Project}
   */
  async create(data: {
    name: string;
    description?: string;
    anonymizationLevel?: string;
  }): Promise<Project> {
    const response = await apiFetch<{data: Project}>('/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response.data;
  },

  /**
   * Get project settings
   * Binding: UI-BIND-008
   */
  async getSettings(projectId: string): Promise<ProjectSettings> {
    const response = await apiFetch<{data: ProjectSettings}>(
      `/projects/${projectId}/settings`
    );
    return response.data;
  },

  /**
   * Update project settings
   * Binding: UI-BIND-008 (onSave)
   */
  async updateSettings(
    projectId: string,
    settings: Partial<ProjectSettings>
  ): Promise<ProjectSettings> {
    const response = await apiFetch<{data: ProjectSettings}>(
      `/projects/${projectId}/settings`,
      {
        method: 'PUT',
        body: JSON.stringify(settings),
      }
    );
    return response.data;
  },

  /**
   * Update project metadata
   */
  async update(
    projectId: string,
    data: { name: string; description?: string; anonymizationLevel?: string }
  ): Promise<Project> {
    const response = await apiFetch<{data: Project}>(
      `/projects/${projectId}`,
      {
        method: 'PUT',
        body: JSON.stringify({
          name: data.name,
          description: data.description,
          default_anonymization_level: data.anonymizationLevel || 'INTERMEDIATE',
        }),
      }
    );
    return response.data;
  },

  /**
   * Delete project
   */
  async delete(projectId: string): Promise<void> {
    const token = getAuthToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    await fetch(`${API_BASE}/projects/${projectId}`, {
      method: 'DELETE',
      headers,
    });
  },

  /**
   * Export project glossary
   */
  async exportGlossary(
    projectId: string,
    format: 'csv' | 'json' = 'csv'
  ): Promise<Blob> {
    const token = getAuthToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(
      `${API_BASE}/projects/${projectId}/export/glossary?format=${format}`,
      { method: 'GET', headers }
    );
    if (!response.ok) {
      throw new Error('Export glossary failed');
    }
    return response.blob();
  },

  /**
   * Get project glossary
   * Binding: UI-BIND-006
   */
  async getGlossary(projectId: string): Promise<GlossaryEntry[]> {
    const response = await apiFetch<{data: Array<{
      id: string;
      originalText: string;
      alias: string;
      category: string;
      occurrences: number;
      createdAt: string;
    }>}>(
      `/projects/${projectId}/glossary`
    );
    // Backend already returns camelCase
    return response.data.map(e => ({
      id: e.id,
      projectId: projectId,
      originalText: e.originalText,
      alias: e.alias,
      category: e.category.toLowerCase() as GlossaryEntry['category'],
      occurrenceCount: e.occurrences,
    }));
  },

  /**
   * Update glossary aliases
   * Binding: UI-BIND-006 (onSave)
   *
   * Allows users to customize aliases in the glossary.
   * Changes persist globally at project level.
   */
  async updateGlossary(
    projectId: string,
    changes: Array<{
      originalTerm: string;
      category: string;
      newAlias: string;
      newCategory?: string;
    }>,
    documentId?: string,
    deletions?: string[] // List of entry IDs to delete
  ): Promise<{
    changesApplied: number;
    changesFailed: number;
    deletionsApplied: number;
    mergedCount: number;
    documentRegenerated: boolean;
    anonymizedText?: string;
  }> {
    const response = await apiFetch<{
      data: {
        project_id: string;
        changes_applied: number;
        changes_failed: number;
        deletions_applied: number;
        merged_count: number;
        document_regenerated: boolean;
        anonymized_text?: string;
      };
    }>(`/projects/${projectId}/glossary`, {
      method: 'PUT',
      body: JSON.stringify({
        changes: changes.map(c => ({
          original_term: c.originalTerm,
          category: c.category.toUpperCase(),
          new_alias: c.newAlias,
          new_category: c.newCategory?.toUpperCase(),
        })),
        deletions: deletions || [],
        document_id: documentId,
      }),
    });

    return {
      changesApplied: response.data.changes_applied,
      changesFailed: response.data.changes_failed,
      deletionsApplied: response.data.deletions_applied,
      mergedCount: response.data.merged_count || 0,
      documentRegenerated: response.data.document_regenerated,
      anonymizedText: response.data.anonymized_text,
    };
  },

  /**
   * Correct glossary entries (fix detection boundaries)
   *
   * Allows users to fix incorrect text detection boundaries.
   * For example, if "también Ezten lo" was detected but only "Ezten" should be,
   * this allows correcting the original text.
   */
  async correctGlossaryEntries(
    projectId: string,
    changes: Array<{
      entryId: string;
      oldOriginalText: string;
      newOriginalText: string;
      category: string;
      alias: string;
    }>,
    documentId?: string
  ): Promise<{
    changesApplied: number;
    changesFailed: number;
    documentRegenerated: boolean;
  }> {
    const response = await apiFetch<{
      data: {
        project_id: string;
        changes_applied: number;
        changes_failed: number;
        document_regenerated: boolean;
      };
    }>(`/projects/${projectId}/glossary/correct`, {
      method: 'POST',
      body: JSON.stringify({
        corrections: changes.map(c => ({
          entry_id: c.entryId,
          old_original_text: c.oldOriginalText,
          new_original_text: c.newOriginalText,
          category: c.category.toUpperCase(),
          alias: c.alias,
        })),
        document_id: documentId,
      }),
    });

    return {
      changesApplied: response.data.changes_applied,
      changesFailed: response.data.changes_failed,
      documentRegenerated: response.data.document_regenerated,
    };
  },
};

// ============================================================================
// DOCUMENT API
// ============================================================================

export const documentApi = {
  /**
   * List documents by project
   * Binding: UI-BIND-002
   * Contract: GET /api/v1/projects/:projectId/documents
   */
  async listByProject(projectId: string): Promise<DocumentListItem[]> {
    const response = await apiFetch<{data: DocumentListItem[], meta: {total: number}}>(
      `/projects/${projectId}/documents`
    );
    return response.data;
  },

  /**
   * Get document by ID
   */
  async getById(documentId: string): Promise<Document> {
    const response = await apiFetch<{data: Document}>(
      `/documents/${documentId}`
    );
    return response.data;
  },

  /**
   * Upload document
   * Binding: UI-BIND-001
   */
  async upload(projectId: string, file: File): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);

    const token = getAuthToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE}/documents?project_id=${projectId}`, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (response.status === 401) {
      handleAuthError();
      throw new Error('Session expired');
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        message: 'Upload failed',
      }));
      throw new Error(error.message);
    }

    const result: {data: Document} = await response.json();
    return result.data;
  },

  /**
   * Get detected entities for document
   * Binding: UI-BIND-004
   * Contract: GET /api/v1/documents/:id/entities
   */
  async getEntities(documentId: string): Promise<DetectedEntity[]> {
    const response = await apiFetch<{data: Array<{
      id: string;
      document_id: string;
      category: string;
      original_text: string;
      alias?: string;
      confidence: number;
      start_offset: number;
      end_offset: number;
      zone?: string;
      zone_reason?: string;
      reviewed?: boolean;
      review_action?: string | null;
    }>}>(
      `/documents/${documentId}/entities`
    );
    // Transform snake_case to camelCase + compute zone if not provided
    return response.data.map(e => {
      // Compute zone client-side if backend doesn't provide it yet
      const confidence = e.confidence;
      const fallbackZone: ConfidenceZone =
        confidence >= 0.85 ? 'GREEN' : confidence >= 0.40 ? 'AMBER' : 'RED';
      const fallbackReason =
        confidence >= 0.85 ? `High confidence (${Math.round(confidence * 100)}%)`
        : confidence >= 0.40 ? `Medium confidence (${Math.round(confidence * 100)}%)`
        : `Low confidence (${Math.round(confidence * 100)}%)`;

      return {
        id: e.id,
        documentId: e.document_id,
        category: e.category.toLowerCase().replace(/_/g, '_') as DetectedEntity['category'],
        originalText: e.original_text,
        alias: e.alias,
        confidence: e.confidence,
        startOffset: e.start_offset,
        endOffset: e.end_offset,
        zone: (e.zone as ConfidenceZone) || fallbackZone,
        zoneReason: e.zone_reason || fallbackReason,
        reviewed: e.reviewed ?? false,
        reviewAction: (e.review_action as ReviewAction) ?? null,
      };
    });
  },

  /**
   * Review a single entity (approve/reject/correct)
   */
  async reviewEntity(
    documentId: string,
    entityId: string,
    action: ReviewAction,
    options?: {
      newCategory?: string;
      newValue?: string;
      reviewTimeMs?: number;
    }
  ): Promise<{ entityId: string; action: ReviewAction; reviewSummary: ReviewSummary; newAlias?: string; newCategory?: string }> {
    const response = await apiFetch<{
      data: {
        entityId: string;
        action: string;
        reviewSummary: ReviewSummary;
        newAlias?: string;
        newCategory?: string;
      };
    }>(`/documents/${documentId}/entities/${entityId}/review`, {
      method: 'POST',
      body: JSON.stringify({
        action,
        newCategory: options?.newCategory ?? null,
        newValue: options?.newValue ?? null,
        reviewTimeMs: options?.reviewTimeMs ?? 0,
      }),
    });
    return {
      entityId: response.data.entityId,
      action: response.data.action as ReviewAction,
      reviewSummary: response.data.reviewSummary,
      newAlias: response.data.newAlias,
      newCategory: response.data.newCategory,
    };
  },

  /**
   * Batch review all entities in a zone
   */
  async batchReview(
    documentId: string,
    zone: ConfidenceZone,
    action: ReviewAction = 'APPROVED'
  ): Promise<{ entitiesApproved: number; reviewSummary: ReviewSummary }> {
    const response = await apiFetch<{
      data: {
        entitiesApproved: number;
        zone: string;
        reviewSummary: ReviewSummary;
      };
    }>(`/documents/${documentId}/entities/batch-review`, {
      method: 'POST',
      body: JSON.stringify({ zone, action }),
    });
    return {
      entitiesApproved: response.data.entitiesApproved,
      reviewSummary: response.data.reviewSummary,
    };
  },

  /**
   * Validate export readiness
   */
  async validateExport(documentId: string): Promise<ExportValidation> {
    const response = await apiFetch<{ data: ExportValidation }>(
      `/documents/${documentId}/export/validate`,
      { method: 'POST' }
    );
    return response.data;
  },

  /**
   * Get anonymized document content
   * Binding: UI-BIND-005
   */
  async getAnonymized(
    documentId: string
  ): Promise<{ originalText: string; anonymizedText: string }> {
    const response = await apiFetch<
      {data: { originalText: string; anonymizedText: string }}
    >(`/documents/${documentId}/anonymized`);
    return response.data;
  },

  /**
   * Export document
   * Binding: UI-BIND-009
   */
  async export(
    documentId: string,
    format: ExportFormat
  ): Promise<Blob> {
    const token = getAuthToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(
      `${API_BASE}/documents/${documentId}/export/advanced?format=${format}`,
      {
        method: 'POST',
        headers,
      }
    );

    if (!response.ok) {
      throw new Error('Export failed');
    }

    return response.blob();
  },

  /**
   * Delete document
   */
  async delete(documentId: string): Promise<void> {
    const token = getAuthToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    await fetch(`${API_BASE}/documents/${documentId}`, {
      method: 'DELETE',
      headers,
    });
  },

  /**
   * Trigger processing for document
   */
  async process(documentId: string, anonymizationLevel?: string): Promise<void> {
    const params = anonymizationLevel
      ? `?level=${encodeURIComponent(anonymizationLevel.toUpperCase())}`
      : '';
    await apiFetch(`/documents/${documentId}/process${params}`, {
      method: 'POST',
    });
  },

  /**
   * Manually anonymize selected text
   *
   * Allows users to anonymize text that wasn't detected automatically,
   * such as professional IDs, case numbers, etc.
   */
  async anonymizeSelection(
    documentId: string,
    text: string,
    category: string,
    alias?: string
  ): Promise<{
    success: boolean;
    text: string;
    alias: string;
    category: string;
    anonymizedText: string;
    message: string;
  }> {
    const params = new URLSearchParams({
      text,
      category,
    });
    if (alias) {
      params.append('alias', alias);
    }

    const response = await apiFetch<{
      data: {
        success: boolean;
        text: string;
        alias: string;
        category: string;
        anonymized_text: string;
        message: string;
      };
    }>(`/documents/${documentId}/anonymize-selection?${params.toString()}`, {
      method: 'POST',
    });

    return {
      success: response.data.success,
      text: response.data.text,
      alias: response.data.alias,
      category: response.data.category,
      anonymizedText: response.data.anonymized_text,
      message: response.data.message,
    };
  },

  /**
   * Batch process multiple documents
   * Binding: UI-BIND-010 (BatchProcessing)
   */
  async batchProcess(documentIds: string[]): Promise<{
    started: string[];
    skipped: Array<{ id: string; reason: string }>;
    notFound: string[];
    totalStarted: number;
  }> {
    const params = new URLSearchParams();
    documentIds.forEach(id => params.append('document_ids', id));

    const response = await apiFetch<{
      data: {
        started: string[];
        skipped: Array<{ id: string; reason: string }>;
        not_found: string[];
        total_started: number;
      };
    }>(`/documents/batch/process?${params.toString()}`, {
      method: 'POST',
    });

    return {
      started: response.data.started,
      skipped: response.data.skipped,
      notFound: response.data.not_found,
      totalStarted: response.data.total_started,
    };
  },

  /**
   * Process all pending documents in a project
   * Binding: UI-BIND-011 (ProcessAllProject)
   */
  async processAllInProject(projectId: string): Promise<{
    projectId: string;
    started: string[];
    totalStarted: number;
    totalPending: number;
  }> {
    const response = await apiFetch<{
      data: {
        project_id: string;
        started: string[];
        total_started: number;
        total_pending: number;
      };
    }>(`/documents/project/${projectId}/process-all`, {
      method: 'POST',
    });

    return {
      projectId: response.data.project_id,
      started: response.data.started,
      totalStarted: response.data.total_started,
      totalPending: response.data.total_pending,
    };
  },
};

// ============================================================================
// SYSTEM API
// ============================================================================

export const systemApi = {
  /**
   * Get hardware information for processing configuration
   */
  async getHardware(): Promise<HardwareInfo> {
    return apiFetch<HardwareInfo>('/system/hardware');
  },

  /**
   * Get current compute mode
   */
  async getComputeMode(): Promise<ComputeModeResponse> {
    return apiFetch<ComputeModeResponse>('/system/compute-mode');
  },

  /**
   * Change compute mode (GPU/CPU)
   */
  async setComputeMode(mode: ComputeMode): Promise<ComputeModeResponse> {
    return apiFetch<ComputeModeResponse>('/system/compute-mode', {
      method: 'POST',
      body: JSON.stringify({ mode }),
    });
  },
};

// ============================================================================
// DOWNLOAD HELPER
// ============================================================================

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
