"""
PiiCategory value object.

Enumeration of PII categories supported by ContextSafe.

Traceability:
- Standard: consolidated_standards.yaml#vocabulary.pii_categories
- Source: controlled_vocabulary.yaml#domain_vocabulary.pii_categories
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict

from contextsafe.domain.shared.errors import InvalidCategoryError
from contextsafe.domain.shared.types import Err, Ok, Result


class PiiCategoryEnum(str, Enum):
    """Enumeration of all PII categories."""

    # Person & Organization
    PERSON_NAME = "PERSON_NAME"
    ORGANIZATION = "ORGANIZATION"

    # Location
    ADDRESS = "ADDRESS"
    LOCATION = "LOCATION"
    POSTAL_CODE = "POSTAL_CODE"      # Spanish: Código Postal

    # Identity Documents
    DNI_NIE = "DNI_NIE"
    PASSPORT = "PASSPORT"

    # Contact
    PHONE = "PHONE"
    EMAIL = "EMAIL"

    # Financial
    BANK_ACCOUNT = "BANK_ACCOUNT"
    IBAN = "IBAN"
    CREDIT_CARD = "CREDIT_CARD"

    # Dates
    DATE = "DATE"                    # Generic date (not specifically birth date)

    # Health & Vehicle
    MEDICAL_RECORD = "MEDICAL_RECORD"
    LICENSE_PLATE = "LICENSE_PLATE"
    SOCIAL_SECURITY = "SOCIAL_SECURITY"

    # Professional & Legal (new)
    PROFESSIONAL_ID = "PROFESSIONAL_ID"  # Colegiado numbers, etc.
    CASE_NUMBER = "CASE_NUMBER"          # Judicial procedure numbers

    # Digital & Platform (new)
    PLATFORM = "PLATFORM"                # WhatsApp, Telegram, etc.
    IP_ADDRESS = "IP_ADDRESS"

    # =========================================================================
    # SECTOR LEGAL ESPAÑOL (nuevas categorías)
    # Ref: "Patrones Regex Sector Legal Español.md"
    # =========================================================================

    # Identificación Civil Avanzada
    ID_SUPPORT = "ID_SUPPORT"            # Número de Soporte (IDESP/IXESP) - CRÍTICO

    # Sector Judicial
    NIG = "NIG"                          # Número de Identificación General (19 dígitos)
    ECLI = "ECLI"                        # European Case Law Identifier
    CSV = "CSV"                          # Código Seguro de Verificación - CRÍTICO

    # Sector Sanitario
    HEALTH_ID = "HEALTH_ID"              # CIP-SNS y CIP Autonómicos

    # Hacienda y Patrimonio
    CADASTRAL_REF = "CADASTRAL_REF"      # Referencia Catastral

    # Ámbito Laboral
    EMPLOYER_ID = "EMPLOYER_ID"          # CCC - Código Cuenta de Cotización


# Alias patterns for each category
ALIAS_PATTERNS: Dict[PiiCategoryEnum, str] = {
    # Person & Organization
    PiiCategoryEnum.PERSON_NAME: "Persona_{N}",
    PiiCategoryEnum.ORGANIZATION: "Org_{N}",

    # Location
    PiiCategoryEnum.ADDRESS: "Dir_{N}",
    PiiCategoryEnum.LOCATION: "Lugar_{N}",
    PiiCategoryEnum.POSTAL_CODE: "CP_{N}",

    # Identity Documents
    PiiCategoryEnum.DNI_NIE: "ID_{N}",
    PiiCategoryEnum.PASSPORT: "Pasaporte_{N}",

    # Contact
    PiiCategoryEnum.PHONE: "Tel_{N}",
    PiiCategoryEnum.EMAIL: "Email_{N}",

    # Financial
    PiiCategoryEnum.BANK_ACCOUNT: "Cuenta_{N}",
    PiiCategoryEnum.IBAN: "IBAN_{N}",
    PiiCategoryEnum.CREDIT_CARD: "Tarjeta_{N}",

    # Dates
    PiiCategoryEnum.DATE: "Fecha_{N}",

    # Health & Vehicle
    PiiCategoryEnum.MEDICAL_RECORD: "HistoriaMedica_{N}",
    PiiCategoryEnum.LICENSE_PLATE: "Matricula_{N}",
    PiiCategoryEnum.SOCIAL_SECURITY: "NSS_{N}",

    # Professional & Legal
    PiiCategoryEnum.PROFESSIONAL_ID: "IdProf_{N}",
    PiiCategoryEnum.CASE_NUMBER: "Proc_{N}",

    # Digital & Platform
    PiiCategoryEnum.PLATFORM: "Plataforma_{N}",
    PiiCategoryEnum.IP_ADDRESS: "IP_{N}",

    # Sector Legal Español
    PiiCategoryEnum.ID_SUPPORT: "Soporte_{N}",
    PiiCategoryEnum.NIG: "NIG_{N}",
    PiiCategoryEnum.ECLI: "ECLI_{N}",
    PiiCategoryEnum.CSV: "CSV_{N}",
    PiiCategoryEnum.HEALTH_ID: "CIP_{N}",
    PiiCategoryEnum.CADASTRAL_REF: "RefCat_{N}",
    PiiCategoryEnum.EMPLOYER_ID: "CCC_{N}",
}


@dataclass(frozen=True, slots=True)
class PiiCategory:
    """
    Value object representing a PII category.

    Wraps the enum to provide factory method with Result type.
    """

    value: PiiCategoryEnum

    @classmethod
    def from_string(cls, value: str) -> Result[PiiCategory, InvalidCategoryError]:
        """
        Create a PiiCategory from string.

        Args:
            value: Category name (case-insensitive)

        Returns:
            Ok[PiiCategory] if valid, Err[InvalidCategoryError] if invalid
        """
        normalized = value.upper().replace("-", "_").replace(" ", "_")

        try:
            category_enum = PiiCategoryEnum(normalized)
            return Ok(cls(value=category_enum))
        except ValueError:
            return Err(InvalidCategoryError.create(value))

    @property
    def alias_pattern(self) -> str:
        """Get the alias pattern for this category."""
        return ALIAS_PATTERNS.get(self.value, "Alias_{N}")

    def generate_alias(self, index: int) -> str:
        """Generate an alias for this category with given index."""
        return self.alias_pattern.replace("{N}", str(index))

    def __str__(self) -> str:
        """String representation."""
        return self.value.value

    def __eq__(self, other: object) -> bool:
        """Compare by value."""
        if isinstance(other, PiiCategory):
            return self.value == other.value
        return False

    def __hash__(self) -> int:
        """Hash by value."""
        return hash(self.value)


# Convenience constants
PERSON_NAME = PiiCategory(PiiCategoryEnum.PERSON_NAME)
ORGANIZATION = PiiCategory(PiiCategoryEnum.ORGANIZATION)
ADDRESS = PiiCategory(PiiCategoryEnum.ADDRESS)
LOCATION = PiiCategory(PiiCategoryEnum.LOCATION)
POSTAL_CODE = PiiCategory(PiiCategoryEnum.POSTAL_CODE)
DNI_NIE = PiiCategory(PiiCategoryEnum.DNI_NIE)
PASSPORT = PiiCategory(PiiCategoryEnum.PASSPORT)
PHONE = PiiCategory(PiiCategoryEnum.PHONE)
EMAIL = PiiCategory(PiiCategoryEnum.EMAIL)
BANK_ACCOUNT = PiiCategory(PiiCategoryEnum.BANK_ACCOUNT)
IBAN = PiiCategory(PiiCategoryEnum.IBAN)
CREDIT_CARD = PiiCategory(PiiCategoryEnum.CREDIT_CARD)
DATE = PiiCategory(PiiCategoryEnum.DATE)
MEDICAL_RECORD = PiiCategory(PiiCategoryEnum.MEDICAL_RECORD)
LICENSE_PLATE = PiiCategory(PiiCategoryEnum.LICENSE_PLATE)
SOCIAL_SECURITY = PiiCategory(PiiCategoryEnum.SOCIAL_SECURITY)
PROFESSIONAL_ID = PiiCategory(PiiCategoryEnum.PROFESSIONAL_ID)
CASE_NUMBER = PiiCategory(PiiCategoryEnum.CASE_NUMBER)
PLATFORM = PiiCategory(PiiCategoryEnum.PLATFORM)
IP_ADDRESS = PiiCategory(PiiCategoryEnum.IP_ADDRESS)

# Sector Legal Español
ID_SUPPORT = PiiCategory(PiiCategoryEnum.ID_SUPPORT)
NIG = PiiCategory(PiiCategoryEnum.NIG)
ECLI = PiiCategory(PiiCategoryEnum.ECLI)
CSV = PiiCategory(PiiCategoryEnum.CSV)
HEALTH_ID = PiiCategory(PiiCategoryEnum.HEALTH_ID)
CADASTRAL_REF = PiiCategory(PiiCategoryEnum.CADASTRAL_REF)
EMPLOYER_ID = PiiCategory(PiiCategoryEnum.EMPLOYER_ID)
