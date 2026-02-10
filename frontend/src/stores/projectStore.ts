/**
 * Project Store - Zustand State Management
 *
 * Traceability:
 * - project_context.yaml#presentation.web.state_management: zustand
 * - Binding: UI-BIND-007
 */

import { create } from 'zustand';
import type { Project, ProjectSettings } from '@/types';
import { projectApi } from '@/services/api';

interface ProjectState {
  // Data
  projects: Project[];
  selectedProject: Project | null;
  settings: ProjectSettings | null;

  // Loading states
  isLoading: boolean;
  isLoadingSettings: boolean;
  error: string | null;

  // Actions
  fetchProjects: () => Promise<void>;
  selectProject: (projectId: string) => Promise<void>;
  createProject: (name: string, description?: string) => Promise<Project>;
  fetchSettings: (projectId: string) => Promise<void>;
  updateSettings: (settings: Partial<ProjectSettings>) => Promise<void>;
  clearError: () => void;
}

export const useProjectStore = create<ProjectState>((set, get) => ({
  // Initial state
  projects: [],
  selectedProject: null,
  settings: null,
  isLoading: false,
  isLoadingSettings: false,
  error: null,

  // Actions
  fetchProjects: async () => {
    set({ isLoading: true, error: null });
    try {
      const projects = await projectApi.list();
      set({ projects, isLoading: false });
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : 'Failed to fetch projects',
        isLoading: false,
      });
    }
  },

  selectProject: async (projectId: string) => {
    const { projects } = get();
    let project = projects.find((p) => p.id === projectId);

    if (!project) {
      set({ isLoading: true, error: null });
      try {
        project = await projectApi.getById(projectId);
        set((state) => ({
          projects: [...state.projects, project!],
          isLoading: false,
        }));
      } catch (e) {
        set({
          error: e instanceof Error ? e.message : 'Failed to fetch project',
          isLoading: false,
        });
        return;
      }
    }

    set({ selectedProject: project });
  },

  createProject: async (name: string, description?: string) => {
    set({ isLoading: true, error: null });
    try {
      const project = await projectApi.create({ name, description });
      set((state) => ({
        projects: [...state.projects, project],
        selectedProject: project,
        isLoading: false,
      }));
      return project;
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : 'Failed to create project',
        isLoading: false,
      });
      throw e;
    }
  },

  fetchSettings: async (projectId: string) => {
    set({ isLoadingSettings: true, error: null });
    try {
      const settings = await projectApi.getSettings(projectId);
      set({ settings, isLoadingSettings: false });
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : 'Failed to fetch settings',
        isLoadingSettings: false,
      });
    }
  },

  updateSettings: async (settings: Partial<ProjectSettings>) => {
    const { selectedProject } = get();
    if (!selectedProject) return;

    set({ isLoadingSettings: true, error: null });
    try {
      const updated = await projectApi.updateSettings(
        selectedProject.id,
        settings
      );
      set({ settings: updated, isLoadingSettings: false });
    } catch (e) {
      set({
        error: e instanceof Error ? e.message : 'Failed to update settings',
        isLoadingSettings: false,
      });
    }
  },

  clearError: () => set({ error: null }),
}));
