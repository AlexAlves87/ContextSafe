/**
 * AnonymizedPreview - Before/after comparison of anonymized document
 *
 * Shows original and anonymized text side by side with highlighted changes.
 * Supports manual anonymization of selected text.
 *
 * Traceability:
 * - Contract: CNT-UI-COMP-005
 * - Binding: UI-BIND-005
 *
 * @modified Highlight only changed words, neutral background
 */

import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react';
import clsx from 'clsx';
import type { GlossaryEntry } from '@/types';
import { useIsMobile } from '@/hooks';

// PII Categories for manual selection
const PII_CATEGORIES = [
  { value: 'PERSON_NAME', label: 'Nombre de persona' },
  { value: 'DNI', label: 'DNI / NIF' },
  { value: 'EMAIL', label: 'Email' },
  { value: 'PHONE', label: 'Teléfono' },
  { value: 'ADDRESS', label: 'Dirección' },
  { value: 'LOCATION', label: 'Ubicación' },
  { value: 'ORGANIZATION', label: 'Organización' },
  { value: 'DATE', label: 'Fecha' },
  { value: 'PROFESSIONAL_ID', label: 'ID Profesional (colegiado, etc.)' },
  { value: 'IBAN', label: 'IBAN / Cuenta bancaria' },
  { value: 'OTHER', label: 'Otro' },
];

// Category highlight classes - defined in index.css with proper dark mode support
const CATEGORY_HIGHLIGHT_COLORS: Record<string, string> = {
  person_name: 'entity-highlight entity-highlight-person',
  organization: 'entity-highlight entity-highlight-organization',
  location: 'entity-highlight entity-highlight-location',
  address: 'entity-highlight entity-highlight-address',
  dni: 'entity-highlight entity-highlight-dni',
  nie: 'entity-highlight entity-highlight-nie',
  dni_nie: 'entity-highlight entity-highlight-dni_nie',
  phone: 'entity-highlight entity-highlight-phone',
  email: 'entity-highlight entity-highlight-email',
  iban: 'entity-highlight entity-highlight-iban',
  date: 'entity-highlight entity-highlight-date',
  professional_id: 'entity-highlight entity-highlight-professional_id',
  other: 'entity-highlight entity-highlight-other',
};

interface AnonymizedPreviewProps {
  originalText: string;
  anonymizedText: string;
  glossary?: GlossaryEntry[];
  viewMode?: 'split';
  className?: string;
  onManualAnonymize?: (text: string, category: string, alias?: string) => Promise<void>;
  highlightedTerm?: string | null;
  onClearHighlight?: () => void;
  /** Anonymization level - affects manual anonymization dialog */
  anonymizationLevel?: 'basic' | 'intermediate' | 'advanced';
}

interface SelectionPopupState {
  visible: boolean;
  text: string;
  x: number;
  y: number;
}

interface HighlightedSegment {
  text: string;
  isHighlight: boolean;
  category?: string;
  tooltip?: string;
}

/**
 * Highlight specific terms in text, returning segments for rendering.
 */
function highlightTerms(
  text: string,
  terms: Array<{ term: string; category: string; tooltip?: string }>
): HighlightedSegment[] {
  if (!terms.length || !text) {
    return [{ text, isHighlight: false }];
  }

  // Sort terms by length (longest first) to avoid partial matches
  const sortedTerms = [...terms].sort((a, b) => b.term.length - a.term.length);

  // Build regex pattern with all terms (case insensitive)
  const escapedTerms = sortedTerms.map(t =>
    t.term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  );
  const pattern = new RegExp(`(${escapedTerms.join('|')})`, 'gi');

  const segments: HighlightedSegment[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = pattern.exec(text)) !== null) {
    // Add text before match
    if (match.index > lastIndex) {
      segments.push({
        text: text.slice(lastIndex, match.index),
        isHighlight: false,
      });
    }

    // Find the matching term (case insensitive)
    const matchedText = match[0];
    const termInfo = sortedTerms.find(
      t => t.term.toLowerCase() === matchedText.toLowerCase()
    );

    // Add highlighted match
    segments.push({
      text: matchedText,
      isHighlight: true,
      category: termInfo?.category || 'other',
      tooltip: termInfo?.tooltip,
    });

    lastIndex = pattern.lastIndex;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    segments.push({
      text: text.slice(lastIndex),
      isHighlight: false,
    });
  }

  return segments;
}

