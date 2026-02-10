/**
 * PreviewScreen - Anonymized document preview and export
 *
 * Traceability:
 * - Contract: CNT-UI-SCREEN-003
 * - Route: /projects/:projectId/documents/:documentId
 *
 * ASCII Layout Reference (from project_context.yaml):
 * ┌─────────────────────────────────────────────────┐
 * │  Vista Previa - demanda.pdf                     │
 * ├─────────────────────────────────────────────────┤
 * │  COMPARACIÓN:                                   │
 * │  ┌───────────────┬───────────────┐             │
 * │  │  ORIGINAL     │  ANONIMIZADO  │             │
 * │  │               │               │             │
 * │  │ El paciente   │ El paciente   │             │
 * │  │ Juan Pérez    │ Persona_1     │             │
 * │  │ (DNI 12345678A│ (DNI ID_001   │             │
 * │  │ fue atendido  │ fue atendido  │             │
 * │  │ en la Clínica │ en la Org_A   │             │
 * │  │ Barcelona...  │ Ciudad_1...   │             │
 * │  │               │               │             │
 * │  └───────────────┴───────────────┘             │
 * │                                                 │
 * │  [⬇️ Descargar PDF] [⬇️ Descargar DOCX]        │
 * │  [📋 Copiar texto]  [🔄 Reprocesar]             │
 * │                                                 │
 * │  📋 Glosario aplicado:                          │
 * │  • Persona_1 = Juan Pérez (aparece 3 veces)     │
 * │  • ID_001 = 12345678A                           │
 * │  • Org_A = Clínica Barcelona                    │
 * └─────────────────────────────────────────────────┘
 */

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  AnonymizedPreview,
  GlossaryTable,
  ExportDialog,
  LoadingSpinner,
  EntityEditorModal,
  ReviewProgressBar,
  EntityZoneGroup,
  SafetyLatchIndicator,
  DocumentTypeBadge,
} from '@/components';
import { useDocumentStore, useProjectStore, useUIStore } from '@/stores';
import { useIsMobile } from '@/hooks';
import { documentApi, projectApi, downloadBlob } from '@/services/api';
import type { ExportFormat, GlossaryEntry, ReviewAction, ConfidenceZone } from '@/types';

