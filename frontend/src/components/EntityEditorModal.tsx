/**
 * EntityEditorModal - Unified entity editing modal for mobile
 *
 * All-in-one editor that combines:
 * - Context view (surrounding text)
 * - Category selection
 * - Visual boundary selector (expand/reduce detection limits)
 * - Alias editing
 * - Delete action
 *
 * @generated for mobile-specific UI
 */

import React, { useState, useMemo, useCallback, useEffect } from 'react';
import clsx from 'clsx';
import type { GlossaryEntry } from '@/types';
import { PII_CATEGORY_LABELS } from '@/types';

interface EntityEditorModalProps {
  entry: GlossaryEntry | null;
  isOpen: boolean;
  onClose: () => void;
  onSave: (changes: {
    entryId: string;
    alias?: string;
    category?: string;
    originalText?: string;
  }) => Promise<void>;
  onDelete: (entryId: string) => void;
  originalDocumentText?: string;
  anonymizationLevel?: 'basic' | 'intermediate' | 'advanced';
}

// Category options
const ALL_CATEGORIES = Object.entries(PII_CATEGORY_LABELS).map(([value, label]) => ({
  value,
  label,
}));

// Extract words around the term for boundary adjustment
function getContextWords(
  fullText: string,
  term: string,
  wordsBefore: number = 5,
  wordsAfter: number = 5
): { before: string[]; term: string; after: string[]; termIndex: number } | null {
  if (!fullText || !term) return null;

  const lowerText = fullText.toLowerCase();
  const lowerTerm = term.toLowerCase();
  const termIndex = lowerText.indexOf(lowerTerm);

  if (termIndex === -1) return null;

  const textBefore = fullText.slice(0, termIndex);
  const actualTerm = fullText.slice(termIndex, termIndex + term.length);
  const textAfter = fullText.slice(termIndex + term.length);

  const beforeWords = textBefore.trim().split(/\s+/).filter(w => w);
  const afterWords = textAfter.trim().split(/\s+/).filter(w => w);

  return {
    before: beforeWords.slice(-wordsBefore),
    term: actualTerm,
    after: afterWords.slice(0, wordsAfter),
    termIndex,
  };
}

