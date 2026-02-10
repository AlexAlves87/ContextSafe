/**
 * WorkspaceScreen - Project overview and document management
 *
 * Traceability:
 * - Contract: CNT-UI-SCREEN-001
 * - Route: /projects/:projectId
 *
 * ASCII Layout Reference (from project_context.yaml):
 * ┌─────────────────────────────────────────────────┐
 * │  [ContextSafe]                           [👤]   │
 * ├─────────────────────────────────────────────────┤
 * │  📁 Proyecto: "Caso_Legal_001"                  │
 * │  📊 3 docs · 15 entidades · 80% anonimizado     │
 * │                                                 │
 * │  ┌────────────┐  ┌────────────┐                │
 * │  │  DRAG &    │  │  Glosario  │                │
 * │  │   DROP     │  │ ────────── │                │
 * │  │   ZONA     │  │ • Juan → Persona_1         │
 * │  │            │  │ • Clínica → Org_A          │
 * │  │ [Subir docs]│  │ • 12345678A → ID_001      │
 * │  └────────────┘  └────────────┘                │
 * │                                                 │
 * │  📄 Documentos del Proyecto:                    │
 * │  • demanda.pdf [✅ Anonimizado] [⬇️] [👁️]      │
 * │  • testimonio.docx [🔄 Procesando... 65%]      │
 * │  • informe.pdf [📤 Listo para subir]           │
 * └─────────────────────────────────────────────────┘
 */

import React, { useEffect, useCallback, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FileUpload,
  DocumentList,
  LoadingSpinner,
  GlossaryTable,
  ProcessingModal,
} from '@/components';
import { useProjectStore, useDocumentStore, useUIStore } from '@/stores';
import { projectApi } from '@/services/api';

