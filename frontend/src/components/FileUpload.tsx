/**
 * FileUpload - Drag-drop file upload component
 *
 * Traceability:
 * - Contract: CNT-UI-COMP-001
 * - Binding: UI-BIND-001
 */

import React, { useCallback, useState, useRef } from 'react';
import clsx from 'clsx';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  acceptedTypes: string[];
  maxSizeMb?: number;
  disabled?: boolean;
  className?: string;
  variant?: 'default' | 'industrial';
}

const FILE_TYPE_MAP: Record<string, string> = {
  'pdf': 'application/pdf',
  'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'txt': 'text/plain',
  'png': 'image/png',
  'jpg': 'image/jpeg',
  'jpeg': 'image/jpeg',
};

export const FileUpload: React.FC<FileUploadProps> = ({
  onFileSelect,
  acceptedTypes,
  maxSizeMb = 50,
  disabled = false,
  className,
  variant = 'default',
}) => {
  const isIndustrial = variant === 'industrial';
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const acceptedMimeTypes = acceptedTypes
    .map((t) => FILE_TYPE_MAP[t] || t)
    .join(',');

  const validateFile = useCallback(
    (file: File): string | null => {
      // Check file type
      const ext = file.name.split('.').pop()?.toLowerCase() || '';
      if (!acceptedTypes.includes(ext)) {
        return `Tipo de archivo no soportado. Acepta: ${acceptedTypes.join(', ')}`;
      }

      // Check file size
      const sizeMb = file.size / (1024 * 1024);
      if (sizeMb > maxSizeMb) {
        return `Archivo demasiado grande. Máximo: ${maxSizeMb}MB`;
      }

      return null;
    },
    [acceptedTypes, maxSizeMb]
  );

  const handleFile = useCallback(
    (file: File) => {
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        return;
      }
      setError(null);
      onFileSelect(file);
    },
    [onFileSelect, validateFile]
  );

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (!disabled) {
        setIsDragging(true);
      }
    },
    [disabled]
  );

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      if (disabled) return;

      const file = e.dataTransfer.files[0];
      if (file) {
        handleFile(file);
      }
    },
    [disabled, handleFile]
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        handleFile(file);
      }
      // Reset input
      e.target.value = '';
    },
    [handleFile]
  );

  const handleClick = useCallback(() => {
    if (!disabled) {
      inputRef.current?.click();
    }
  }, [disabled]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if ((e.key === 'Enter' || e.key === ' ') && !disabled) {
        e.preventDefault();
        inputRef.current?.click();
      }
    },
    [disabled]
  );

  // Industrial variant
  if (isIndustrial) {
    return (
      <div className={className}>
        <div
          role="button"
          tabIndex={disabled ? -1 : 0}
          aria-label="Subir documento"
          aria-disabled={disabled}
          data-testid="file-upload"
          onClick={handleClick}
          onKeyDown={handleKeyDown}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={clsx(
            'upload-zone-industrial',
            {
              'dragging': isDragging,
              'opacity-50 cursor-not-allowed': disabled,
            }
          )}
        >
          <input
            ref={inputRef}
            type="file"
            accept={acceptedMimeTypes}
            onChange={handleInputChange}
            disabled={disabled}
            className="hidden"
            aria-hidden="true"
          />

          {/* Industrial Plus Icon */}
          <div className={clsx(
            'w-12 h-12 mb-3 flex items-center justify-center',
            'border-2 border-dashed',
            isDragging ? 'border-primary text-primary' : 'border-muted-foreground/50 text-muted-foreground'
          )}>
            <span className="text-2xl font-light">+</span>
          </div>

          {/* Industrial Text */}
          <p className="upload-text">
            ARRASTRAR ARCHIVOS FUENTE
          </p>
          <p className="upload-hint">
            {acceptedTypes.map((t) => t.toUpperCase()).join(' · ')} (MAX {maxSizeMb}MB)
          </p>
        </div>

        {/* Error message */}
        {error && (
          <p className="mt-2 text-[10px] uppercase tracking-wider text-destructive" role="alert">
            {error}
          </p>
        )}
      </div>
    );
  }

  // Default variant
  return (
    <div className={className}>
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label="Subir documento"
        aria-disabled={disabled}
        data-testid="file-upload"
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={clsx(
          'relative flex flex-col items-center justify-center',
          'w-full min-h-[200px] p-6',
          'border-2 border-dashed rounded-lg',
          'transition-colors duration-200',
          'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2',
          {
            'border-gray-300 dark:border-gray-600': !isDragging && !disabled,
            'border-primary-500 bg-primary-50 dark:bg-primary-900/20': isDragging,
            'bg-gray-50 dark:bg-gray-800': !isDragging && !disabled,
            'bg-gray-100 dark:bg-gray-900 cursor-not-allowed opacity-50': disabled,
            'cursor-pointer hover:border-primary-400 hover:bg-primary-50/50 dark:hover:bg-primary-900/10':
              !disabled,
          }
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept={acceptedMimeTypes}
          onChange={handleInputChange}
          disabled={disabled}
          className="hidden"
          aria-hidden="true"
        />

        {/* Icon */}
        <svg
          className={clsx('w-12 h-12 mb-4', {
            'text-primary-500': isDragging,
            'text-gray-400 dark:text-gray-500': !isDragging,
          })}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
          />
        </svg>

        {/* Text */}
        <p className="mb-2 text-sm text-gray-700 dark:text-gray-300">
          <span className="font-semibold">Haz clic para subir</span> o arrastra y suelta
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {acceptedTypes.map((t) => t.toUpperCase()).join(', ')} (máx. {maxSizeMb}MB)
        </p>
      </div>

      {/* Error message */}
      {error && (
        <p
          className="mt-2 text-sm text-danger-600 dark:text-danger-500"
          role="alert"
        >
          {error}
        </p>
      )}
    </div>
  );
};

export default FileUpload;
