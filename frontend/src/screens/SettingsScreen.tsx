/**
 * SettingsScreen - Application settings and configuration
 */

import React, { useState, useEffect } from 'react';
import clsx from 'clsx';
import type { AnonymizationLevel, PiiCategory } from '@/types';
import { ANONYMIZATION_LEVEL_LABELS, PII_CATEGORY_LABELS } from '@/types';

interface AppSettings {
  theme: 'light' | 'dark' | 'system';
  language: 'es' | 'en';
  defaultAnonymizationLevel: AnonymizationLevel;
  enabledCategories: PiiCategory[];
  confidenceThreshold: number;
  exportFormat: 'pdf' | 'docx' | 'txt';
  preserveFormatting: boolean;
  showConfidenceScores: boolean;
  autoProcessOnUpload: boolean;
}

const DEFAULT_SETTINGS: AppSettings = {
  theme: 'system',
  language: 'es',
  defaultAnonymizationLevel: 'intermediate',
  enabledCategories: [
    'person_name', 'dni_nie', 'passport', 'phone', 'email',
    'address', 'bank_account', 'credit_card', 'date_of_birth',
    'medical_record', 'social_security'
  ],
  confidenceThreshold: 0.5,
  exportFormat: 'pdf',
  preserveFormatting: true,
  showConfidenceScores: true,
  autoProcessOnUpload: false,
};

const ALL_CATEGORIES: PiiCategory[] = [
  'person_name', 'organization', 'address', 'dni_nie', 'passport',
  'phone', 'email', 'bank_account', 'credit_card', 'date_of_birth',
  'medical_record', 'license_plate', 'social_security', 'ip_address', 'url'
];

