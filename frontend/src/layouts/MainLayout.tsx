/**
 * MainLayout - Main application layout with header, sidebar, and content area
 *
 * Traceability:
 * - Contract: CNT-UI-LAYOUT-001
 *
 * Layout Structure (from contract):
 * - Header: 64px fixed top (Logo, ProjectSelector, UserMenu)
 * - Sidebar: 240px/64px fixed left (Navigation, Settings)
 * - Content: main area with padding, vertical scroll
 *
 * Responsive breakpoints:
 * - mobile: < 768px - sidebar hidden, hamburger menu
 * - tablet: 768px - 1024px - sidebar collapsed
 * - desktop: >= 1024px - sidebar expanded
 */

import React, { ReactNode, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import { Sidebar, ProjectSelector, ToastContainer, NotificationToast } from '@/components';
import { useProjectStore, useUIStore } from '@/stores';
import { projectApi } from '@/services/api';

interface MainLayoutProps {
  children: ReactNode;
  sidebarCollapsed?: boolean;
  onToggleSidebar?: () => void;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  children,
  sidebarCollapsed: controlledCollapsed,
  onToggleSidebar: controlledToggle,
}) => {
  const {
    sidebarCollapsed: storeCollapsed,
    toggleSidebar: storeToggle,
    toasts,
    removeToast,
    resolvedTheme,
    setTheme,
  } = useUIStore();

  const { projects, selectedProject, fetchProjects, selectProject } =
    useProjectStore();

  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newProjectName, setNewProjectName] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return;
    setIsCreating(true);
    try {
      const project = await projectApi.create({ name: newProjectName.trim() });
      await fetchProjects();
      setShowCreateModal(false);
      setNewProjectName('');
      navigate(`/projects/${project.id}`);
    } catch (error) {
      console.error('Error creating project:', error);
    } finally {
      setIsCreating(false);
    }
  };

  const handleSelectProject = (id: string) => {
    selectProject(id);
    navigate(`/projects/${id}`);
  };

  const sidebarCollapsed = controlledCollapsed ?? storeCollapsed;
  const toggleSidebar = controlledToggle ?? storeToggle;

  // Force dark mode for tool
  useEffect(() => {
    document.documentElement.classList.add('dark');
    return () => {
      document.documentElement.classList.remove('dark');
    };
  }, []);

  // Fetch projects on mount
  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  // Handle responsive sidebar
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setMobileMenuOpen(false);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div className="min-h-screen bg-background overflow-x-hidden">
      {/* Skip link for accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-4 focus:bg-primary focus:text-primary-foreground"
      >
        Saltar al contenido principal
      </a>

      {/* Fixed top container: Header */}
      <div className="fixed top-0 left-0 right-0 z-40">
        {/* Header */}
        <header
          role="banner"
          className={clsx(
            'h-14 px-4',
            'bg-card',
            'border-b border-border',
            'shadow-sm',
            'flex items-center gap-3'
          )}
        >
        {/* Mobile menu button */}
        <button
          type="button"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-2 rounded text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
          aria-label="Abrir menú"
        >
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z"
              clipRule="evenodd"
            />
          </svg>
        </button>

        {/* Logo */}
        <div className="flex items-center gap-2">
          <svg
            className="w-8 h-8 text-primary"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z" />
          </svg>
          <span className="text-xl font-bold text-foreground hidden sm:inline">
            ContextSafe
          </span>
        </div>

        {/* Project selector */}
        <div className="flex-1 max-w-xs hidden sm:block">
          <ProjectSelector
            projects={projects}
            selectedId={selectedProject?.id || ''}
            onSelect={handleSelectProject}
            onCreateNew={() => setShowCreateModal(true)}
          />
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Theme toggle */}
        <button
          type="button"
          onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
          className="p-2 rounded text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
          aria-label={`Cambiar a modo ${resolvedTheme === 'dark' ? 'claro' : 'oscuro'}`}
        >
          {resolvedTheme === 'dark' ? (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z"
                clipRule="evenodd"
              />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
            </svg>
          )}
        </button>

        {/* User menu */}
        <button
          type="button"
          className="flex items-center gap-2 p-2 rounded hover:bg-accent hover:text-accent-foreground transition-colors"
          aria-label="Menú de usuario"
        >
          <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
            <span className="text-sm font-semibold text-primary">
              U
            </span>
          </div>
        </button>
        </header>

      </div>

      {/* Sidebar - Desktop */}
      <div
        className={clsx(
          'hidden md:block fixed left-0 top-[6.5rem] bottom-0 z-20',
          'transition-all duration-200',
          {
            'w-64': !sidebarCollapsed,
            'w-16': sidebarCollapsed,
          }
        )}
      >
        <Sidebar
          currentPath=""
          collapsed={sidebarCollapsed}
          onToggle={toggleSidebar}
        />
      </div>

      {/* Sidebar - Mobile overlay */}
      {mobileMenuOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-black/50 md:hidden"
            onClick={() => setMobileMenuOpen(false)}
          />
          <div className="fixed left-0 top-[6.5rem] bottom-0 z-50 w-64 md:hidden">
            <Sidebar currentPath="" collapsed={false} />
          </div>
        </>
      )}

      {/* Main content */}
      <main
        id="main-content"
        role="main"
        className={clsx(
          'pt-[6.5rem] min-h-screen',
          'transition-all duration-200',
          {
            'md:pl-64': !sidebarCollapsed,
            'md:pl-16': sidebarCollapsed,
          }
        )}
      >
        <div className="p-4 md:p-5 lg:p-6">{children}</div>
      </main>

      {/* Create project modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-background/80 backdrop-blur-sm" onClick={() => setShowCreateModal(false)} />
          <div className="relative bg-popover rounded border border-border shadow-2xl p-6 w-full max-w-md mx-4">
            <h2 className="text-xl font-bold text-popover-foreground mb-4">
              Crear nuevo proyecto
            </h2>
            <input
              type="text"
              value={newProjectName}
              onChange={(e) => setNewProjectName(e.target.value)}
              placeholder="Nombre del proyecto (ej: Caso_Legal_001)"
              className="input mb-4"
              onKeyDown={(e) => e.key === 'Enter' && handleCreateProject()}
              autoFocus
            />
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => { setShowCreateModal(false); setNewProjectName(''); }}
                className="btn-secondary"
              >
                Cancelar
              </button>
              <button
                onClick={handleCreateProject}
                disabled={isCreating || !newProjectName.trim()}
                className="btn-primary"
              >
                {isCreating ? 'Creando...' : 'Crear proyecto'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Toast notifications */}
      <ToastContainer>
        {toasts.map((toast) => (
          <NotificationToast
            key={toast.id}
            message={toast.message}
            type={toast.type}
            onClose={() => removeToast(toast.id)}
          />
        ))}
      </ToastContainer>
    </div>
  );
};

export default MainLayout;
