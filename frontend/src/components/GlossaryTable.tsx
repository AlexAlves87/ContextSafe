/**
 * GlossaryTable - Entity to alias mapping table with inline editing
 *
 * Traceability:
 * - Contract: CNT-UI-COMP-006
 * - Binding: UI-BIND-006
 *
 * @modified Added inline alias editing support
 */

import React, { useState, useMemo, useCallback } from 'react';
import clsx from 'clsx';
import type { GlossaryEntry } from '@/types';
import { PII_CATEGORY_LABELS } from '@/types';
import { CategoryChip } from './CategoryChip';
import { useIsMobile } from '@/hooks';

interface AliasChange {
  originalTerm: string;
  category: string;
  newAlias: string;
  newCategory?: string;
}

interface OriginalTextChange {
  entryId: string;
  oldOriginalText: string;
  newOriginalText: string;
  category: string;
  alias: string;
}

interface GlossaryTableProps {
  entries: GlossaryEntry[];
  originalDocumentText?: string; // Full document text for context extraction
  onSearch?: (query: string) => void;
  onSaveChanges?: (changes: AliasChange[], deletions?: string[]) => Promise<void>;
  onSaveOriginalTextChanges?: (changes: OriginalTextChange[]) => Promise<void>;
  onFindInText?: (entry: GlossaryEntry) => void;
  /** Called when entry is selected for editing (mobile) */
  onSelectEntry?: (entry: GlossaryEntry) => void;
  sortBy?: 'entity' | 'alias' | 'category';
  editable?: boolean;
  /** Anonymization level - when 'basic', alias editing is disabled (masking is irreversible) */
  anonymizationLevel?: 'basic' | 'intermediate' | 'advanced';
  className?: string;
  variant?: 'default' | 'industrial';
}

// All available categories for the dropdown
const ALL_CATEGORIES: Array<{ value: string; label: string }> = Object.entries(PII_CATEGORY_LABELS).map(
  ([value, label]) => ({ value, label })
);

type SortKey = 'entity' | 'alias' | 'category' | 'count';
type SortDirection = 'asc' | 'desc';

// Helper function to extract context around a term in text
function getTextContext(fullText: string, term: string, wordCount: number = 5): {
  before: string;
  term: string;
  after: string;
} | null {
  if (!fullText || !term) return null;

  // Find the term in the text (case-insensitive)
  const lowerText = fullText.toLowerCase();
  const lowerTerm = term.toLowerCase();
  const termIndex = lowerText.indexOf(lowerTerm);

  if (termIndex === -1) return null;

  // Get text before and after the term
  const textBefore = fullText.slice(0, termIndex);
  const actualTerm = fullText.slice(termIndex, termIndex + term.length);
  const textAfter = fullText.slice(termIndex + term.length);

  // Split into words and get N words before/after
  const wordsBefore = textBefore.trim().split(/\s+/).filter(w => w);
  const wordsAfter = textAfter.trim().split(/\s+/).filter(w => w);

  const contextBefore = wordsBefore.slice(-wordCount).join(' ');
  const contextAfter = wordsAfter.slice(0, wordCount).join(' ');

  return {
    before: contextBefore ? `...${contextBefore} ` : '',
    term: actualTerm,
    after: contextAfter ? ` ${contextAfter}...` : '',
  };
}

// Category abbreviations for industrial display
const CATEGORY_ABBREV: Record<string, string> = {
  person_name: 'PER',
  dni_nie: 'DNI',
  dni: 'DNI',
  nie: 'NIE',
  phone: 'TEL',
  email: 'EMAIL',
  address: 'DIR',
  location: 'LOC',
  organization: 'ORG',
  date: 'FECH',
  iban: 'IBAN',
  professional_id: 'PROF',
  case_number: 'EXP',
  other: 'OTRO',
};