export const SettingsScreen: React.FC = () => {
  const [settings, setSettings] = useState<AppSettings>(() => {
    const saved = localStorage.getItem('contextsafe_settings');
    return saved ? { ...DEFAULT_SETTINGS, ...JSON.parse(saved) } : DEFAULT_SETTINGS;
  });
  const [saved, setSaved] = useState(false);

  // Apply theme when changed
  useEffect(() => {
    const root = document.documentElement;
    if (settings.theme === 'dark') {
      root.classList.add('dark');
    } else if (settings.theme === 'light') {
      root.classList.remove('dark');
    } else {
      // system
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        root.classList.add('dark');
      } else {
        root.classList.remove('dark');
      }
    }
  }, [settings.theme]);

  const handleSave = () => {
    localStorage.setItem('contextsafe_settings', JSON.stringify(settings));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleReset = () => {
    setSettings(DEFAULT_SETTINGS);
    localStorage.removeItem('contextsafe_settings');
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const toggleCategory = (category: PiiCategory) => {
    setSettings(prev => ({
      ...prev,
      enabledCategories: prev.enabledCategories.includes(category)
        ? prev.enabledCategories.filter(c => c !== category)
        : [...prev.enabledCategories, category]
    }));
  };

  const selectAllCategories = () => {
    setSettings(prev => ({ ...prev, enabledCategories: [...ALL_CATEGORIES] }));
  };

  const deselectAllCategories = () => {
    setSettings(prev => ({ ...prev, enabledCategories: [] }));
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Configuracion
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Personaliza el comportamiento de la aplicacion
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleReset}
            className={clsx(
              'px-4 py-2 text-sm font-medium',
              'text-gray-700 dark:text-gray-300',
              'border border-gray-300 dark:border-gray-600 rounded-lg',
              'hover:bg-gray-50 dark:hover:bg-gray-700',
              'transition-colors'
            )}
          >
            Restaurar
          </button>
          <button
            onClick={handleSave}
            className={clsx(
              'px-4 py-2 text-sm font-medium text-white',
              'bg-primary-600 hover:bg-primary-700 rounded-lg',
              'transition-colors'
            )}
          >
            {saved ? 'Guardado!' : 'Guardar cambios'}
          </button>
        </div>
      </div>

      <div className="space-y-6">
        {/* Appearance Section */}
        <section className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Apariencia
            </h2>
          </div>
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Tema
              </label>
              <div className="flex gap-3">
                {(['light', 'dark', 'system'] as const).map((theme) => (
                  <button
                    key={theme}
                    onClick={() => setSettings(prev => ({ ...prev, theme }))}
                    className={clsx(
                      'flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors',
                      settings.theme === theme
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300'
                        : 'border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700'
                    )}
                  >
                    {theme === 'light' && (
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clipRule="evenodd" />
                      </svg>
                    )}
                    {theme === 'dark' && (
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
                      </svg>
                    )}
                    {theme === 'system' && (
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M3 5a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2h-2.22l.123.489.804.804A1 1 0 0113 18H7a1 1 0 01-.707-1.707l.804-.804L7.22 15H5a2 2 0 01-2-2V5zm5.771 7H5V5h10v7H8.771z" clipRule="evenodd" />
                      </svg>
                    )}
                    <span className="text-sm font-medium">
                      {theme === 'light' ? 'Claro' : theme === 'dark' ? 'Oscuro' : 'Sistema'}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Idioma
              </label>
              <select
                value={settings.language}
                onChange={(e) => setSettings(prev => ({ ...prev, language: e.target.value as 'es' | 'en' }))}
                className={clsx(
                  'w-full max-w-xs px-3 py-2 rounded-lg border',
                  'border-gray-300 dark:border-gray-600',
                  'bg-white dark:bg-gray-700',
                  'text-gray-900 dark:text-white',
                  'focus:outline-none focus:ring-2 focus:ring-primary-500'
                )}
              >
                <option value="es">Espanol</option>
                <option value="en">English</option>
              </select>
            </div>
          </div>
        </section>

        {/* Anonymization Section */}
        <section className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Anonimizacion
            </h2>
          </div>
          <div className="p-6 space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Nivel de anonimizacion por defecto
              </label>
              <div className="space-y-2">
                {(['basic', 'intermediate', 'advanced'] as const).map((level) => (
                  <label
                    key={level}
                    className={clsx(
                      'flex items-center p-3 rounded-lg border cursor-pointer transition-colors',
                      settings.defaultAnonymizationLevel === level
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
                    )}
                  >
                    <input
                      type="radio"
                      name="anonymizationLevel"
                      value={level}
                      checked={settings.defaultAnonymizationLevel === level}
                      onChange={() => setSettings(prev => ({ ...prev, defaultAnonymizationLevel: level }))}
                      className="sr-only"
                    />
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900 dark:text-white">
                        {ANONYMIZATION_LEVEL_LABELS[level]}
                      </div>
                    </div>
                    {settings.defaultAnonymizationLevel === level && (
                      <svg className="w-5 h-5 text-primary-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    )}
                  </label>
                ))}
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Categorias de PII habilitadas
                </label>
                <div className="flex gap-2">
                  <button
                    onClick={selectAllCategories}
                    className="text-xs text-primary-600 dark:text-primary-400 hover:underline"
                  >
                    Seleccionar todas
                  </button>
                  <span className="text-gray-300 dark:text-gray-600">|</span>
                  <button
                    onClick={deselectAllCategories}
                    className="text-xs text-primary-600 dark:text-primary-400 hover:underline"
                  >
                    Deseleccionar
                  </button>
                </div>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {ALL_CATEGORIES.map((category) => (
                  <label
                    key={category}
                    className={clsx(
                      'flex items-center gap-2 p-2 rounded-lg border cursor-pointer transition-colors',
                      settings.enabledCategories.includes(category)
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
                    )}
                  >
                    <input
                      type="checkbox"
                      checked={settings.enabledCategories.includes(category)}
                      onChange={() => toggleCategory(category)}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {PII_CATEGORY_LABELS[category]}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Umbral de confianza: {(settings.confidenceThreshold * 100).toFixed(0)}%
              </label>
              <input
                type="range"
                min="0"
                max="100"
                value={settings.confidenceThreshold * 100}
                onChange={(e) => setSettings(prev => ({ ...prev, confidenceThreshold: Number(e.target.value) / 100 }))}
                className="w-full max-w-md"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Solo se detectaran entidades con confianza superior a este umbral
              </p>
            </div>
          </div>
        </section>

        {/* Export Section */}
        <section className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Exportacion
            </h2>
          </div>
          <div className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Formato de exportacion por defecto
              </label>
              <select
                value={settings.exportFormat}
                onChange={(e) => setSettings(prev => ({ ...prev, exportFormat: e.target.value as 'pdf' | 'docx' | 'txt' }))}
                className={clsx(
                  'w-full max-w-xs px-3 py-2 rounded-lg border',
                  'border-gray-300 dark:border-gray-600',
                  'bg-white dark:bg-gray-700',
                  'text-gray-900 dark:text-white',
                  'focus:outline-none focus:ring-2 focus:ring-primary-500'
                )}
              >
                <option value="pdf">PDF</option>
                <option value="docx">DOCX (Word)</option>
                <option value="txt">TXT (Texto plano)</option>
              </select>
            </div>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.preserveFormatting}
                onChange={(e) => setSettings(prev => ({ ...prev, preserveFormatting: e.target.checked }))}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">
                Preservar formato original del documento
              </span>
            </label>
          </div>
        </section>

        {/* Behavior Section */}
        <section className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Comportamiento
            </h2>
          </div>
          <div className="p-6 space-y-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.showConfidenceScores}
                onChange={(e) => setSettings(prev => ({ ...prev, showConfidenceScores: e.target.checked }))}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <div>
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Mostrar puntuaciones de confianza
                </span>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Muestra el nivel de confianza para cada entidad detectada
                </p>
              </div>
            </label>

            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.autoProcessOnUpload}
                onChange={(e) => setSettings(prev => ({ ...prev, autoProcessOnUpload: e.target.checked }))}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <div>
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  Procesar automaticamente al subir
                </span>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  Inicia la deteccion automaticamente cuando se sube un documento
                </p>
              </div>
            </label>
          </div>
        </section>

        {/* About Section */}
        <section className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Acerca de
            </h2>
          </div>
          <div className="p-6">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center">
                <svg className="w-7 h-7 text-primary-600 dark:text-primary-400" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z" />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  ContextSafe
                </h3>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Version 0.1.0 - 100% Procesamiento Local
                </p>
              </div>
            </div>
            <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">
              ContextSafe es una herramienta de anonimizacion de documentos que procesa
              todos los datos localmente, sin enviar informacion a servidores externos.
              Ideal para documentos legales, medicos y cualquier informacion sensible.
            </p>
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                ContextSafe - Document Anonymization
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default SettingsScreen;
