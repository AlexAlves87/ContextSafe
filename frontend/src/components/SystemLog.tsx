/**
 * SystemLog - Terminal-style log viewer for processing feedback
 *
 * Industrial design: monospace font, dark background, auto-scroll
 * with pause on user scroll.
 *
 * @generated for REFORMA.md implementation
 */

import React, { useRef, useEffect, useState, useCallback } from 'react';
import clsx from 'clsx';

export interface LogEntry {
  id: string;
  timestamp: Date;
  level: 'info' | 'success' | 'warning' | 'error';
  message: string;
}

interface SystemLogProps {
  entries: LogEntry[];
  maxHeight?: number;
  className?: string;
}

const LEVEL_CONFIG: Record<LogEntry['level'], { prefix: string; color: string }> = {
  info: { prefix: '>', color: 'text-gray-300' },
  success: { prefix: '✓', color: 'text-green-400' },
  warning: { prefix: '⚠', color: 'text-yellow-400' },
  error: { prefix: '✗', color: 'text-red-400' },
};

function formatTime(date: Date): string {
  return date.toLocaleTimeString('es-ES', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export const SystemLog: React.FC<SystemLogProps> = ({
  entries,
  maxHeight = 250,
  className,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [userScrolled, setUserScrolled] = useState(false);

  // Auto-scroll when new entries arrive (if enabled)
  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [entries, autoScroll]);

  // Detect user scroll to pause auto-scroll
  const handleScroll = useCallback(() => {
    if (!containerRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;

    if (!isAtBottom && !userScrolled) {
      setUserScrolled(true);
      setAutoScroll(false);
    } else if (isAtBottom && userScrolled) {
      setUserScrolled(false);
      setAutoScroll(true);
    }
  }, [userScrolled]);

  // Resume auto-scroll
  const handleResumeAutoScroll = useCallback(() => {
    setAutoScroll(true);
    setUserScrolled(false);
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, []);

  return (
    <div className={clsx('relative', className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-gray-900 border-b border-gray-700 rounded-t-lg">
        <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">
          System Log
        </span>
        <button
          onClick={handleResumeAutoScroll}
          className={clsx(
            'flex items-center gap-1 px-2 py-1 text-xs rounded transition-colors',
            autoScroll
              ? 'bg-green-900/50 text-green-400'
              : 'bg-gray-800 text-gray-500 hover:bg-gray-700 hover:text-gray-300'
          )}
        >
          {autoScroll ? (
            <>
              <span className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
              Auto
            </>
          ) : (
            <>
              <span className="w-1.5 h-1.5 bg-gray-500 rounded-full" />
              Pausado
            </>
          )}
        </button>
      </div>

      {/* Log entries */}
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="bg-gray-950 rounded-b-lg overflow-y-auto font-mono text-sm"
        style={{ maxHeight }}
      >
        {entries.length === 0 ? (
          <div className="px-3 py-4 text-gray-600 text-center">
            Esperando logs...
          </div>
        ) : (
          <div className="p-3 space-y-1">
            {entries.map((entry) => {
              const config = LEVEL_CONFIG[entry.level];
              return (
                <div
                  key={entry.id}
                  className={clsx('flex items-start gap-2', config.color)}
                >
                  <span className="flex-shrink-0 w-4 text-center">
                    {config.prefix}
                  </span>
                  <span className="flex-shrink-0 text-gray-500">
                    [{formatTime(entry.timestamp)}]
                  </span>
                  <span className="break-all">{entry.message}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Scroll indicator when paused */}
      {!autoScroll && entries.length > 0 && (
        <button
          onClick={handleResumeAutoScroll}
          className="absolute bottom-2 right-2 flex items-center gap-1 px-2 py-1 bg-primary-500 text-white text-xs rounded-full shadow-lg hover:bg-primary-600 transition-colors"
        >
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
          Ir al final
        </button>
      )}
    </div>
  );
};

export default SystemLog;