export const PreviewScreen: React.FC = () => {
  const { projectId, documentId } = useParams<{
    projectId: string;
    documentId: string;
  }>();
  const navigate = useNavigate();

  const {
    selectedDocument,
    anonymizedContent,
    entities,
    glossary,
    reviewSummary,
    isReviewing,
    selectDocument,
    fetchAnonymized,
    fetchEntities,
    fetchGlossary,
    reviewEntity,
    batchReviewGreen,
    isLoading,
    isLoadingAnonymized,
  } = useDocumentStore();
  const { selectedProject, selectProject } = useProjectStore();
  const { addToast } = useUIStore();

  // Get anonymization level from project
  const anonymizationLevel = selectedProject?.anonymizationLevel || 'intermediate';

  const isMobile = useIsMobile();
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [highlightedTerm, setHighlightedTerm] = useState<string | null>(null);

  // Mobile: Entity editor modal state
  const [editingEntry, setEditingEntry] = useState<GlossaryEntry | null>(null);

  // Load document and project data
  useEffect(() => {
    if (documentId) {
      selectDocument(documentId);
      fetchAnonymized(documentId);
      fetchEntities(documentId);
    }
    if (projectId) {
      fetchGlossary(projectId);
      selectProject(projectId);
    }
  }, [documentId, projectId, selectDocument, fetchAnonymized, fetchEntities, fetchGlossary, selectProject]);

  // Handle export
  const handleExport = useCallback(
    async (format: ExportFormat) => {
      if (!documentId || !selectedDocument) return;

      setIsExporting(true);
      try {
        const blob = await documentApi.export(documentId, format);
        const filename = selectedDocument.filename.replace(
          /\.[^.]+$/,
          `_anonimizado.${format}`
        );
        downloadBlob(blob, filename);
        addToast({
          type: 'success',
          message: `Documento exportado como ${format.toUpperCase()}`,
        });
        setExportDialogOpen(false);
      } catch (error) {
        addToast({
          type: 'error',
          message: 'Error al exportar el documento',
        });
      } finally {
        setIsExporting(false);
      }
    },
    [documentId, selectedDocument, addToast]
  );

  // Copy to clipboard
  const handleCopyText = useCallback(async () => {
    if (!anonymizedContent?.anonymized) return;

    try {
      await navigator.clipboard.writeText(anonymizedContent.anonymized);
      addToast({
        type: 'success',
        message: 'Texto copiado al portapapeles',
      });
    } catch (error) {
      addToast({
        type: 'error',
        message: 'Error al copiar el texto',
      });
    }
  }, [anonymizedContent, addToast]);

  // Reprocess document - navigates to project-level processing
  const handleReprocess = useCallback(() => {
    if (projectId) {
      navigate(`/projects/${projectId}/process`);
    }
  }, [projectId, navigate]);

  // Handle glossary alias changes - save and regenerate document
  const handleSaveGlossaryChanges = useCallback(
    async (
      changes: Array<{
        originalTerm: string;
        category: string;
        newAlias: string;
      }>,
      deletions?: string[]
    ) => {
      if (!projectId || !documentId) return;

      try {
        // Save changes to glossary (this also regenerates all project documents)
        const result = await projectApi.updateGlossary(projectId, changes, documentId, deletions);

        if (result.changesFailed > 0) {
          throw new Error(`${result.changesFailed} cambio(s) fallaron`);
        }

        const deletedCount = deletions?.length || 0;
        let message = '';
        if (result.changesApplied > 0) message += `${result.changesApplied} alias actualizado(s). `;
        if (deletedCount > 0) message += `${deletedCount} entrada(s) eliminada(s). `;
        if (result.mergedCount > 0) message += `${result.mergedCount} entrada(s) fusionada(s). `;
        message += 'Documento regenerado.';

        addToast({
          type: 'success',
          message: message,
        });

        // Reload the anonymized content to show updated text
        await fetchAnonymized(documentId);
        // Also reload glossary to reflect changes
        await fetchGlossary(projectId);
      } catch (error) {
        addToast({
          type: 'error',
          message: error instanceof Error ? error.message : 'Error al guardar cambios',
        });
        throw error; // Re-throw to show error in GlossaryTable
      }
    },
    [projectId, documentId, addToast, fetchAnonymized, fetchGlossary]
  );

  // Handle original text corrections (fix detection boundaries)
  const handleSaveOriginalTextChanges = useCallback(
    async (
      changes: Array<{
        entryId: string;
        oldOriginalText: string;
        newOriginalText: string;
        category: string;
        alias: string;
      }>
    ) => {
      if (!projectId || !documentId) return;

      try {
        // Call API to update the original text in glossary entries
        const result = await projectApi.correctGlossaryEntries(projectId, changes, documentId);

        if (result.changesFailed > 0) {
          throw new Error(`${result.changesFailed} corrección(es) fallaron`);
        }

        addToast({
          type: 'success',
          message: `${result.changesApplied} texto(s) corregido(s). Documento regenerado.`,
        });

        // Reload the anonymized content to show updated text
        await fetchAnonymized(documentId);
        // Also reload glossary to reflect changes
        await fetchGlossary(projectId);
      } catch (error) {
        addToast({
          type: 'error',
          message: error instanceof Error ? error.message : 'Error al guardar correcciones',
        });
        throw error;
      }
    },
    [projectId, documentId, addToast, fetchAnonymized, fetchGlossary]
  );

  // Handle find in text - scroll to the term in the preview
  const handleFindInText = useCallback(
    (entry: { originalText: string; alias: string }) => {
      setHighlightedTerm(entry.originalText);
      // Scroll to the comparison section
      const comparisonSection = document.getElementById('comparison-section');
      if (comparisonSection) {
        comparisonSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    },
    []
  );

  // Clear the highlighted term
  const handleClearHighlight = useCallback(() => {
    setHighlightedTerm(null);
  }, []);

  // Handle manual anonymization of selected text
  const handleManualAnonymize = useCallback(
    async (text: string, category: string, alias?: string) => {
      if (!documentId || !projectId) return;

      try {
        const result = await documentApi.anonymizeSelection(
          documentId,
          text,
          category,
          alias
        );

        if (result.success) {
          addToast({
            type: 'success',
            message: `"${text}" anonimizado como "${result.alias}"`,
          });

          // Reload the anonymized content to show updated text
          await fetchAnonymized(documentId);
          // Also reload glossary to reflect new entry
          await fetchGlossary(projectId);
        } else {
          throw new Error(result.message || 'Error al anonimizar');
        }
      } catch (error) {
        addToast({
          type: 'error',
          message: error instanceof Error ? error.message : 'Error al anonimizar texto',
        });
        throw error;
      }
    },
    [documentId, projectId, addToast, fetchAnonymized, fetchGlossary]
  );

  // Mobile: Handle entity edit modal save
  const handleEntityModalSave = useCallback(
    async (changes: {
      entryId: string;
      alias?: string;
      category?: string;
      originalText?: string;
    }) => {
      if (!projectId || !documentId) return;

      try {
        const entry = glossary.find(e => e.id === changes.entryId);
        if (!entry) return;

        // Handle alias/category changes
        if (changes.alias || changes.category) {
          await projectApi.updateGlossary(projectId, [{
            originalTerm: entry.originalText,
            category: entry.category,
            newAlias: changes.alias || entry.alias,
            newCategory: changes.category,
          }], documentId);
        }

        // Handle original text changes (boundary correction)
        if (changes.originalText) {
          await projectApi.correctGlossaryEntries(projectId, [{
            entryId: entry.id,
            oldOriginalText: entry.originalText,
            newOriginalText: changes.originalText,
            category: changes.category || entry.category,
            alias: changes.alias || entry.alias,
          }], documentId);
        }

        addToast({
          type: 'success',
          message: 'Cambios guardados correctamente',
        });

        // Reload data
        await fetchAnonymized(documentId);
        await fetchGlossary(projectId);
      } catch (error) {
        addToast({
          type: 'error',
          message: error instanceof Error ? error.message : 'Error al guardar cambios',
        });
        throw error;
      }
    },
    [projectId, documentId, glossary, addToast, fetchAnonymized, fetchGlossary]
  );

  // Review panel state
  const [reviewPanelOpen, setReviewPanelOpen] = useState(false);

  // Group entities by zone (memoized)
  const entitiesByZone = useMemo(() => {
    const groups: Record<ConfidenceZone, typeof entities> = {
      RED: [],
      AMBER: [],
      GREEN: [],
    };
    for (const entity of entities) {
      groups[entity.zone]?.push(entity);
    }
    return groups;
  }, [entities]);

  // Handle entity review (with optional category correction)
  const handleReviewEntity = useCallback(
    (entityId: string, action: ReviewAction, newCategory?: string) => {
      if (!documentId) return;
      if (newCategory) {
        reviewEntity(documentId, entityId, action, { newCategory });
      } else {
        reviewEntity(documentId, entityId, action);
      }
    },
    [documentId, reviewEntity]
  );

  // Handle batch approve GREEN
  const handleBatchApproveGreen = useCallback(() => {
    if (!documentId) return;
    batchReviewGreen(documentId);
  }, [documentId, batchReviewGreen]);

  // Mobile: Handle entity delete from modal
  const handleEntityModalDelete = useCallback(
    async (entryId: string) => {
      if (!projectId || !documentId) return;

      try {
        await projectApi.updateGlossary(projectId, [], documentId, [entryId]);
        addToast({
          type: 'success',
          message: 'Anonimización eliminada',
        });
        await fetchAnonymized(documentId);
        await fetchGlossary(projectId);
      } catch (error) {
        addToast({
          type: 'error',
          message: 'Error al eliminar',
        });
      }
    },
    [projectId, documentId, addToast, fetchAnonymized, fetchGlossary]
  );

  if (isLoading || !selectedDocument) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" label="Cargando documento..." />
      </div>
    );
  }

  return (
    <div className="industrial w-full h-full flex flex-col">
      {/* DEBUG: Indicador de versión actualizada */}
      <div className="bg-red-600 text-white text-center py-1 text-xs font-bold">
        DEBUG v2: reviewPanelOpen = {String(reviewPanelOpen)} | entities = {entities.length}
      </div>
      {/* Compact Industrial Header - responsive */}
      <div className="status-bar-industrial flex-shrink-0">
        <div className="flex items-center gap-2 md:gap-4 min-w-0">
          <button
            onClick={() => navigate(`/projects/${projectId}`)}
            className="p-1 hover:bg-muted/50 text-muted-foreground hover:text-foreground flex-shrink-0"
            title="Volver al proyecto"
          >
            ←
          </button>
          <span className="text-foreground font-semibold truncate">{selectedDocument.filename}</span>
          {selectedDocument.documentType && (
            <DocumentTypeBadge
              documentType={selectedDocument.documentType}
              confidence={selectedDocument.documentTypeConfidence}
            />
          )}
          <span className="status-separator hidden md:inline">|</span>
          <span className="text-success hidden md:inline">{selectedDocument.entityCount} ENTIDADES</span>
          <span className="status-separator hidden md:inline">|</span>
          {reviewSummary && (
            <SafetyLatchIndicator
              canExport={reviewSummary.canExport}
              blockedReason={reviewSummary.exportBlockedReason}
              compact
            />
          )}
        </div>
        <div className="flex items-center gap-1 md:gap-2 flex-shrink-0">
          <button
            onClick={() => setReviewPanelOpen(!reviewPanelOpen)}
            className={`px-2 md:px-3 py-1 text-[10px] font-semibold uppercase tracking-wider border border-border hover:bg-muted/50 ${reviewPanelOpen ? 'bg-muted text-foreground' : 'text-muted-foreground'}`}
          >
            REVISAR {reviewSummary && reviewSummary.pendingAmberRed > 0 ? `(${reviewSummary.pendingAmberRed})` : ''}
          </button>
          <button
            onClick={handleCopyText}
            className="px-2 md:px-3 py-1 text-[10px] font-semibold uppercase tracking-wider border border-border text-muted-foreground hover:bg-muted/50 hidden sm:block"
          >
            COPIAR
          </button>
          <button
            onClick={handleReprocess}
            className="px-2 md:px-3 py-1 text-[10px] font-semibold uppercase tracking-wider border border-border text-muted-foreground hover:bg-muted/50 hidden md:block"
          >
            REPROCESAR
          </button>
          <button
            onClick={() => setExportDialogOpen(true)}
            disabled={reviewSummary ? !reviewSummary.canExport : false}
            className={`btn-industrial py-1 px-2 md:px-3 ${reviewSummary && !reviewSummary.canExport ? 'opacity-50 cursor-not-allowed' : ''}`}
            title={reviewSummary && !reviewSummary.canExport ? reviewSummary.exportBlockedReason : 'Exportar'}
          >
            <span className="hidden sm:inline">DESCARGAR</span> ↓
          </button>
        </div>
      </div>

      {/* Review Panel (collapsible) */}
      {reviewPanelOpen && (
        <div className="flex-shrink-0 border-b border-border px-2 md:px-4 py-3 space-y-3 max-h-[50vh] overflow-y-auto bg-muted/30">
          {entities.length === 0 ? (
            <div className="text-center text-muted-foreground text-sm py-4">
              No hay entidades detectadas en este documento
            </div>
          ) : (
            <>
              {/* Progress bar */}
              {reviewSummary && <ReviewProgressBar summary={reviewSummary} />}

              {/* Safety latch indicator */}
              {reviewSummary && (
                <SafetyLatchIndicator
                  canExport={reviewSummary.canExport}
                  blockedReason={reviewSummary.exportBlockedReason}
                />
              )}

              {/* Entity groups by zone: RED first, then AMBER, then GREEN */}
              <EntityZoneGroup
                zone="RED"
                entities={entitiesByZone.RED}
                onReviewEntity={handleReviewEntity}
                isReviewing={isReviewing}
              />
              <EntityZoneGroup
                zone="AMBER"
                entities={entitiesByZone.AMBER}
                onReviewEntity={handleReviewEntity}
                isReviewing={isReviewing}
              />
              <EntityZoneGroup
                zone="GREEN"
                entities={entitiesByZone.GREEN}
                onReviewEntity={handleReviewEntity}
                onBatchApprove={handleBatchApproveGreen}
                isReviewing={isReviewing}
              />
            </>
          )}
        </div>
      )}

      {/* Full-Width Comparison View - Takes remaining height */}
      <div id="comparison-section" className="flex-1 min-h-0 px-2 md:px-4 py-2">
        {isLoadingAnonymized ? (
          <div className="flex items-center justify-center h-full">
            <LoadingSpinner size="md" label="CARGANDO..." />
          </div>
        ) : anonymizedContent ? (
          <AnonymizedPreview
            originalText={anonymizedContent.original}
            anonymizedText={anonymizedContent.anonymized}
            glossary={glossary}
            viewMode="split"
            onManualAnonymize={handleManualAnonymize}
            highlightedTerm={highlightedTerm}
            onClearHighlight={handleClearHighlight}
            anonymizationLevel={anonymizationLevel}
          />
        ) : (
          <div className="flex items-center justify-center h-full text-muted-foreground text-xs uppercase">
            CONTENIDO NO DISPONIBLE
          </div>
        )}
      </div>

      {/* Glossary Section - Integrated in page flow */}
      <div className="border-t border-border flex-shrink-0 px-2 md:px-4 py-2 md:py-3">
        <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
          GLOSARIO ({glossary.length})
          {anonymizationLevel === 'basic' && <span className="ml-2">MODO AUDITORÍA</span>}
        </div>
        {glossary.length > 0 ? (
          <GlossaryTable
            entries={glossary}
            originalDocumentText={anonymizedContent?.original}
            editable={true}
            anonymizationLevel={anonymizationLevel}
            onSaveChanges={handleSaveGlossaryChanges}
            onSaveOriginalTextChanges={handleSaveOriginalTextChanges}
            onFindInText={isMobile ? undefined : handleFindInText}
            onSelectEntry={isMobile ? setEditingEntry : undefined}
            variant="industrial"
          />
        ) : (
          <div className="text-muted-foreground text-xs uppercase">
            SIN ENTRADAS
          </div>
        )}
      </div>

      {/* Export Dialog */}
      <ExportDialog
        isOpen={exportDialogOpen}
        onClose={() => setExportDialogOpen(false)}
        onExport={handleExport}
        isExporting={isExporting}
        documentName={selectedDocument.filename}
        canExport={reviewSummary?.canExport ?? true}
        exportBlockedReason={reviewSummary?.exportBlockedReason}
      />

      {/* Mobile: Entity Editor Modal */}
      <EntityEditorModal
        entry={editingEntry}
        isOpen={!!editingEntry}
        onClose={() => setEditingEntry(null)}
        onSave={handleEntityModalSave}
        onDelete={handleEntityModalDelete}
        originalDocumentText={anonymizedContent?.original}
        anonymizationLevel={anonymizationLevel}
      />
    </div>
  );
};

export default PreviewScreen;
