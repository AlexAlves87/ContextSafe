/**
 * ProjectSelector - Project dropdown with create option
 *
 * Traceability:
 * - Contract: CNT-UI-COMP-007
 * - Binding: UI-BIND-007
 */

import React, { useState, useRef, useEffect } from 'react';
import clsx from 'clsx';
import type { Project } from '@/types';

interface ProjectSelectorProps {
  projects: Project[];
  selectedId: string;
  onSelect: (id: string) => void;
  onCreateNew?: () => void;
  className?: string;
}

export const ProjectSelector: React.FC<ProjectSelectorProps> = ({
  projects,
  selectedId,
  onSelect,
  onCreateNew,
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Guard against undefined projects
  const projectList = projects ?? [];
  const selectedProject = projectList.find((p) => p.id === selectedId);

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close on Escape
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
    } else if (e.key === 'ArrowDown' && !isOpen) {
      e.preventDefault();
      setIsOpen(true);
    }
  };

  return (
    <div ref={containerRef} className={clsx('relative', className)}>
      {/* Trigger button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={handleKeyDown}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label="Seleccionar proyecto"
        className={clsx(
          'flex items-center gap-2 px-3 py-2 w-full',
          'text-left text-sm',
          'bg-white dark:bg-gray-800',
          'border border-gray-300 dark:border-gray-600 rounded-lg',
          'hover:bg-gray-50 dark:hover:bg-gray-700',
          'focus:outline-none focus:ring-2 focus:ring-primary-500'
        )}
      >
        {/* Folder icon */}
        <svg
          className="w-5 h-5 text-gray-400"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
        </svg>

        {/* Selected project */}
        <span className="flex-1 truncate font-medium text-gray-900 dark:text-white">
          {selectedProject?.name || 'Seleccionar proyecto'}
        </span>

        {/* Chevron */}
        <svg
          className={clsx('w-5 h-5 text-gray-400 transition-transform', {
            'rotate-180': isOpen,
          })}
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div
          role="listbox"
          className={clsx(
            'absolute z-50 mt-1 w-full',
            'bg-white dark:bg-gray-800',
            'border border-gray-200 dark:border-gray-700',
            'rounded-lg shadow-lg',
            'max-h-60 overflow-auto'
          )}
        >
          {projectList.length === 0 ? (
            <div className="px-3 py-4 text-sm text-gray-500 dark:text-gray-400 text-center">
              No hay proyectos
            </div>
          ) : (
            projectList.map((project) => (
              <button
                key={project.id}
                role="option"
                aria-selected={project.id === selectedId}
                onClick={() => {
                  onSelect(project.id);
                  setIsOpen(false);
                }}
                className={clsx(
                  'flex items-center gap-3 w-full px-3 py-2 text-left',
                  'hover:bg-gray-50 dark:hover:bg-gray-700',
                  'focus:outline-none focus:bg-gray-50 dark:focus:bg-gray-700',
                  {
                    'bg-primary-50 dark:bg-primary-900/20':
                      project.id === selectedId,
                  }
                )}
              >
                <svg
                  className="w-5 h-5 text-gray-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
                </svg>

                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {project.name}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {project.documentCount} docs · {project.entityCount} entidades
                  </p>
                </div>

                {project.id === selectedId && (
                  <svg
                    className="w-5 h-5 text-primary-500"
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
              </button>
            ))
          )}

          {/* Create new */}
          {onCreateNew && (
            <>
              <hr className="border-gray-200 dark:border-gray-700" />
              <button
                type="button"
                onClick={() => {
                  onCreateNew();
                  setIsOpen(false);
                }}
                className={clsx(
                  'flex items-center gap-2 w-full px-3 py-2',
                  'text-sm text-primary-600 dark:text-primary-400',
                  'hover:bg-primary-50 dark:hover:bg-primary-900/20',
                  'focus:outline-none focus:bg-primary-50 dark:focus:bg-primary-900/20'
                )}
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                    clipRule="evenodd"
                  />
                </svg>
                Crear nuevo proyecto
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default ProjectSelector;
