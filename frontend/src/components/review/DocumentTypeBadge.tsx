/**
 * DocumentTypeBadge - Shows classified document type.
 */

import React from 'react';
import type { LegalDocumentType } from '@/types';

interface DocumentTypeBadgeProps {
  documentType: LegalDocumentType;
  confidence?: number;
}

const TYPE_LABELS: Record<LegalDocumentType, string> = {
  SENTENCIA: 'Sentencia',
  ESCRITURA: 'Escritura',
  FACTURA: 'Factura',
  RECURSO: 'Recurso',
  DENUNCIA: 'Denuncia',
  CONTRATO: 'Contrato',
  GENERIC: 'Genérico',
};

export const DocumentTypeBadge: React.FC<DocumentTypeBadgeProps> = ({
  documentType,
  confidence,
}) => {
  if (documentType === 'GENERIC') return null;

  const label = TYPE_LABELS[documentType];

  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200 rounded"
      title={confidence ? `${label} (${Math.round(confidence * 100)}% confianza)` : label}
    >
      {label}
    </span>
  );
};

export default DocumentTypeBadge;
