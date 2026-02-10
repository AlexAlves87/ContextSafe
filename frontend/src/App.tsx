/**
 * App - Aplicacion local ContextSafe
 *
 * Rutas:
 *   - / → Proyectos (pantalla principal)
 *   - /projects/:projectId → Workspace
 *   - /projects/:projectId/process → Procesamiento
 *   - /projects/:projectId/documents/:documentId → Preview
 */

import React from 'react';
import {
  BrowserRouter,
  Routes,
  Route,
} from 'react-router-dom';
import { ErrorBoundary } from '@/components';
import { MainLayout } from '@/layouts';
import {
  WorkspaceScreen,
  ProcessingScreen,
  PreviewScreen,
  ProjectsScreen,
  GlossaryScreen,
  SettingsScreen,
} from '@/screens';

// Welcome screen when no project is selected
const WelcomeScreen: React.FC = () => {
  return (
    <div className="max-w-2xl mx-auto text-center py-12">
      <svg className="w-20 h-20 mx-auto text-primary-500 mb-6" fill="currentColor" viewBox="0 0 24 24">
        <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z" />
      </svg>
      <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
        ContextSafe
      </h1>
      <p className="text-lg text-gray-500 dark:text-gray-400 mb-8">
        Selecciona un proyecto del menu superior o crea uno nuevo para comenzar a anonimizar documentos.
      </p>
    </div>
  );
};

// 404 page
const NotFoundScreen: React.FC = () => {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-gray-200 dark:text-gray-700">404</h1>
        <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">Pagina no encontrada</p>
        <a href="/" className="mt-6 inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-primary-600 dark:text-primary-400 hover:underline">
          Volver a inicio
        </a>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <MainLayout>
          <Routes>
            {/* Pantalla principal */}
            <Route path="/" element={<WelcomeScreen />} />

            {/* Proyectos */}
            <Route path="/projects" element={<ProjectsScreen />} />
            <Route path="/projects/:projectId" element={<WorkspaceScreen />} />
            <Route path="/projects/:projectId/process" element={<ProcessingScreen />} />
            <Route path="/projects/:projectId/documents" element={<WorkspaceScreen />} />
            <Route path="/projects/:projectId/documents/:documentId" element={<PreviewScreen />} />

            {/* Glossary y Settings */}
            <Route path="/glossary" element={<GlossaryScreen />} />
            <Route path="/settings" element={<SettingsScreen />} />

            {/* 404 */}
            <Route path="*" element={<NotFoundScreen />} />
          </Routes>
        </MainLayout>
      </BrowserRouter>
    </ErrorBoundary>
  );
};

export default App;
