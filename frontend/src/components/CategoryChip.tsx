/**
 * CategoryChip - PII category tag with icon
 * Updated for HSL Industrial Theme
 *
 * Traceability:
 * - Contract: CNT-UI-COMP-014
 */

import React from 'react';
import clsx from 'clsx';
import type { PiiCategory } from '@/types';
import { PII_CATEGORY_LABELS } from '@/types';

interface CategoryChipProps {
  category: PiiCategory;
  size?: 'sm' | 'md';
  className?: string;
}

// Mapping de categorías a colores HSL + íconos
// 6 grupos temáticos industriales
const CATEGORY_CONFIG: Record<PiiCategory, { colorClass: string; icon: string }> = {
  // GRUPO 1: Identidad Personal (azul)
  person_name: { colorClass: 'entity-chip-person', icon: '👤' },
  dni: { colorClass: 'entity-chip-dni', icon: '🪪' },
  nie: { colorClass: 'entity-chip-dni', icon: '🪪' },
  dni_nie: { colorClass: 'entity-chip-dni', icon: '🪪' },
  passport: { colorClass: 'entity-chip-person', icon: '🛂' },

  // GRUPO 2: Organización (gris neutro)
  organization: { colorClass: 'entity-chip-organization', icon: '🏢' },
  cif: { colorClass: 'entity-chip-organization', icon: '🏛️' },

  // GRUPO 3: Ubicación (verde esmeralda)
  address: { colorClass: 'entity-chip-address', icon: '📍' },
  location: { colorClass: 'entity-chip-address', icon: '🌍' },
  postal_code: { colorClass: 'entity-chip-address', icon: '📮' },

  // GRUPO 4: Contacto (cyan)
  phone: { colorClass: 'entity-chip-phone', icon: '📞' },
  email: { colorClass: 'entity-chip-email', icon: '📧' },
  url: { colorClass: 'entity-chip-email', icon: '🔗' },
  ip_address: { colorClass: 'entity-chip-phone', icon: '🌐' },

  // GRUPO 5: Financiero (ámbar)
  iban: { colorClass: 'entity-chip-iban', icon: '🏦' },
  bank_account: { colorClass: 'entity-chip-iban', icon: '🏦' },
  credit_card: { colorClass: 'entity-chip-iban', icon: '💳' },

  // GRUPO 6: Administrativo (violeta)
  social_security: { colorClass: 'entity-chip-social', icon: '📋' },
  nss: { colorClass: 'entity-chip-social', icon: '📋' },
  license_plate: { colorClass: 'entity-chip-social', icon: '🚗' },
  date: { colorClass: 'entity-chip-social', icon: '📅' },
  date_of_birth: { colorClass: 'entity-chip-social', icon: '📅' },
  medical_record: { colorClass: 'entity-chip-social', icon: '🏥' },
};

// Default fallback for unknown categories
const DEFAULT_CONFIG = {
  colorClass: 'entity-chip-organization',
  icon: '❓',
};

export const CategoryChip: React.FC<CategoryChipProps> = ({
  category,
  size = 'sm',
  className,
}) => {
  const config = CATEGORY_CONFIG[category] || DEFAULT_CONFIG;
  const label = PII_CATEGORY_LABELS[category] || category;

  return (
    <span
      className={clsx(
        'entity-chip',
        config.colorClass,
        {
          'px-2 py-0.5 text-xs': size === 'sm',
          'px-2.5 py-1 text-sm': size === 'md',
        },
        className
      )}
    >
      <span aria-hidden="true">{config.icon}</span>
      <span>{label}</span>
    </span>
  );
};

export default CategoryChip;