export const EntityEditorModal: React.FC<EntityEditorModalProps> = ({
  entry,
  isOpen,
  onClose,
  onSave,
  onDelete,
  originalDocumentText,
  anonymizationLevel = 'intermediate',
}) => {
  const isMaskingLevel = anonymizationLevel === 'basic';

  // Editable state
  const [editedAlias, setEditedAlias] = useState('');
  const [editedCategory, setEditedCategory] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  // Boundary adjustment offsets
  const [startOffset, setStartOffset] = useState(0); // negative = expand left, positive = reduce left
  const [endOffset, setEndOffset] = useState(0); // positive = expand right, negative = reduce right

  // Context words
  const contextData = useMemo(() => {
    if (!entry || !originalDocumentText) return null;
    return getContextWords(originalDocumentText, entry.originalText, 5, 5);
  }, [entry, originalDocumentText]);

  // Reset state when entry changes
  useEffect(() => {
    if (entry) {
      setEditedAlias(entry.alias);
      setEditedCategory(entry.category.toLowerCase());
      setStartOffset(0);
      setEndOffset(0);
    }
  }, [entry]);

  // Calculate adjusted text based on offsets
  const adjustedText = useMemo(() => {
    if (!contextData || !entry) return entry?.originalText || '';

    const { before, term, after } = contextData;

    // Calculate which words to include
    let result = term;

    // Expand/reduce left boundary
    if (startOffset < 0) {
      // Expand left: add words from before
      const wordsToAdd = before.slice(startOffset);
      result = wordsToAdd.join(' ') + ' ' + result;
    } else if (startOffset > 0) {
      // Reduce left: remove words from start of term
      const termWords = term.split(/\s+/);
      result = termWords.slice(startOffset).join(' ');
    }

    // Expand/reduce right boundary
    if (endOffset > 0) {
      // Expand right: add words from after
      const wordsToAdd = after.slice(0, endOffset);
      result = result + ' ' + wordsToAdd.join(' ');
    } else if (endOffset < 0) {
      // Reduce right: remove words from end of result
      const resultWords = result.split(/\s+/);
      result = resultWords.slice(0, resultWords.length + endOffset).join(' ');
    }

    return result.trim();
  }, [contextData, entry, startOffset, endOffset]);

  // Check if there are changes
  const hasChanges = useMemo(() => {
    if (!entry) return false;
    return (
      editedAlias !== entry.alias ||
      editedCategory !== entry.category.toLowerCase() ||
      adjustedText !== entry.originalText
    );
  }, [entry, editedAlias, editedCategory, adjustedText]);

  // Handle save
  const handleSave = useCallback(async () => {
    if (!entry || !hasChanges) return;

    setIsSaving(true);
    try {
      await onSave({
        entryId: entry.id,
        alias: editedAlias !== entry.alias ? editedAlias : undefined,
        category: editedCategory !== entry.category.toLowerCase() ? editedCategory : undefined,
        originalText: adjustedText !== entry.originalText ? adjustedText : undefined,
      });
      onClose();
    } catch (error) {
      // Error handling done by parent
    } finally {
      setIsSaving(false);
    }
  }, [entry, hasChanges, editedAlias, editedCategory, adjustedText, onSave, onClose]);

  // Handle delete
  const handleDelete = useCallback(() => {
    if (!entry) return;
    if (confirm('¿Eliminar esta anonimización? El texto original se restaurará.')) {
      onDelete(entry.id);
      onClose();
    }
  }, [entry, onDelete, onClose]);

  if (!isOpen || !entry) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/50">
      <div className="bg-white dark:bg-gray-800 w-full sm:max-w-lg sm:mx-4 sm:rounded-lg rounded-t-2xl shadow-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-4 py-3 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Editar Entidad
          </h3>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-4 space-y-5">
          {/* 1. Context View */}
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
              1. Contexto
            </label>
            <div className="p-3 bg-gray-900 dark:bg-gray-950 rounded-lg font-mono text-sm leading-relaxed overflow-x-auto">
              {contextData ? (
                <>
                  <span className="text-gray-500">{contextData.before.join(' ')} </span>
                  <mark className="bg-yellow-400 text-gray-900 px-1 rounded font-semibold">
                    {adjustedText}
                  </mark>
                  <span className="text-gray-500"> {contextData.after.join(' ')}</span>
                </>
              ) : (
                <span className="text-gray-300">{entry.originalText}</span>
              )}
            </div>
          </div>

          {/* 2. Category Selection */}
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
              2. Categoría
            </label>
            <select
              value={editedCategory}
              onChange={(e) => setEditedCategory(e.target.value)}
              className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              {ALL_CATEGORIES.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>

          {/* 3. Boundary Selector */}
          {contextData && (
            <div>
              <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
                3. Ajustar límites de detección
              </label>
              <div className="bg-gray-50 dark:bg-gray-900 rounded-lg p-3 space-y-3">
                {/* Visual representation */}
                <div className="flex items-center justify-center gap-1 text-xs overflow-x-auto py-2">
                  {contextData.before.slice(-3).map((word, i) => (
                    <span
                      key={`before-${i}`}
                      className={clsx(
                        'px-1.5 py-1 rounded transition-colors',
                        startOffset < 0 && i >= contextData.before.slice(-3).length + startOffset
                          ? 'bg-yellow-200 dark:bg-yellow-700 text-gray-900 dark:text-white'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-500'
                      )}
                    >
                      {word}
                    </span>
                  ))}
                  <span className="px-2 py-1 bg-yellow-400 text-gray-900 rounded font-semibold">
                    {entry.originalText.split(/\s+/).slice(
                      Math.max(0, startOffset),
                      entry.originalText.split(/\s+/).length + Math.min(0, endOffset) || undefined
                    ).join(' ') || entry.originalText}
                  </span>
                  {contextData.after.slice(0, 3).map((word, i) => (
                    <span
                      key={`after-${i}`}
                      className={clsx(
                        'px-1.5 py-1 rounded transition-colors',
                        endOffset > 0 && i < endOffset
                          ? 'bg-yellow-200 dark:bg-yellow-700 text-gray-900 dark:text-white'
                          : 'bg-gray-200 dark:bg-gray-700 text-gray-500'
                      )}
                    >
                      {word}
                    </span>
                  ))}
                </div>

                {/* Control buttons */}
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => setStartOffset(prev => Math.max(prev - 1, -contextData.before.length))}
                    disabled={startOffset <= -contextData.before.length}
                    className="flex items-center justify-center gap-1 px-3 py-2 text-xs font-medium border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                    Expandir izq.
                  </button>
                  <button
                    onClick={() => setEndOffset(prev => Math.min(prev + 1, contextData.after.length))}
                    disabled={endOffset >= contextData.after.length}
                    className="flex items-center justify-center gap-1 px-3 py-2 text-xs font-medium border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Expandir der.
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                  <button
                    onClick={() => setStartOffset(prev => Math.min(prev + 1, entry.originalText.split(/\s+/).length - 1))}
                    disabled={startOffset >= entry.originalText.split(/\s+/).length - 1}
                    className="flex items-center justify-center gap-1 px-3 py-2 text-xs font-medium border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                    Reducir izq.
                  </button>
                  <button
                    onClick={() => setEndOffset(prev => Math.max(prev - 1, -(entry.originalText.split(/\s+/).length - 1)))}
                    disabled={endOffset <= -(entry.originalText.split(/\s+/).length - 1)}
                    className="flex items-center justify-center gap-1 px-3 py-2 text-xs font-medium border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Reducir der.
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                  </button>
                </div>

                {/* Reset button */}
                {(startOffset !== 0 || endOffset !== 0) && (
                  <button
                    onClick={() => { setStartOffset(0); setEndOffset(0); }}
                    className="w-full text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 py-1"
                  >
                    Restablecer límites originales
                  </button>
                )}

                {/* Result preview */}
                {adjustedText !== entry.originalText && (
                  <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
                    <p className="text-xs text-gray-500 mb-1">Resultado:</p>
                    <p className="text-sm font-mono">
                      <span className="line-through text-gray-400">{entry.originalText}</span>
                      <span className="mx-2">→</span>
                      <span className="text-green-600 dark:text-green-400 font-semibold">{adjustedText}</span>
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* 4. Alias */}
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
              4. Alias asignado
            </label>
            {isMaskingLevel ? (
              <div className="p-3 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm font-mono text-gray-600 dark:text-gray-400">
                {entry.alias}
                <span className="ml-2 text-xs">🔒 (masking irreversible)</span>
              </div>
            ) : (
              <input
                type="text"
                value={editedAlias}
                onChange={(e) => setEditedAlias(e.target.value)}
                className="w-full px-3 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white font-mono focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder="Ej: Persona_001"
              />
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="sticky bottom-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-4 py-3 flex items-center justify-between gap-3">
          <button
            onClick={handleDelete}
            className="p-2.5 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
            title="Eliminar anonimización"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>

          <div className="flex gap-2">
            <button
              onClick={onClose}
              disabled={isSaving}
              className="px-4 py-2.5 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={handleSave}
              disabled={isSaving || !hasChanges}
              className={clsx(
                'px-6 py-2.5 text-sm font-medium text-white rounded-lg transition-colors',
                'bg-primary-500 hover:bg-primary-600 active:bg-primary-700',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'flex items-center gap-2'
              )}
            >
              {isSaving ? (
                <>
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Guardando...
                </>
              ) : (
                'Guardar Cambios'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EntityEditorModal;