export const GlossaryTable: React.FC<GlossaryTableProps> = ({
  entries,
  originalDocumentText,
  onSearch,
  onSaveChanges,
  onSaveOriginalTextChanges,
  onFindInText,
  onSelectEntry,
  sortBy: initialSortBy,
  editable = true,
  anonymizationLevel = 'intermediate',
  className,
  variant = 'default',
}) => {
  const isIndustrial = variant === 'industrial';
  const isMobile = useIsMobile();
  // BASIC level: aliases are asterisks (masking) - editing alias is disabled
  // User can still add/remove entities, but cannot change the alias
  const isMaskingLevel = anonymizationLevel === 'basic';
  const aliasEditable = editable && !isMaskingLevel;
  const [searchQuery, setSearchQuery] = useState('');
  const [sortKey, setSortKey] = useState<SortKey>(initialSortBy || 'entity');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [editedAliases, setEditedAliases] = useState<Record<string, string>>({});
  const [editedCategories, setEditedCategories] = useState<Record<string, string>>({});
  const [editedOriginalTexts, setEditedOriginalTexts] = useState<Record<string, string>>({});
  const [deletedEntryIds, setDeletedEntryIds] = useState<Set<string>>(new Set());
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  // Modal state for editing original text
  const [editModalEntry, setEditModalEntry] = useState<GlossaryEntry | null>(null);
  const [editModalText, setEditModalText] = useState('');

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    onSearch?.(query);
  };

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDirection('asc');
    }
  };

  const handleAliasChange = useCallback((entryId: string, newAlias: string) => {
    setEditedAliases(prev => ({
      ...prev,
      [entryId]: newAlias,
    }));
    setSaveMessage(null);
  }, []);

  const handleCategoryChange = useCallback((entryId: string, newCategory: string) => {
    setEditedCategories(prev => ({
      ...prev,
      [entryId]: newCategory,
    }));
    setSaveMessage(null);
  }, []);

  const handleOriginalTextChange = useCallback((entryId: string, newText: string) => {
    setEditedOriginalTexts(prev => ({
      ...prev,
      [entryId]: newText,
    }));
    setSaveMessage(null);
  }, []);

  const toggleDelete = useCallback((entryId: string) => {
    setDeletedEntryIds(prev => {
      const next = new Set(prev);
      if (next.has(entryId)) {
        next.delete(entryId);
      } else {
        next.add(entryId);
      }
      return next;
    });
    setSaveMessage(null);
  }, []);

  // Open edit modal for original text
  const handleOpenEditModal = useCallback((entry: GlossaryEntry) => {
    setEditModalEntry(entry);
    setEditModalText(editedOriginalTexts[entry.id] ?? entry.originalText);
  }, [editedOriginalTexts]);

  // Save from edit modal
  const handleSaveEditModal = useCallback(() => {
    if (editModalEntry && editModalText.trim()) {
      handleOriginalTextChange(editModalEntry.id, editModalText.trim());
    }
    setEditModalEntry(null);
    setEditModalText('');
  }, [editModalEntry, editModalText, handleOriginalTextChange]);

  const hasAliasChanges = useMemo(() => {
    const aliasChanged = Object.keys(editedAliases).some(id => {
      const entry = entries.find(e => e.id === id);
      return entry && editedAliases[id] !== entry.alias;
    });
    const categoryChanged = Object.keys(editedCategories).some(id => {
      const entry = entries.find(e => e.id === id);
      return entry && editedCategories[id].toLowerCase() !== entry.category.toLowerCase();
    });
    return aliasChanged || categoryChanged;
  }, [editedAliases, editedCategories, entries]);

  const hasOriginalTextChanges = useMemo(() => {
    return Object.keys(editedOriginalTexts).some(id => {
      const entry = entries.find(e => e.id === id);
      return entry && editedOriginalTexts[id] !== entry.originalText;
    });
  }, [editedOriginalTexts, entries]);

  const hasDeletions = deletedEntryIds.size > 0;
  const hasChanges = hasAliasChanges || hasOriginalTextChanges || hasDeletions;

  const handleSaveChanges = async () => {
    if (!hasChanges) return;

    setIsSaving(true);
    setSaveMessage(null);

    try {
      let totalChanges = 0;

      // Save alias/category changes AND deletions
      if ((hasAliasChanges || hasDeletions) && onSaveChanges) {
        const aliasChanges: AliasChange[] = [];
        const deletions = Array.from(deletedEntryIds);

        // Collect all entry IDs that have either alias or category changes
        const changedEntryIds = new Set([
          ...Object.keys(editedAliases),
          ...Object.keys(editedCategories),
        ]);

        // Build changes for entries NOT marked for deletion
        for (const entryId of changedEntryIds) {
          if (deletedEntryIds.has(entryId)) continue;

          const entry = entries.find(e => e.id === entryId);
          if (!entry) continue;

          const newAlias = editedAliases[entryId];
          const newCategory = editedCategories[entryId];
          const aliasChanged = newAlias !== undefined && newAlias !== entry.alias && newAlias.trim();
          const categoryChanged = newCategory !== undefined && newCategory !== entry.category;

          if (aliasChanged || categoryChanged) {
            aliasChanges.push({
              originalTerm: entry.originalText,
              category: entry.category,
              newAlias: newAlias?.trim() || entry.alias,
              newCategory: categoryChanged ? newCategory : undefined,
            });
          }
        }

        if (aliasChanges.length > 0 || deletions.length > 0) {
          await onSaveChanges(aliasChanges, deletions);
          totalChanges += aliasChanges.length + deletions.length;
        }
      }

      // Save original text changes (corrections to detected text boundaries)
      if (hasOriginalTextChanges && onSaveOriginalTextChanges) {
        const textChanges: OriginalTextChange[] = [];
        for (const [entryId, newText] of Object.entries(editedOriginalTexts)) {
          if (deletedEntryIds.has(entryId)) continue;

          const entry = entries.find(e => e.id === entryId);
          if (entry && newText !== entry.originalText && newText.trim()) {
            textChanges.push({
              entryId: entry.id,
              oldOriginalText: entry.originalText,
              newOriginalText: newText.trim(),
              category: entry.category,
              alias: entry.alias,
            });
          }
        }
        if (textChanges.length > 0) {
          await onSaveOriginalTextChanges(textChanges);
          totalChanges += textChanges.length;
        }
      }

      setSaveMessage({
        type: 'success',
        text: `${totalChanges} cambio${totalChanges !== 1 ? 's' : ''} guardado${totalChanges !== 1 ? 's' : ''} correctamente`,
      });
      // Clear edited state after successful save
      setEditedAliases({});
      setEditedCategories({});
      setEditedOriginalTexts({});
      setDeletedEntryIds(new Set());
    } catch (error) {
      setSaveMessage({
        type: 'error',
        text: error instanceof Error ? error.message : 'Error al guardar los cambios',
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleDiscardChanges = () => {
    setEditedAliases({});
    setEditedCategories({});
    setEditedOriginalTexts({});
    setDeletedEntryIds(new Set());
    setSaveMessage(null);
  };

  const getDisplayAlias = (entry: GlossaryEntry): string => {
    return editedAliases[entry.id] ?? entry.alias;
  };

  const getDisplayCategory = (entry: GlossaryEntry): string => {
    // Normalize to lowercase to match PII_CATEGORY_LABELS keys
    const category = editedCategories[entry.id] ?? entry.category;
    return category.toLowerCase();
  };

  const getDisplayOriginalText = (entry: GlossaryEntry): string => {
    return editedOriginalTexts[entry.id] ?? entry.originalText;
  };

  const isEntryModified = (entry: GlossaryEntry): boolean => {
    const aliasModified = entry.id in editedAliases && editedAliases[entry.id] !== entry.alias;
    const categoryModified = entry.id in editedCategories &&
      editedCategories[entry.id].toLowerCase() !== entry.category.toLowerCase();
    const textModified = entry.id in editedOriginalTexts && editedOriginalTexts[entry.id] !== entry.originalText;
    return aliasModified || categoryModified || textModified;
  };

  const isCategoryModified = (entry: GlossaryEntry): boolean => {
    if (!(entry.id in editedCategories)) return false;
    // Compare normalized (lowercase) values
    return editedCategories[entry.id].toLowerCase() !== entry.category.toLowerCase();
  };

  const isEntryDeleted = (entry: GlossaryEntry): boolean => {
    return deletedEntryIds.has(entry.id);
  };

  const isOriginalTextModified = (entry: GlossaryEntry): boolean => {
    return entry.id in editedOriginalTexts && editedOriginalTexts[entry.id] !== entry.originalText;
  };

  const filteredAndSorted = useMemo(() => {
    let result = [...entries];

    // Filter (with null safety)
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (entry) =>
          (entry.originalText || '').toLowerCase().includes(query) ||
          (entry.alias || '').toLowerCase().includes(query) ||
          (PII_CATEGORY_LABELS[entry.category] || '').toLowerCase().includes(query)
      );
    }

    // Sort (with null safety)
    result.sort((a, b) => {
      let comparison = 0;
      switch (sortKey) {
        case 'entity':
          comparison = (a.originalText || '').localeCompare(b.originalText || '');
          break;
        case 'alias':
          comparison = (a.alias || '').localeCompare(b.alias || '');
          break;
        case 'category':
          comparison = (PII_CATEGORY_LABELS[a.category] || '').localeCompare(
            PII_CATEGORY_LABELS[b.category] || ''
          );
          break;
        case 'count':
          comparison = (a.occurrenceCount || 0) - (b.occurrenceCount || 0);
          break;
      }
      return sortDirection === 'asc' ? comparison : -comparison;
    });

    return result;
  }, [entries, searchQuery, sortKey, sortDirection]);

  const SortIcon: React.FC<{ active: boolean; direction: SortDirection }> = ({
    active,
    direction,
  }) => (
    <svg
      className={clsx('w-4 h-4 ml-1 inline', {
        'text-primary-500': active,
        'text-gray-400': !active,
      })}
      fill="currentColor"
      viewBox="0 0 20 20"
    >
      {direction === 'asc' || !active ? (
        <path
          fillRule="evenodd"
          d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
          clipRule="evenodd"
        />
      ) : (
        <path
          fillRule="evenodd"
          d="M14.707 12.707a1 1 0 01-1.414 0L10 9.414l-3.293 3.293a1 1 0 01-1.414-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 010 1.414z"
          clipRule="evenodd"
        />
      )}
    </svg>
  );

  // Reusable action buttons component
  const ActionButtons: React.FC = () => (
    <div className="flex gap-2">
      <button
        onClick={handleDiscardChanges}
        disabled={isSaving}
        className={clsx(
          'px-4 py-2 text-sm font-medium rounded-lg',
          'border border-gray-300 dark:border-gray-600',
          'text-gray-700 dark:text-gray-300',
          'hover:bg-gray-50 dark:hover:bg-gray-700',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          'transition-colors'
        )}
      >
        Descartar
      </button>
      <button
        onClick={handleSaveChanges}
        disabled={isSaving}
        className={clsx(
          'px-4 py-2 text-sm font-medium rounded-lg',
          'bg-primary-600 text-white',
          'hover:bg-primary-700',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          'transition-colors',
          'flex items-center gap-2'
        )}
      >
        {isSaving ? (
          <>
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Guardando...
          </>
        ) : (
          'Guardar Cambios'
        )}
      </button>
    </div>
  );

  return (
    <div className={clsx(isIndustrial ? 'flex flex-col h-full' : 'space-y-4', className)}>
      {/* Header with Search and Actions */}
      <div className={clsx(
        'flex gap-2 items-center justify-between',
        isIndustrial ? 'p-2 border-b border-border' : 'flex-col sm:flex-row gap-4 items-start sm:items-center'
      )}>
        {/* Search */}
        <div className={clsx('relative', isIndustrial ? 'flex-1' : 'flex-1 max-w-md')}>
          <input
            type="search"
            placeholder={isIndustrial ? 'BUSCAR...' : 'Buscar en glosario...'}
            value={searchQuery}
            onChange={handleSearchChange}
            className={clsx(
              'w-full pl-8 pr-3 py-1.5',
              isIndustrial
                ? 'text-[11px] uppercase tracking-wide font-industrial bg-input border border-border text-foreground placeholder:text-muted-foreground/50'
                : 'text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400',
              'focus:outline-none focus:ring-1 focus:ring-primary'
            )}
          />
          <svg
            className={clsx('absolute left-2 top-1/2 -translate-y-1/2', isIndustrial ? 'w-4 h-4' : 'w-5 h-5', 'text-muted-foreground')}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>

        {/* Action Buttons (top) */}
        {editable && hasChanges && <ActionButtons />}
      </div>

      {/* Save Message */}
      {saveMessage && (
        <div
          className={clsx(
            'px-4 py-3 rounded-lg text-sm',
            saveMessage.type === 'success'
              ? 'bg-green-50 text-green-800 dark:bg-green-900/20 dark:text-green-400'
              : 'bg-red-50 text-red-800 dark:bg-red-900/20 dark:text-red-400'
          )}
        >
          {saveMessage.text}
        </div>
      )}

      {/* Mobile: Simple List View */}
      {isMobile ? (
        <div className="flex-1 overflow-y-auto">
          {filteredAndSorted.length === 0 ? (
            <div className="p-4 text-center text-sm text-gray-500 dark:text-gray-400">
              {searchQuery ? 'No se encontraron resultados' : 'No hay entradas en el glosario'}
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredAndSorted.map((entry) => (
                <button
                  key={entry.id}
                  onClick={() => onSelectEntry?.(entry)}
                  className={clsx(
                    'w-full flex items-center justify-between p-3 text-left transition-colors',
                    'hover:bg-gray-50 dark:hover:bg-gray-800 active:bg-gray-100 dark:active:bg-gray-700',
                    isEntryDeleted(entry) && 'opacity-50 bg-red-50 dark:bg-red-900/10',
                    isEntryModified(entry) && !isEntryDeleted(entry) && 'bg-yellow-50 dark:bg-yellow-900/10'
                  )}
                >
                  <div className="flex-1 min-w-0 mr-2">
                    <p className={clsx(
                      'text-sm font-medium text-gray-900 dark:text-white truncate',
                      isEntryDeleted(entry) && 'line-through'
                    )}>
                      {entry.originalText}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                      <span className="inline-block px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-[10px] uppercase">
                        {CATEGORY_ABBREV[entry.category.toLowerCase()] || entry.category.slice(0, 4).toUpperCase()}
                      </span>
                      <span className="ml-2 text-primary-600 dark:text-primary-400 font-mono">
                        → {entry.alias}
                      </span>
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400 dark:text-gray-500 font-mono">
                      [{entry.occurrenceCount}]
                    </span>
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      ) : (
      /* Desktop: Table */
      <div className={clsx('overflow-x-auto', isIndustrial && 'flex-1')}>
        <table className={clsx(isIndustrial ? 'table-industrial' : 'min-w-full divide-y divide-gray-200 dark:divide-gray-700')}>
          <thead className={clsx(isIndustrial ? '' : 'bg-gray-50 dark:bg-gray-800')}>
            <tr>
              <th
                scope="col"
                className={clsx(
                  isIndustrial
                    ? 'cursor-pointer hover:bg-muted/70'
                    : 'px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700'
                )}
                onClick={() => handleSort('entity')}
              >
                {isIndustrial ? 'ORIGINAL' : 'Texto Original'}
                <SortIcon
                  active={sortKey === 'entity'}
                  direction={sortDirection}
                />
              </th>
              <th
                scope="col"
                className={clsx(
                  isIndustrial
                    ? 'cursor-pointer hover:bg-muted/70'
                    : 'px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700'
                )}
                onClick={() => handleSort('alias')}
              >
                ALIAS
                {isMaskingLevel && <span className="text-muted-foreground ml-1" title="Nivel BASIC: masking irreversible">🔒</span>}
                <SortIcon
                  active={sortKey === 'alias'}
                  direction={sortDirection}
                />
              </th>
              <th
                scope="col"
                className={clsx(
                  isIndustrial
                    ? 'cursor-pointer hover:bg-muted/70 w-16'
                    : 'px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700'
                )}
                onClick={() => handleSort('category')}
              >
                CAT
                <SortIcon
                  active={sortKey === 'category'}
                  direction={sortDirection}
                />
              </th>
              <th
                scope="col"
                className={clsx(
                  isIndustrial
                    ? 'cursor-pointer hover:bg-muted/70 text-right w-12'
                    : 'px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700'
                )}
                onClick={() => handleSort('count')}
              >
                #
                <SortIcon
                  active={sortKey === 'count'}
                  direction={sortDirection}
                />
              </th>
              {/* Find in text column header */}
              {onFindInText && (
                <th scope="col" className={clsx(isIndustrial ? 'w-8' : 'px-2 py-3 w-10')}></th>
              )}
            </tr>
          </thead>
          <tbody className={clsx(isIndustrial ? '' : 'bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700')}>
            {filteredAndSorted.length === 0 ? (
              <tr>
                <td
                  colSpan={onFindInText ? 5 : 4}
                  className="px-4 py-8 text-center text-sm text-gray-500 dark:text-gray-400"
                >
                  {searchQuery
                    ? 'No se encontraron resultados'
                    : 'No hay entradas en el glosario'}
                </td>
              </tr>
            ) : (
              filteredAndSorted.map((entry) => (
                <tr
                  key={entry.id}
                  className={clsx(
                    'hover:bg-gray-50 dark:hover:bg-gray-800',
                    isEntryDeleted(entry)
                      ? 'bg-red-50 dark:bg-red-900/10 opacity-70'
                      : isEntryModified(entry) && 'bg-yellow-50 dark:bg-yellow-900/10'
                  )}
                >
                  <td className={clsx(isIndustrial ? 'text-foreground' : 'px-4 py-3 text-sm font-medium text-gray-900 dark:text-white')}>
                    <div className="flex items-center gap-2">
                      <span className={clsx(
                        (isOriginalTextModified(entry) || isEntryDeleted(entry)) && 'line-through text-gray-400'
                      )}>
                        {entry.originalText}
                      </span>
                      {isOriginalTextModified(entry) && !isEntryDeleted(entry) && (
                        <span className="text-green-600 dark:text-green-400 font-medium">
                          → {getDisplayOriginalText(entry)}
                        </span>
                      )}

                      {/* Edit Button */}
                      {editable && onSaveOriginalTextChanges && !isEntryDeleted(entry) && (
                        <button
                          onClick={() => handleOpenEditModal(entry)}
                          className="ml-auto p-1 text-gray-400 hover:text-primary-500 rounded"
                          title="Editar texto original (corregir límites)"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                          </svg>
                        </button>
                      )}

                      {/* Restore Button (if deleted) */}
                      {editable && isEntryDeleted(entry) && (
                        <button
                          onClick={() => toggleDelete(entry.id)}
                          className="ml-auto p-1 text-gray-400 hover:text-green-500 rounded"
                          title="Restaurar (cancelar eliminación)"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </td>
                  <td className={clsx(isIndustrial ? '' : 'px-4 py-3')}>
                    {aliasEditable && !isEntryDeleted(entry) ? (
                      <input
                        type="text"
                        value={getDisplayAlias(entry)}
                        onChange={(e) => handleAliasChange(entry.id, e.target.value)}
                        className={clsx(
                          'w-full px-1 py-0.5',
                          isIndustrial ? 'text-primary' : 'text-sm font-mono text-primary-600 dark:text-primary-400 rounded',
                          'border',
                          isEntryModified(entry)
                            ? isIndustrial ? 'border-warning bg-warning/10' : 'border-yellow-400 bg-yellow-50 dark:bg-yellow-900/20'
                            : isIndustrial ? 'border-border bg-input' : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800',
                          isIndustrial ? 'focus:outline-none focus:ring-1 focus:ring-primary' : 'focus:outline-none focus:ring-2 focus:ring-primary-500'
                        )}
                      />
                    ) : (
                      <span className={clsx(
                        isIndustrial ? 'text-primary' : 'text-sm font-mono text-primary-600 dark:text-primary-400',
                        isEntryDeleted(entry) && "line-through opacity-50"
                      )}>
                        {entry.alias}
                        {isMaskingLevel && (
                          <span className="ml-1 text-xs text-muted-foreground" title="Nivel BASIC: el alias no es editable (masking irreversible)">
                            🔒
                          </span>
                        )}
                      </span>
                    )}
                  </td>
                  <td className={clsx(isIndustrial ? '' : 'px-4 py-3')}>
                    {editable && !isEntryDeleted(entry) ? (
                      isIndustrial ? (
                        <select
                          value={getDisplayCategory(entry)}
                          onChange={(e) => handleCategoryChange(entry.id, e.target.value)}
                          className={clsx(
                            'w-full px-1 py-0.5 text-[10px] uppercase tracking-wide',
                            'border bg-input',
                            isCategoryModified(entry)
                              ? 'border-warning bg-warning/10'
                              : 'border-border',
                            'text-foreground',
                            'focus:outline-none focus:ring-1 focus:ring-primary'
                          )}
                        >
                          {ALL_CATEGORIES.map((cat) => (
                            <option key={cat.value} value={cat.value}>
                              {CATEGORY_ABBREV[cat.value.toLowerCase()] || cat.value.slice(0, 4).toUpperCase()}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <select
                          value={getDisplayCategory(entry)}
                          onChange={(e) => handleCategoryChange(entry.id, e.target.value)}
                          className={clsx(
                            'px-2 py-1 text-sm rounded',
                            'border',
                            isCategoryModified(entry)
                              ? 'border-yellow-400 bg-yellow-50 dark:bg-yellow-900/20'
                              : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800',
                            'text-gray-900 dark:text-white',
                            'focus:outline-none focus:ring-2 focus:ring-primary-500'
                          )}
                        >
                          {ALL_CATEGORIES.map((cat) => (
                            <option key={cat.value} value={cat.value}>
                              {cat.label}
                            </option>
                          ))}
                        </select>
                      )
                    ) : (
                      <div className={clsx(isEntryDeleted(entry) && "opacity-50")}>
                        {isIndustrial ? (
                          <span className="cat-abbrev">
                            {CATEGORY_ABBREV[entry.category.toLowerCase()] || entry.category.slice(0, 4).toUpperCase()}
                          </span>
                        ) : (
                          <CategoryChip category={entry.category} />
                        )}
                      </div>
                    )}
                  </td>
                  <td className={clsx(isIndustrial ? 'text-right text-muted-foreground' : 'px-4 py-3 text-sm text-right text-gray-500 dark:text-gray-400')}>
                    <span className={clsx(isEntryDeleted(entry) && "line-through opacity-50")}>
                      {entry.occurrenceCount}
                    </span>
                  </td>
                  {/* Find in text button */}
                  {onFindInText && (
                    <td className="px-2 py-3">
                      <button
                        onClick={() => onFindInText(entry)}
                        className="p-1.5 text-gray-400 hover:text-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/20 rounded transition-colors"
                        title="Buscar en el texto"
                      >
                        👁️
                      </button>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      )}

      {/* Summary and Bottom Action Buttons - hidden on mobile */}
      {!isMobile && (
      <div className={clsx(
        'flex justify-between items-center gap-2',
        isIndustrial ? 'p-2 border-t border-border text-[10px] uppercase tracking-wide' : 'flex-col sm:flex-row items-start sm:items-center gap-3'
      )}>
        <div className={clsx('flex items-center gap-4', isIndustrial ? 'text-muted-foreground' : 'text-xs text-gray-500 dark:text-gray-400')}>
          <span>{isIndustrial ? `Total: ${filteredAndSorted.length}` : `${filteredAndSorted.length} de ${entries.length} entradas`}</span>
          {hasChanges && (
            <span className="text-yellow-600 dark:text-yellow-400">
              {[
                ...Object.keys(editedAliases).filter(id => {
                  const entry = entries.find(e => e.id === id);
                  return entry && editedAliases[id] !== entry.alias && !deletedEntryIds.has(id);
                }),
                ...Object.keys(editedCategories).filter(id => {
                  const entry = entries.find(e => e.id === id);
                  return entry && editedCategories[id].toLowerCase() !== entry.category.toLowerCase() && !deletedEntryIds.has(id);
                }),
                ...Object.keys(editedOriginalTexts).filter(id => {
                  const entry = entries.find(e => e.id === id);
                  return entry && editedOriginalTexts[id] !== entry.originalText && !deletedEntryIds.has(id);
                }),
                ...Array.from(deletedEntryIds)
              ].filter((v, i, a) => a.indexOf(v) === i).length} cambio(s) pendiente(s)
            </span>
          )}
        </div>
        {/* Action Buttons (bottom) */}
        {editable && hasChanges && <ActionButtons />}
      </div>
      )}

      {/* Edit Original Text Modal */}
      {editModalEntry && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Corregir texto detectado
            </h3>

            {/* Context display - shows surrounding text */}
            {(() => {
              const context = originalDocumentText
                ? getTextContext(originalDocumentText, editModalEntry.originalText, 5)
                : null;

              return (
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    Contexto en el documento
                  </label>
                  <div className="p-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-sm font-mono leading-relaxed">
                    {context ? (
                      <>
                        <span className="text-gray-500 dark:text-gray-400">{context.before}</span>
                        <mark className="bg-yellow-200 dark:bg-yellow-700 px-1 rounded font-semibold text-gray-900 dark:text-white">
                          {context.term}
                        </mark>
                        <span className="text-gray-500 dark:text-gray-400">{context.after}</span>
                      </>
                    ) : (
                      <span className="text-gray-800 dark:text-gray-200">{editModalEntry.originalText}</span>
                    )}
                  </div>
                </div>
              );
            })()}

            {/* Alias (read only) */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Alias asignado
              </label>
              <div className="p-3 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm font-mono text-primary-600 dark:text-primary-400">
                {editModalEntry.alias}
              </div>
            </div>

            {/* Editable text */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Ajustar límites de detección
              </label>
              <input
                type="text"
                value={editModalText}
                onChange={(e) => setEditModalText(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono focus:ring-2 focus:ring-primary-500"
                placeholder="Ajusta el texto que debe anonimizarse"
              />
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Puedes añadir o quitar palabras del contexto para ajustar los límites
              </p>
            </div>

            {/* Preview of change */}
            {editModalText.trim() !== editModalEntry.originalText && editModalText.trim() && (
              <div className="mb-6 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                <p className="text-sm font-medium text-yellow-800 dark:text-yellow-300 mb-1">Vista previa del cambio:</p>
                <p className="text-sm text-yellow-700 dark:text-yellow-400">
                  <span className="line-through">{editModalEntry.originalText}</span>
                  {' → '}
                  <span className="font-medium">{editModalText.trim()}</span>
                </p>
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-between gap-3">
              {/* Delete button on the left */}
              <button
                onClick={() => {
                  toggleDelete(editModalEntry.id);
                  setEditModalEntry(null);
                  setEditModalText('');
                }}
                className="px-4 py-2 text-sm font-medium text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 border border-red-300 dark:border-red-700 rounded-lg flex items-center gap-2"
                title="Eliminar esta anonimización (el texto original se restaurará)"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Eliminar anonimización
              </button>

              {/* Cancel and Apply buttons on the right */}
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setEditModalEntry(null);
                    setEditModalText('');
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleSaveEditModal}
                  disabled={!editModalText.trim() || editModalText.trim() === editModalEntry.originalText}
                  className="px-4 py-2 text-sm font-medium text-white bg-primary-500 hover:bg-primary-600 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Aplicar corrección
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GlossaryTable;