export const AnonymizedPreview: React.FC<AnonymizedPreviewProps> = ({
  originalText,
  anonymizedText,
  glossary = [],
  className,
  onManualAnonymize,
  highlightedTerm,
  onClearHighlight,
  anonymizationLevel = 'intermediate',
}) => {
  // BASIC level uses masking (asterisks) - no custom alias allowed
  const isMaskingLevel = anonymizationLevel === 'basic';
  const isMobile = useIsMobile();

  // Mobile: tabs for switching views
  const [mobileTab, setMobileTab] = useState<'original' | 'anonymized'>('original');

  // Desktop: floating popup / Mobile: bottom bar
  const [selectionPopup, setSelectionPopup] = useState<SelectionPopupState>({
    visible: false,
    text: '',
    x: 0,
    y: 0,
  });

  // Mobile bottom bar state
  const [mobileSelection, setMobileSelection] = useState<string>('');

  const [showDialog, setShowDialog] = useState(false);
  const [selectedText, setSelectedText] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('PERSON_NAME');
  const [customAlias, setCustomAlias] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const originalTextRef = useRef<HTMLDivElement>(null);
  const anonymizedTextRef = useRef<HTMLDivElement>(null);
  const popupRef = useRef<HTMLDivElement>(null);
  const isScrolling = useRef(false);

  // State for occurrence navigation
  const [occurrenceNav, setOccurrenceNav] = useState<{
    term: string;
    total: number;
    current: number;
    marks: Element[];
  } | null>(null);

  // Prepare terms for highlighting
  const originalTerms = useMemo(() => {
    return glossary.map(entry => ({
      term: entry.originalText,
      category: entry.category,
      tooltip: `→ ${entry.alias}`,
    }));
  }, [glossary]);

  const anonymizedTerms = useMemo(() => {
    return glossary.map(entry => ({
      term: entry.alias,
      category: entry.category,
      tooltip: `← ${entry.originalText}`,
    }));
  }, [glossary]);

  // Generate highlighted segments
  const originalSegments = useMemo(
    () => highlightTerms(originalText, originalTerms),
    [originalText, originalTerms]
  );

  const anonymizedSegments = useMemo(
    () => highlightTerms(anonymizedText, anonymizedTerms),
    [anonymizedText, anonymizedTerms]
  );

  // Scroll to highlighted term when set from glossary
  useEffect(() => {
    if (!highlightedTerm || !originalTextRef.current) return;

    // Find ALL highlighted mark elements that contain the term
    const allMarks = originalTextRef.current.querySelectorAll('mark');
    const matchingMarks: Element[] = [];

    for (const mark of allMarks) {
      if (mark.textContent?.toLowerCase().includes(highlightedTerm.toLowerCase())) {
        matchingMarks.push(mark);
      }
    }

    if (matchingMarks.length === 0) return;

    // Set occurrence navigation state
    setOccurrenceNav({
      term: highlightedTerm,
      total: matchingMarks.length,
      current: 0,
      marks: matchingMarks,
    });

    // Scroll to first occurrence
    const firstMark = matchingMarks[0];
    firstMark.scrollIntoView({ behavior: 'smooth', block: 'center' });

    // Highlight first occurrence
    firstMark.classList.add('ring-2', 'ring-primary-500', 'ring-offset-2');

  }, [highlightedTerm]);

  // Navigate to specific occurrence
  const navigateToOccurrence = useCallback((index: number) => {
    if (!occurrenceNav || index < 0 || index >= occurrenceNav.total) return;

    // Remove highlight from previous
    occurrenceNav.marks[occurrenceNav.current]?.classList.remove('ring-2', 'ring-primary-500', 'ring-offset-2');

    // Update current index
    setOccurrenceNav(prev => prev ? { ...prev, current: index } : null);

    // Scroll to and highlight new occurrence
    const mark = occurrenceNav.marks[index];
    mark.scrollIntoView({ behavior: 'smooth', block: 'center' });
    mark.classList.add('ring-2', 'ring-primary-500', 'ring-offset-2');
  }, [occurrenceNav]);

  // Close occurrence navigator
  const closeOccurrenceNav = useCallback(() => {
    if (occurrenceNav) {
      // Remove all highlights
      occurrenceNav.marks.forEach(mark => {
        mark.classList.remove('ring-2', 'ring-primary-500', 'ring-offset-2');
      });
    }
    setOccurrenceNav(null);
    onClearHighlight?.();
  }, [occurrenceNav, onClearHighlight]);

  // Synchronized scrolling between panels
  const handleScroll = useCallback((source: 'original' | 'anonymized') => {
    if (isScrolling.current) return;

    isScrolling.current = true;

    const sourceRef = source === 'original' ? originalTextRef : anonymizedTextRef;
    const targetRef = source === 'original' ? anonymizedTextRef : originalTextRef;

    if (sourceRef.current && targetRef.current) {
      const sourceMaxScroll = sourceRef.current.scrollHeight - sourceRef.current.clientHeight;
      const scrollRatio = sourceMaxScroll > 0
        ? sourceRef.current.scrollTop / sourceMaxScroll
        : 0;

      const targetMaxScroll = targetRef.current.scrollHeight - targetRef.current.clientHeight;
      targetRef.current.scrollTop = scrollRatio * targetMaxScroll;
    }

    requestAnimationFrame(() => {
      isScrolling.current = false;
    });
  }, []);

  // Handle text selection in original panel (desktop: mouseup)
  const handleMouseUp = useCallback(() => {
    if (!onManualAnonymize || isMobile) return;

    const selection = window.getSelection();
    const text = selection?.toString().trim();

    if (text && text.length > 0) {
      const range = selection?.getRangeAt(0);
      const rect = range?.getBoundingClientRect();

      if (rect) {
        setSelectionPopup({
          visible: true,
          text,
          x: rect.left + rect.width / 2,
          y: rect.bottom + 8,
        });
      }
    } else {
      setSelectionPopup({ visible: false, text: '', x: 0, y: 0 });
    }
  }, [onManualAnonymize, isMobile]);

  // Mobile: Listen for selectionchange event (works better with touch)
  useEffect(() => {
    if (!isMobile || !onManualAnonymize) return;

    const handleSelectionChange = () => {
      const selection = window.getSelection();
      const text = selection?.toString().trim();

      if (text && text.length > 0) {
        // Check if selection is within original text panel
        const anchorNode = selection?.anchorNode;
        if (anchorNode && originalTextRef.current?.contains(anchorNode)) {
          setMobileSelection(text);
        } else {
          setMobileSelection('');
        }
      } else {
        setMobileSelection('');
      }
    };

    document.addEventListener('selectionchange', handleSelectionChange);
    return () => document.removeEventListener('selectionchange', handleSelectionChange);
  }, [isMobile, onManualAnonymize]);

  // Close popup when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (popupRef.current && !popupRef.current.contains(e.target as Node)) {
        setSelectionPopup({ visible: false, text: '', x: 0, y: 0 });
      }
    };

    if (selectionPopup.visible) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [selectionPopup.visible]);

  // Open anonymization dialog (from popup or mobile bar)
  const handleOpenDialog = useCallback((textToAnonymize?: string) => {
    const text = textToAnonymize || selectionPopup.text || mobileSelection;
    if (!text) return;

    setSelectedText(text);
    setSelectedCategory('PERSON_NAME');
    setCustomAlias('');
    setShowDialog(true);
    setSelectionPopup({ visible: false, text: '', x: 0, y: 0 });
    setMobileSelection('');
    window.getSelection()?.removeAllRanges();
  }, [selectionPopup.text, mobileSelection]);

  // Submit manual anonymization
  const handleSubmit = useCallback(async () => {
    if (!onManualAnonymize || !selectedText) return;

    setIsSubmitting(true);
    try {
      await onManualAnonymize(
        selectedText,
        selectedCategory,
        customAlias || undefined
      );
      setShowDialog(false);
    } catch {
      // Error handling is done by parent component
    } finally {
      setIsSubmitting(false);
    }
  }, [onManualAnonymize, selectedText, selectedCategory, customAlias]);

  // Render text with highlights
  const renderHighlightedText = (segments: HighlightedSegment[]) => {
    return segments.map((segment, index) => {
      if (!segment.isHighlight) {
        return <span key={index}>{segment.text}</span>;
      }

      const colorClass = CATEGORY_HIGHLIGHT_COLORS[segment.category || 'other']
        || CATEGORY_HIGHLIGHT_COLORS.other;

      return (
        <mark
          key={index}
          className={colorClass}
          title={segment.tooltip}
        >
          {segment.text}
        </mark>
      );
    });
  };

  return (
    <div className={clsx('space-y-2 md:space-y-4 relative', isMobile && mobileSelection && 'pb-24', className)}>
      {/* Instructions for manual anonymization - hidden on mobile (tip shown in bottom bar) */}
      {onManualAnonymize && !isMobile && (
        <div className="text-sm text-gray-500 dark:text-gray-400 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg px-3 py-2">
          <span className="font-medium text-blue-700 dark:text-blue-300">Tip:</span> Selecciona texto en el panel "Original" para anonimizarlo manualmente.
        </div>
      )}

      {/* Legend - compact on mobile */}
      {glossary.length > 0 && (
        <div className="flex flex-wrap gap-1 md:gap-2 text-[10px] md:text-xs">
          <span className="text-gray-500 dark:text-gray-400 hidden md:inline">Leyenda:</span>
          <span className="entity-highlight entity-highlight-person">Persona</span>
          <span className="entity-highlight entity-highlight-organization">Org</span>
          <span className="entity-highlight entity-highlight-location">Loc</span>
          <span className="entity-highlight entity-highlight-dni">DNI</span>
          <span className="entity-highlight entity-highlight-phone hidden md:inline">Teléfono</span>
          <span className="entity-highlight entity-highlight-email hidden md:inline">Email</span>
        </div>
      )}

      {/* Mobile: Tabs for switching views */}
      {isMobile && (
        <div className="flex border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setMobileTab('original')}
            className={clsx(
              'flex-1 py-2 text-sm font-medium text-center transition-colors',
              mobileTab === 'original'
                ? 'text-primary-600 border-b-2 border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400'
            )}
          >
            Original
            {onManualAnonymize && <span className="text-[10px] ml-1 opacity-60">(seleccionar)</span>}
          </button>
          <button
            onClick={() => setMobileTab('anonymized')}
            className={clsx(
              'flex-1 py-2 text-sm font-medium text-center transition-colors',
              mobileTab === 'anonymized'
                ? 'text-primary-600 border-b-2 border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400'
            )}
          >
            Anonimizado
          </button>
        </div>
      )}

      {/* Split view - Original vs Anonymized */}
      <div className={clsx('relative', !isMobile && 'grid grid-cols-1 lg:grid-cols-2 gap-2 md:gap-4')}>
        {/* Floating Occurrence Navigation Indicator - centered between panels */}
        {occurrenceNav && occurrenceNav.total > 1 && (
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-30 hidden lg:flex">
            <div className="flex flex-col items-center gap-2 px-3 py-3 bg-primary-500 text-white rounded-lg shadow-xl text-sm font-medium">
              <button
                onClick={() => navigateToOccurrence(occurrenceNav.current - 1)}
                disabled={occurrenceNav.current === 0}
                className="p-1.5 hover:bg-primary-600 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed"
                title="Anterior"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                </svg>
              </button>
              <span className="text-center leading-tight">
                <span className="text-lg font-bold">{occurrenceNav.current + 1}</span>
                <span className="text-xs opacity-80 block">de {occurrenceNav.total}</span>
              </span>
              <button
                onClick={() => navigateToOccurrence(occurrenceNav.current + 1)}
                disabled={occurrenceNav.current === occurrenceNav.total - 1}
                className="p-1.5 hover:bg-primary-600 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed"
                title="Siguiente"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              <button
                onClick={closeOccurrenceNav}
                className="p-1 hover:bg-primary-600 rounded mt-1 opacity-70 hover:opacity-100"
                title="Cerrar"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Mobile: show indicator at top */}
        {occurrenceNav && occurrenceNav.total > 1 && (
          <div className="col-span-1 lg:hidden flex justify-center mb-2">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-full shadow-lg text-sm font-medium">
              <button
                onClick={() => navigateToOccurrence(occurrenceNav.current - 1)}
                disabled={occurrenceNav.current === 0}
                className="p-1 hover:bg-primary-600 rounded disabled:opacity-40 disabled:cursor-not-allowed"
                title="Anterior"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <span>{occurrenceNav.current + 1} de {occurrenceNav.total}</span>
              <button
                onClick={() => navigateToOccurrence(occurrenceNav.current + 1)}
                disabled={occurrenceNav.current === occurrenceNav.total - 1}
                className="p-1 hover:bg-primary-600 rounded disabled:opacity-40 disabled:cursor-not-allowed"
                title="Siguiente"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
              <button
                onClick={closeOccurrenceNav}
                className="p-1 hover:bg-primary-600 rounded ml-1"
                title="Cerrar"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Original - show when desktop OR mobile tab is 'original' */}
        {(!isMobile || mobileTab === 'original') && (
          <div>
            {/* Header hidden on mobile (tabs replace it) */}
            {!isMobile && (
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-gray-400"></span>
                Original
                {onManualAnonymize && (
                  <span className="text-xs text-gray-400">(selecciona para anonimizar)</span>
                )}
              </h4>
            )}
            <div
              ref={originalTextRef}
              onMouseUp={handleMouseUp}
              onScroll={() => handleScroll('original')}
              className={clsx(
                "bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700 overflow-y-auto",
                isMobile ? "p-2 rounded max-h-[50vh]" : "p-4 rounded-lg max-h-[600px]",
                onManualAnonymize && "cursor-text select-text"
              )}
            >
              <div className={clsx(
                "whitespace-pre-wrap font-mono text-gray-800 dark:text-gray-200 leading-relaxed",
                isMobile ? "text-sm" : "text-sm"
              )}>
                {renderHighlightedText(originalSegments)}
              </div>
            </div>
          </div>
        )}

        {/* Anonymized - show when desktop OR mobile tab is 'anonymized' */}
        {(!isMobile || mobileTab === 'anonymized') && (
          <div>
            {/* Header hidden on mobile (tabs replace it) */}
            {!isMobile && (
              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                <span className="w-3 h-3 rounded-full bg-gray-400"></span>
                Anonimizado
              </h4>
            )}
            <div
              ref={anonymizedTextRef}
              onScroll={() => handleScroll('anonymized')}
              className={clsx(
                "bg-gray-50 dark:bg-gray-900/50 border border-gray-200 dark:border-gray-700 overflow-y-auto",
                isMobile ? "p-2 rounded max-h-[50vh]" : "p-4 rounded-lg max-h-[600px]"
              )}
            >
              <div className={clsx(
                "whitespace-pre-wrap font-mono text-gray-800 dark:text-gray-200 leading-relaxed",
                isMobile ? "text-sm" : "text-sm"
              )}>
                {renderHighlightedText(anonymizedSegments)}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Selection Popup - Desktop only */}
      {!isMobile && selectionPopup.visible && (
        <div
          ref={popupRef}
          className="fixed z-50 bg-white dark:bg-gray-800 shadow-lg rounded-lg border border-gray-200 dark:border-gray-700 p-2"
          style={{
            left: selectionPopup.x,
            top: selectionPopup.y,
            transform: 'translateX(-50%)',
          }}
        >
          <button
            onClick={() => handleOpenDialog()}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-white bg-primary-500 hover:bg-primary-600 rounded-md"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
            </svg>
            Anonimizar "{selectionPopup.text.length > 20 ? selectionPopup.text.slice(0, 20) + '...' : selectionPopup.text}"
          </button>
        </div>
      )}

      {/* Mobile Bottom Action Bar */}
      {isMobile && mobileSelection && onManualAnonymize && (
        <div className="fixed bottom-0 left-0 right-0 z-50 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 shadow-2xl p-4 safe-area-pb">
          <div className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
            Texto seleccionado:
          </div>
          <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded text-sm font-mono text-gray-800 dark:text-gray-200 mb-3 max-h-16 overflow-y-auto">
            "{mobileSelection.length > 60 ? mobileSelection.slice(0, 60) + '...' : mobileSelection}"
          </div>
          <button
            onClick={() => handleOpenDialog(mobileSelection)}
            className="w-full flex items-center justify-center gap-2 py-3 text-base font-semibold text-white bg-primary-500 hover:bg-primary-600 active:bg-primary-700 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            ANONIMIZAR SELECCIÓN
          </button>
        </div>
      )}

      {/* Anonymization Dialog */}
      {showDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Anonimizar texto manualmente
            </h3>

            {/* Selected text preview */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Texto seleccionado
              </label>
              <div className="p-3 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm font-mono text-gray-800 dark:text-gray-200">
                {selectedText}
              </div>
            </div>

            {/* Category selection */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Categoría
              </label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500"
              >
                {PII_CATEGORIES.map((cat) => (
                  <option key={cat.value} value={cat.value}>
                    {cat.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Custom alias (optional) - only for INTERMEDIATE/ADVANCED */}
            {isMaskingLevel ? (
              <div className="mb-6 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-lg">
                <p className="text-sm text-amber-800 dark:text-amber-300">
                  <span className="font-medium">Nivel BASIC:</span> El texto seleccionado será reemplazado por asteriscos (<code className="font-mono bg-amber-100 dark:bg-amber-800 px-1 rounded">*****</code>).
                </p>
              </div>
            ) : (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Alias personalizado (opcional)
                </label>
                <input
                  type="text"
                  value={customAlias}
                  onChange={(e) => setCustomAlias(e.target.value)}
                  placeholder="Ej: Colegiado_1, Juez_2"
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500 focus:ring-2 focus:ring-primary-500"
                />
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  Si no especificas uno, se generará automáticamente.
                </p>
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowDialog(false)}
                disabled={isSubmitting}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
              >
                Cancelar
              </button>
              <button
                onClick={handleSubmit}
                disabled={isSubmitting}
                className="px-4 py-2 text-sm font-medium text-white bg-primary-500 hover:bg-primary-600 rounded-lg disabled:opacity-50 flex items-center gap-2"
              >
                {isSubmitting ? (
                  <>
                    <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Guardando...
                  </>
                ) : (
                  'Anonimizar'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnonymizedPreview;
