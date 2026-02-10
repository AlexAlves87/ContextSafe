/**
 * SettingsPanel - Anonymization level and settings configuration
 *
 * Traceability:
 * - Contract: CNT-UI-COMP-008
 * - Binding: UI-BIND-008
 */

import React, { useState, useEffect } from 'react';
import clsx from 'clsx';
import type { ProjectSettings, AnonymizationLevel, PiiCategory } from '@/types';
import { ANONYMIZATION_LEVEL_LABELS, PII_CATEGORY_LABELS } from '@/types';

interface SettingsPanelProps {
  settings: ProjectSettings;
  onSave: (settings: ProjectSettings) => void;
  isLoading?: boolean;
  className?: string;
}

const ALL_CATEGORIES: PiiCategory[] = [
  'person_name',
  'organization',
  'address',
  'dni_nie',
  'passport',
  'phone',
  'email',
  'bank_account',
  'credit_card',
  'date_of_birth',
  'medical_record',
  'license_plate',
  'social_security',
];

export const SettingsPanel: React.FC<SettingsPanelProps> = ({
  settings,
  onSave,
  isLoading = false,
  className,
}) => {
  const [localSettings, setLocalSettings] = useState<ProjectSettings>(settings);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    setLocalSettings(settings);
    setHasChanges(false);
  }, [settings]);

  const updateSettings = (updates: Partial<ProjectSettings>) => {
    setLocalSettings((prev) => ({ ...prev, ...updates }));
    setHasChanges(true);
  };

  const handleSave = () => {
    onSave(localSettings);
    setHasChanges(false);
  };

  const handleReset = () => {
    setLocalSettings(settings);
    setHasChanges(false);
  };

  const toggleCategory = (category: PiiCategory) => {
    const current = localSettings.enabledCategories;
    const updated = current.includes(category)
      ? current.filter((c) => c !== category)
      : [...current, category];
    updateSettings({ enabledCategories: updated });
  };

  return (
    <div className={clsx('space-y-6', className)}>
      {/* Anonymization Level */}
      <section>
        <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
          Nivel de anonimización
        </h3>
        <div className="space-y-2">
          {(
            Object.entries(ANONYMIZATION_LEVEL_LABELS) as [
              AnonymizationLevel,
              string,
            ][]
          ).map(([level, label]) => (
            <label
              key={level}
              className={clsx(
                'flex items-center gap-3 p-3 rounded-lg border cursor-pointer',
                'transition-colors duration-150',
                {
                  'border-primary-500 bg-primary-50 dark:bg-primary-900/20':
                    localSettings.anonymizationLevel === level,
                  'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800':
                    localSettings.anonymizationLevel !== level,
                }
              )}
            >
              <input
                type="radio"
                name="anonymizationLevel"
                value={level}
                checked={localSettings.anonymizationLevel === level}
                onChange={() => updateSettings({ anonymizationLevel: level })}
                className="sr-only"
              />
              <div
                className={clsx(
                  'w-4 h-4 rounded-full border-2 flex items-center justify-center',
                  {
                    'border-primary-500': localSettings.anonymizationLevel === level,
                    'border-gray-300 dark:border-gray-600':
                      localSettings.anonymizationLevel !== level,
                  }
                )}
              >
                {localSettings.anonymizationLevel === level && (
                  <div className="w-2 h-2 rounded-full bg-primary-500" />
                )}
              </div>
              <span className="text-sm text-gray-700 dark:text-gray-300">
                {label}
              </span>
              {level === 'intermediate' && (
                <span className="ml-auto text-xs bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 px-2 py-0.5 rounded">
                  Recomendado
                </span>
              )}
            </label>
          ))}
        </div>
      </section>

      {/* PII Categories */}
      <section>
        <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
          Categorías PII habilitadas
        </h3>
        <div className="grid grid-cols-2 gap-2">
          {ALL_CATEGORIES.map((category) => (
            <label
              key={category}
              className={clsx(
                'flex items-center gap-2 p-2 rounded-lg border cursor-pointer',
                'text-sm transition-colors duration-150',
                {
                  'border-primary-500 bg-primary-50 dark:bg-primary-900/20':
                    localSettings.enabledCategories.includes(category),
                  'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800':
                    !localSettings.enabledCategories.includes(category),
                }
              )}
            >
              <input
                type="checkbox"
                checked={localSettings.enabledCategories.includes(category)}
                onChange={() => toggleCategory(category)}
                className="sr-only"
              />
              <div
                className={clsx(
                  'w-4 h-4 rounded border flex items-center justify-center',
                  {
                    'bg-primary-500 border-primary-500':
                      localSettings.enabledCategories.includes(category),
                    'border-gray-300 dark:border-gray-600':
                      !localSettings.enabledCategories.includes(category),
                  }
                )}
              >
                {localSettings.enabledCategories.includes(category) && (
                  <svg
                    className="w-3 h-3 text-white"
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
              </div>
              <span className="text-gray-700 dark:text-gray-300">
                {PII_CATEGORY_LABELS[category]}
              </span>
            </label>
          ))}
        </div>
      </section>

      {/* Options */}
      <section>
        <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
          Opciones avanzadas
        </h3>
        <div className="space-y-3">
          {[
            {
              key: 'maintainConsistency' as const,
              label: 'Mantener consistencia entre documentos',
              description: 'El mismo texto siempre recibe el mismo alias',
            },
            {
              key: 'preserveFormatting' as const,
              label: 'Preservar formato original',
              description: 'Mantener estructura y estilos del documento',
            },
            {
              key: 'generateAuditReport' as const,
              label: 'Generar informe de auditoría',
              description: 'Incluir registro detallado de cambios',
            },
          ].map(({ key, label, description }) => (
            <label
              key={key}
              className="flex items-start gap-3 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={localSettings[key]}
                onChange={(e) => updateSettings({ [key]: e.target.checked })}
                className={clsx(
                  'mt-1 w-4 h-4 rounded',
                  'text-primary-500 border-gray-300 dark:border-gray-600',
                  'focus:ring-primary-500'
                )}
              />
              <div>
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  {label}
                </span>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {description}
                </p>
              </div>
            </label>
          ))}
        </div>
      </section>

      {/* Actions */}
      <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
        <button
          type="button"
          onClick={handleReset}
          disabled={!hasChanges || isLoading}
          className={clsx(
            'px-4 py-2 text-sm font-medium rounded-lg',
            'border border-gray-300 dark:border-gray-600',
            'text-gray-700 dark:text-gray-300',
            'hover:bg-gray-50 dark:hover:bg-gray-800',
            'focus:outline-none focus:ring-2 focus:ring-primary-500',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          Cancelar
        </button>
        <button
          type="button"
          onClick={handleSave}
          disabled={!hasChanges || isLoading}
          className={clsx(
            'px-4 py-2 text-sm font-medium rounded-lg',
            'bg-primary-500 text-white',
            'hover:bg-primary-600',
            'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          {isLoading ? 'Guardando...' : 'Guardar cambios'}
        </button>
      </div>
    </div>
  );
};

export default SettingsPanel;
