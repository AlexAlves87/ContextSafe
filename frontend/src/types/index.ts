/**
 * ContextSafe Frontend Type Definitions
 *
 * Traceability:
 * - Source: Domain layer value objects and entities
 * - Contracts: CNT-UI-COMP-*, CNT-UI-BIND-*
 */

// ============================================================================
// PII CATEGORIES (from controlled_vocabulary.yaml)
// ============================================================================
export type PiiCategory =
  | 'person_name'
  | 'organization'
  | 'address'
  | 'postal_code'
  | 'dni'
  | 'nie'
  | 'cif'
  | 'nss'
  | 'dni_nie'
  | 'passport'
  | 'phone'
  | 'email'
  | 'iban'
  | 'bank_account'
  | 'credit_card'
  | 'date'
  | 'date_of_birth'
  | 'location'
  | 'medical_record'
  | 'license_plate'
  | 'social_security'
  | 'ip_address'
  | 'url';

export const PII_CATEGORY_LABELS: Record<PiiCategory, string> = {
  person_name: 'Nombre',
  organization: 'Organización',
  address: 'Dirección',
  postal_code: 'Código Postal',
  dni: 'DNI',
  nie: 'NIE',
  cif: 'CIF',
  nss: 'NSS',
  dni_nie: 'DNI/NIE',
  passport: 'Pasaporte',
  phone: 'Teléfono',
  email: 'Email',
  iban: 'IBAN',
  bank_account: 'Cuenta Bancaria',
  credit_card: 'Tarjeta de Crédito',
  date: 'Fecha',
  date_of_birth: 'Fecha',  // Legacy - now uses 'date'
  location: 'Ubicación',
  medical_record: 'Historia Clínica',
  license_plate: 'Matrícula',
  social_security: 'Seguridad Social',
  ip_address: 'Dirección IP',
  url: 'URL',
};

// ============================================================================
// ANONYMIZATION LEVELS
// ============================================================================
export type AnonymizationLevel = 'basic' | 'intermediate' | 'advanced';

export const ANONYMIZATION_LEVEL_LABELS: Record<AnonymizationLevel, string> = {
  basic: 'Básico - Solo datos críticos',
  intermediate: 'Intermedio - Todo PII (Recomendado)',
  advanced: 'Avanzado - Máxima privacidad',
};

// ============================================================================
// CONFIDENCE ZONES (from confidence_zone.py)
// ============================================================================
export type ConfidenceZone = 'GREEN' | 'AMBER' | 'RED';

export type ReviewAction = 'APPROVED' | 'REJECTED' | 'CORRECTED';

// ============================================================================
// DOCUMENT TYPES (from document_classifier.py)
// ============================================================================
export type LegalDocumentType =
  | 'SENTENCIA'
  | 'ESCRITURA'
  | 'FACTURA'
  | 'RECURSO'
  | 'DENUNCIA'
  | 'CONTRATO'
  | 'GENERIC';

// ============================================================================
// REVIEW SUMMARY
// ============================================================================
export interface ReviewSummary {
  total: number;
  reviewed: number;
  pending: number;
  pendingAmberRed: number;
  byZone: { GREEN: number; AMBER: number; RED: number };
  reviewPercentage: number;
  canExport: boolean;
  exportBlockedReason: string;
}

// ============================================================================
// VALIDATION TYPES
// ============================================================================
export type ValidationSeverity = 'CRITICAL' | 'WARNING';

export interface ValidationResult {
  passed: boolean;
  severity: ValidationSeverity;
  ruleId: string;
  message: string;
}

export interface ExportValidation {
  canExport: boolean;
  pendingReviews: number;
  totalEntities: number;
  reviewedEntities: number;
  reviewPercentage: number;
  validationResults: ValidationResult[];
  warnings: ValidationResult[];
}

// ============================================================================
// DOCUMENT STATES
// ============================================================================
export type DocumentState =
  | 'pending'
  | 'ingesting'
  | 'detecting'
  | 'anonymizing'
  | 'completed'
  | 'failed';

export const DOCUMENT_STATE_LABELS: Record<DocumentState, string> = {
  pending: 'Pendiente',
  ingesting: 'Extrayendo texto',
  detecting: 'Detectando PII',
  anonymizing: 'Anonimizando',
  completed: 'Completado',
  failed: 'Error',
};

// ============================================================================
// DOMAIN ENTITIES (TypeScript versions)
// ============================================================================

/**
 * Project entity
 */
export interface Project {
  id: string;
  name: string;
  description?: string;
  anonymizationLevel: AnonymizationLevel;
  createdAt: string;
  updatedAt: string;
  documentCount: number;
  entityCount: number;
  completionPercentage: number;
}

/**
 * Document entity
 */
export interface Document {
  id: string;
  projectId: string;
  filename: string;
  originalFilename: string;
  format: 'pdf' | 'docx' | 'txt' | 'png' | 'jpg' | 'jpeg';
  state: DocumentState;
  pageCount: number;
  entityCount: number;
  createdAt: string;
  updatedAt: string;
  textContent?: string;
  anonymizedContent?: string;
  documentType?: LegalDocumentType;
  documentTypeConfidence?: number;
  reviewSummary?: ReviewSummary;
}

/**
 * Document list item (for DocumentList component)
 */
export interface DocumentListItem {
  id: string;
  filename: string;
  format: Document['format'];
  state: DocumentState;
  progress?: number;
  entityCount: number;
  createdAt: string;
}

/**
 * Detected entity
 */
export interface DetectedEntity {
  id: string;
  documentId: string;
  category: PiiCategory;
  originalText: string;
  startOffset: number;
  endOffset: number;
  confidence: number;
  alias?: string;
  zone: ConfidenceZone;
  zoneReason: string;
  reviewed: boolean;
  reviewAction: ReviewAction | null;
}

/**
 * Glossary entry (alias mapping)
 */
export interface GlossaryEntry {
  id: string;
  projectId: string;
  originalText: string;
  alias: string;
  category: PiiCategory;
  occurrenceCount: number;
}

/**
 * Project settings
 */
export interface ProjectSettings {
  anonymizationLevel: AnonymizationLevel;
  enabledCategories: PiiCategory[];
  preserveFormatting: boolean;
  maintainConsistency: boolean;
  generateAuditReport: boolean;
}

// ============================================================================
// PROCESSING TYPES
// ============================================================================

export type ProcessingStage = 'ingesting' | 'detecting' | 'anonymizing';

export interface ProcessingProgress {
  documentId: string;
  stage: ProcessingStage;
  progress: number;
  currentEntity?: string;
  error?: string;
}

// ============================================================================
// COMPUTE MODE & HARDWARE TYPES
// ============================================================================

export type ComputeMode = 'gpu' | 'cpu';

export interface HardwareInfo {
  gpu: {
    available: boolean;
    name: string | null;
    vram_gb: number;
    vram_free_gb: number;
    driver: string | null;
  };
  cpu: {
    name: string;
    cores: number;
    threads: number;
  };
  ram: {
    total_gb: number;
    available_gb: number;
    percent_used: number;
  };
  current_mode: ComputeMode;
  recommended_mode: ComputeMode;
}

export interface ComputeModeResponse {
  mode: ComputeMode;
  gpu_available: boolean;
  effective: ComputeMode;
}

// ============================================================================
// EXPORT TYPES
// ============================================================================

export type ExportFormat = 'pdf' | 'docx' | 'txt';

export interface ExportRequest {
  documentId: string;
  format: ExportFormat;
  includeAuditReport: boolean;
}

// ============================================================================
// API RESPONSE TYPES
// ============================================================================

export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  hasMore: boolean;
}
