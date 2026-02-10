/**
 * GlossaryScreen - View and search glossary across projects
 */

import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import { useProjectStore } from '@/stores';
import { projectApi, downloadBlob } from '@/services/api';

import { LoadingSpinner, GlossaryTable, CategoryChip } from '@/components';
import type { GlossaryEntry } from '@/types';

export const GlossaryScreen: React.FC = () => {
  const navigate = useNavigate();
  const { projects, fetchProjects, isLoading: projectsLoading } = useProjectStore();
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [glossary, setGlossary] = useState<GlossaryEntry[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  useEffect(() => {
    if (selectedProjectId) {
      loadGlossary(selectedProjectId);
    }
  }, [selectedProjectId]);

  // Auto-select first project if none selected
  useEffect(() => {
    if (!selectedProjectId && projects.length > 0) {
      setSelectedProjectId(projects[0].id);
    }
  }, [projects, selectedProjectId]);

  const loadGlossary = async (projectId: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const entries = await projectApi.getGlossary(projectId);
      setGlossary(entries);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error al cargar el glosario');
      setGlossary([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = async (format: 'csv' | 'json') => {
    if (!selectedProjectId) return;
    try {
      const blob = await projectApi.exportGlossary(selectedProjectId, format);
      const project = projects.find(p => p.id === selectedProjectId);
      const filename = `glosario_${project?.name || 'proyecto'}.${format}`;
      downloadBlob(blob, filename);
    } catch (e) {
      console.error('Export failed:', e);
    }
  };

  const handleSaveChanges = async (
    changes: Array<{
      originalTerm: string;
      category: string;
      newAlias: string;
    }>,
    deletions?: string[]
  ) => {
    if (!selectedProjectId) return;

    const result = await projectApi.updateGlossary(selectedProjectId, changes, undefined, deletions);

    if (result.changesFailed > 0) {
      throw new Error(`${result.changesFailed} cambio(s) fallaron`);
    }

    // Reload glossary to show updated data
    await loadGlossary(selectedProjectId);
  };

  const selectedProject = projects.find(p => p.id === selectedProjectId);

  // Stats calculation
  const stats = {
    totalEntries: glossary.length,
    byCategory: glossary.reduce((acc, entry) => {
      acc[entry.category] = (acc[entry.category] || 0) + 1;
      return acc;
    }, {} as Record<string, number>),
    totalOccurrences: glossary.reduce((sum, e) => sum + (e.occurrenceCount || 0), 0),
  };

  if (projectsLoading && projects.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Glosario de Alias
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Mapeo de entidades originales a sus alias anonimizados
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => handleExport('csv')}
            disabled={glossary.length === 0}
            className={clsx(
              'inline-flex items-center gap-2 px-3 py-2 text-sm font-medium',
              'border border-gray-300 dark:border-gray-600 rounded-lg',
              'text-gray-700 dark:text-gray-300',
              'hover:bg-gray-50 dark:hover:bg-gray-700',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'transition-colors'
            )}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Exportar CSV
          </button>
          <button
            onClick={() => handleExport('json')}
            disabled={glossary.length === 0}
            className={clsx(
              'inline-flex items-center gap-2 px-3 py-2 text-sm font-medium',
              'border border-gray-300 dark:border-gray-600 rounded-lg',
              'text-gray-700 dark:text-gray-300',
              'hover:bg-gray-50 dark:hover:bg-gray-700',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'transition-colors'
            )}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Exportar JSON
          </button>
        </div>
      </div>

      {/* Project Selector */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Seleccionar Proyecto
        </label>
        <div className="flex flex-wrap gap-2">
          {projects.map((project) => (
            <button
              key={project.id}
              onClick={() => setSelectedProjectId(project.id)}
              className={clsx(
                'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
                selectedProjectId === project.id
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              )}
            >
              {project.name}
            </button>
          ))}
          {projects.length === 0 && (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              No hay proyectos.{' '}
              <button
                onClick={() => navigate('/projects')}
                className="text-primary-600 dark:text-primary-400 hover:underline"
              >
                Crear uno
              </button>
            </p>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      {selectedProject && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <div className="text-sm text-gray-500 dark:text-gray-400">Total Entradas</div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {stats.totalEntries}
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <div className="text-sm text-gray-500 dark:text-gray-400">Categorias</div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {Object.keys(stats.byCategory).length}
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <div className="text-sm text-gray-500 dark:text-gray-400">Ocurrencias</div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              {stats.totalOccurrences}
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <div className="text-sm text-gray-500 dark:text-gray-400">Proyecto</div>
            <div className="text-lg font-semibold text-primary-600 dark:text-primary-400 mt-1 truncate">
              {selectedProject.name}
            </div>
          </div>
        </div>
      )}

      {/* Category Distribution */}
      {Object.keys(stats.byCategory).length > 0 && (
        <div className="mb-6 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
            Distribucion por Categoria
          </h3>
          <div className="flex flex-wrap gap-2">
            {Object.entries(stats.byCategory).map(([category, count]) => (
              <div
                key={category}
                className="inline-flex items-center gap-2 px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-full"
              >
                <CategoryChip category={category as any} />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {count}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      )}

      {/* Glossary Table */}
      {!isLoading && selectedProjectId && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          {glossary.length > 0 ? (
            <GlossaryTable
              entries={glossary}
              onSaveChanges={handleSaveChanges}
              editable={true}
            />
          ) : (
            <div className="text-center py-12">
              <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                Glosario vacio
              </h3>
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                Procesa documentos para generar el glosario de alias
              </p>
              <button
                onClick={() => navigate(`/projects/${selectedProjectId}`)}
                className="text-primary-600 dark:text-primary-400 hover:underline font-medium"
              >
                Ir al proyecto
              </button>
            </div>
          )}
        </div>
      )}

      {/* No Project Selected */}
      {!selectedProjectId && projects.length > 0 && (
        <div className="text-center py-12 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
          <p className="text-gray-500 dark:text-gray-400">
            Selecciona un proyecto para ver su glosario
          </p>
        </div>
      )}
    </div>
  );
};

export default GlossaryScreen;