export const WorkspaceScreen: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const { selectedProject, selectProject, isLoading: projectLoading } =
    useProjectStore();
  const {
    documents,
    glossary,
    fetchDocuments,
    fetchGlossary,
    uploadDocument,
    isLoading: documentsLoading,
    isUploading,
  } = useDocumentStore();
  const { addToast } = useUIStore();

  // Estado para el archivo seleccionado (antes de confirmar subida)
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Estado para el modal de procesamiento (REFORMA.md)
  const [showProcessingModal, setShowProcessingModal] = useState(false);

  // Load project data
  useEffect(() => {
    if (projectId) {
      selectProject(projectId);
      fetchDocuments(projectId);
      fetchGlossary(projectId);
    }
  }, [projectId, selectProject, fetchDocuments, fetchGlossary]);

  // Handle file selection (muestra preview antes de subir)
  const handleFileSelect = useCallback((file: File) => {
    setSelectedFile(file);
  }, []);

  // Confirmar subida del archivo seleccionado
  const handleConfirmUpload = useCallback(async () => {
    if (!projectId || !selectedFile) return;

    try {
      await uploadDocument(projectId, selectedFile);
      addToast({
        type: 'success',
        message: `Documento "${selectedFile.name}" subido correctamente. Listo para procesar.`,
      });
      setSelectedFile(null); // Limpiar selección
      fetchDocuments(projectId);
    } catch (error) {
      addToast({
        type: 'error',
        message: `Error al subir "${selectedFile.name}"`,
      });
    }
  }, [projectId, selectedFile, uploadDocument, addToast, fetchDocuments]);

  // Descartar archivo seleccionado
  const handleDiscardFile = useCallback(() => {
    setSelectedFile(null);
    addToast({
      type: 'info',
      message: 'Documento descartado',
    });
  }, [addToast]);

  // Handle document selection - navigate to preview (spec route)
  const handleDocumentSelect = useCallback(
    (docId: string) => {
      const doc = documents.find((d) => d.id === docId);
      if (!doc || !projectId) return;

      // All documents go to preview route: /projects/:projectId/documents/:documentId
      navigate(`/projects/${projectId}/documents/${docId}`);
    },
    [documents, projectId, navigate]
  );

  // Handle process all documents - open modal (REFORMA.md: no navigation)
  const handleProcessAll = useCallback(() => {
    if (!projectId) return;
    setShowProcessingModal(true);
  }, [projectId]);

  // Handle processing complete - refresh data
  const handleProcessingComplete = useCallback(() => {
    if (!projectId) return;
    fetchDocuments(projectId);
    fetchGlossary(projectId);
  }, [projectId, fetchDocuments, fetchGlossary]);

  // Handle document download
  const handleDocumentDownload = useCallback(
    async (docId: string) => {
      const doc = documents.find((d) => d.id === docId);
      if (!doc) return;

      try {
        // Import dynamically to avoid circular deps
        const { documentApi, downloadBlob } = await import('@/services/api');
        const blob = await documentApi.export(docId, 'pdf');
        const filename = doc.filename.replace(/\.[^.]+$/, '_anonimizado.pdf');
        downloadBlob(blob, filename);
        addToast({
          type: 'success',
          message: `Documento "${filename}" descargado`,
        });
      } catch (error) {
        addToast({
          type: 'error',
          message: 'Error al descargar el documento',
        });
      }
    },
    [documents, addToast]
  );

  // Handle document view - navigate to preview
  const handleDocumentView = useCallback(
    (docId: string) => {
      if (!projectId) return;
      navigate(`/projects/${projectId}/documents/${docId}`);
    },
    [projectId, navigate]
  );

  // Handle glossary changes (edit + delete)
  const handleGlossarySaveChanges = async (
    changes: Array<{
      originalTerm: string;
      category: string;
      newAlias: string;
    }>,
    deletions?: string[]
  ) => {
    if (!projectId) return;

    try {
      const result = await projectApi.updateGlossary(projectId, changes, undefined, deletions);

      if (result.changesFailed > 0) {
        addToast({
          type: 'warning',
          message: `${result.changesFailed} cambio(s) no se pudieron aplicar`,
        });
      } else {
        addToast({
          type: 'success',
          message: 'Glosario actualizado correctamente',
        });
      }

      // Reload glossary to show updated data
      await fetchGlossary(projectId);
    } catch (error) {
      addToast({
        type: 'error',
        message: 'Error al actualizar el glosario',
      });
    }
  };

  if (projectLoading || !selectedProject) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" label="Cargando proyecto..." />
      </div>
    );
  }

  return (
    <div className="industrial flex flex-col h-full">
      {/* Status Bar - Compact Industrial Header */}
      <div className="status-bar-industrial">
        <div className="flex items-center">
          <span className="status-item">
            <span className="text-primary">📂</span>
            <span>PROYECTO:</span>
            <span className="text-foreground font-semibold">{selectedProject.name}</span>
          </span>
          <span className="status-separator">│</span>
          <span className="status-item">
            <span>DOCS:</span>
            <span className="text-foreground">{selectedProject.documentCount}</span>
          </span>
          <span className="status-separator">│</span>
          <span className="status-item">
            <span>ENTIDADES:</span>
            <span className="text-foreground">{selectedProject.entityCount}</span>
          </span>
          <span className="status-separator">│</span>
          <span className="status-item">
            <span className="text-success">{selectedProject.completionPercentage}%</span>
          </span>
        </div>
      </div>

      {/* Main Content Grid - Industrial Docking Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 min-h-[200px]">
        {/* Upload Zone - Left Panel */}
        <div className="panel-industrial border-r-0 lg:border-r flex flex-col">
          <div className="panel-industrial-header">
            ZONA DE INGESTA
          </div>
          <div className="flex-1 p-3">
            {/* Si hay archivo seleccionado, mostrar preview con opciones */}
            {selectedFile ? (
              <div className="border border-dashed border-primary/50 p-4 bg-primary/5">
                {/* Header con icono y nombre */}
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 bg-primary/20">
                    <svg className="w-6 h-6 text-primary" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-industrial text-foreground truncate">
                      {selectedFile.name}
                    </p>
                    <p className="text-[10px] uppercase text-muted-foreground">
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                  </div>
                </div>

                {/* Botones de acción */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleConfirmUpload}
                    disabled={isUploading}
                    className="btn-industrial flex-1 flex items-center justify-center gap-2"
                  >
                    {isUploading ? (
                      <>
                        <LoadingSpinner size="sm" />
                        SUBIENDO...
                      </>
                    ) : (
                      <>
                        <span>↑</span>
                        SUBIR
                      </>
                    )}
                  </button>
                  <button
                    onClick={handleDiscardFile}
                    disabled={isUploading}
                    className="px-3 py-2 text-xs font-semibold uppercase tracking-wider border border-border text-muted-foreground hover:bg-muted/50 disabled:opacity-50"
                  >
                    ✕
                  </button>
                </div>
              </div>
            ) : (
              <>
                <FileUpload
                  onFileSelect={handleFileSelect}
                  acceptedTypes={['pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg']}
                  maxSizeMb={50}
                  disabled={isUploading}
                  variant="industrial"
                />
                {isUploading && (
                  <div className="mt-3">
                    <LoadingSpinner size="sm" label="SUBIENDO DOCUMENTO..." />
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {/* Document List - Right Panel */}
        <div className="panel-industrial flex flex-col">
          <div className="panel-industrial-header flex items-center justify-between">
            <span>DOCUMENTOS</span>
            {documents.length > 0 && (
              <button
                onClick={handleProcessAll}
                className="btn-industrial py-1 px-3"
              >
                PROCESAR LOTE →
              </button>
            )}
          </div>
          <div className="flex-1 overflow-auto max-h-[250px]">
            <DocumentList
              documents={documents}
              onSelect={handleDocumentSelect}
              onDownload={handleDocumentDownload}
              onView={handleDocumentView}
              isLoading={documentsLoading}
              variant="industrial"
            />
          </div>
        </div>
      </div>

      {/* Glosario - Bottom Panel (full width) */}
      <div className="panel-industrial flex flex-col border-t-0 flex-1 min-h-[150px] max-h-[300px]">
        <div className="panel-industrial-header">
          GLOSARIO {glossary.length > 0 && <span className="ml-2 text-foreground">({glossary.length})</span>}
        </div>
        <div className="flex-1 overflow-auto">
          {glossary.length > 0 ? (
            <GlossaryTable
              entries={glossary}
              onSaveChanges={handleGlossarySaveChanges}
              editable={true}
              anonymizationLevel={selectedProject?.anonymizationLevel || 'intermediate'}
              variant="industrial"
              className="h-full"
            />
          ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground text-xs uppercase tracking-wider py-8">
              SIN ENTIDADES
            </div>
          )}
        </div>
      </div>

      {/* Processing Modal (REFORMA.md) */}
      <ProcessingModal
        isOpen={showProcessingModal}
        onClose={() => setShowProcessingModal(false)}
        projectId={projectId || ''}
        projectName={selectedProject?.name || ''}
        documents={documents.filter(d => d.state === 'pending')}
        onComplete={handleProcessingComplete}
      />
    </div>
  );
};

export default WorkspaceScreen;
