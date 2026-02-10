"""
Synthetic strategy for Level 3 (ADVANCED) anonymization.

ARCHITECTURE: Level 3 = Level 2 (complete) + synthetic transformation

The flow is:
1. Execute EXACTLY the same as Level 2 (get/create alias via adapter)
2. For certain categories, transform the alias into synthetic data:
   - PERSON_NAME: LLM generates name of same gender
   - ORGANIZATION: LLM generates company of same sector
   - ADDRESS/LOCATION: LLM generates plausible location
   - DNI_NIE, IBAN, etc.: Code generates number with INVALID checksum

CRITICAL: Administrative numbers (DNI, IBAN, NSS, etc.) use INVALID checksums
to make it mathematically impossible to correspond to real data.

Example:
    "Juan García" → "Carlos Mendive" (LLM-generated, same gender)
    "Ibercaja" → "Banco del Valle" (LLM-generated, same sector: banking)
    "12345678Z" → "87654321X" (code-generated, INVALID control letter)
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import shutil
import subprocess
from typing import TYPE_CHECKING

import httpx

from contextsafe.infrastructure.nlp.strategies.base import (
    AnonymizationStrategy,
    ReplacementResult,
)

if TYPE_CHECKING:
    from contextsafe.application.ports.ner_service import NerDetection
    from contextsafe.infrastructure.nlp.anonymization_adapter import (
        InMemoryAnonymizationAdapter,
    )

logger = logging.getLogger(__name__)


# =============================================================================
# ENVIRONMENT DETECTION
# =============================================================================

def _is_wsl() -> bool:
    """Detect if running in WSL (Windows Subsystem for Linux)."""
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except Exception:
        return False


def _has_powershell() -> bool:
    """Check if PowerShell is available (for WSL→Windows communication)."""
    return shutil.which("powershell.exe") is not None


IS_WSL = _is_wsl()
HAS_POWERSHELL = _has_powershell()


# =============================================================================
# SYNTHETIC NUMBER GENERATORS (guaranteed INVALID checksums)
# =============================================================================
# These generators create numbers that LOOK valid but have mathematically
# incorrect control digits, making them impossible to correspond to real data.

DNI_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"


def generate_invalid_dni() -> str:
    """
    Generate a Spanish DNI with INVALID control letter.

    Real DNI: 8 digits + letter calculated as digits mod 23 → DNI_LETTERS
    We intentionally use a WRONG letter.
    """
    digits = random.randint(10000000, 99999999)
    valid_letter = DNI_LETTERS[digits % 23]
    # Pick any letter EXCEPT the valid one
    invalid_letters = [l for l in DNI_LETTERS if l != valid_letter]
    invalid_letter = random.choice(invalid_letters)
    return f"{digits}{invalid_letter}"


def generate_invalid_nie() -> str:
    """
    Generate a Spanish NIE with INVALID control letter.

    NIE format: X/Y/Z + 7 digits + control letter
    X=0, Y=1, Z=2 for calculation, then same mod-23 algorithm.
    """
    prefix_map = {"X": 0, "Y": 1, "Z": 2}
    prefix = random.choice(["X", "Y", "Z"])
    digits = random.randint(1000000, 9999999)
    full_number = int(f"{prefix_map[prefix]}{digits}")
    valid_letter = DNI_LETTERS[full_number % 23]
    invalid_letters = [l for l in DNI_LETTERS if l != valid_letter]
    invalid_letter = random.choice(invalid_letters)
    return f"{prefix}{digits}{invalid_letter}"


def generate_invalid_iban() -> str:
    """
    Generate a Spanish IBAN with INVALID check digits.

    Real IBAN check: rearrange, convert letters to numbers, mod 97 must equal 1.
    We use check digits "00" which is almost always invalid.
    """
    bank = f"{random.randint(0, 9999):04d}"
    branch = f"{random.randint(0, 9999):04d}"
    dc = f"{random.randint(0, 99):02d}"
    account = f"{random.randint(0, 9999999999):010d}"
    # Use invalid IBAN check digits (00 is almost always invalid)
    iban_check = "00"
    return f"ES{iban_check} {bank} {branch} {dc} {account[:4]} {account[4:]}"


def generate_invalid_nss() -> str:
    """
    Generate a Spanish Social Security Number with INVALID control digits.

    Format: XX/NNNNNNNN/CC where CC = mod-97 check
    We intentionally use wrong control digits.
    """
    province = f"{random.randint(1, 52):02d}"
    number = f"{random.randint(10000000, 99999999):08d}"
    full_num = int(f"{province}{number}")
    valid_control = f"{full_num % 97:02d}"
    # Use invalid control (add random offset and wrap)
    invalid_control = f"{(int(valid_control) + random.randint(1, 96)) % 97:02d}"
    return f"{province}/{number}/{invalid_control}"


def generate_invalid_credit_card() -> str:
    """
    Generate a credit card number that FAILS the Luhn algorithm.

    Luhn: sum of digits (doubling every second from right) must be divisible by 10.
    We ensure it's NOT divisible by 10.
    """
    # Start with Visa-like prefix
    digits = [4] + [random.randint(0, 9) for _ in range(14)]

    # Calculate Luhn checksum
    total = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d

    # Find check digit that would make it valid
    valid_check = (10 - (total % 10)) % 10
    # Use invalid check digit (anything except valid)
    invalid_check = (valid_check + random.randint(1, 9)) % 10
    digits.append(invalid_check)

    num = ''.join(map(str, digits))
    return f"{num[:4]} {num[4:8]} {num[8:12]} {num[12:]}"


def generate_phone() -> str:
    """Generate a plausible Spanish mobile number."""
    prefix = random.choice(["6", "7"])
    rest = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    return f"+34 {prefix}{rest[:2]} {rest[2:5]} {rest[5:]}"


def generate_license_plate() -> str:
    """Generate a Spanish license plate (valid format, random values)."""
    digits = f"{random.randint(0, 9999):04d}"
    # Spanish plates use consonants only (no vowels, no Ñ, Q)
    consonants = "BCDFGHJKLMNPRSTVWXYZ"
    letters = ''.join(random.choices(consonants, k=3))
    return f"{digits} {letters}"


# =============================================================================
# NUEVOS GENERADORES - SECTOR LEGAL ESPAÑOL
# Ref: "Patrones Regex Sector Legal Español.md"
# =============================================================================

def generate_id_support() -> str:
    """
    Generate a Spanish ID support number (Número de Soporte).

    DNI format: 3 letters + 6 digits
    These numbers don't have a public checksum algorithm,
    but we generate random ones that are unlikely to match real ones.
    """
    letters = ''.join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ", k=3))
    digits = f"{random.randint(0, 999999):06d}"
    return f"{letters}{digits}"


def generate_nig() -> str:
    """
    Generate a fake NIG (Número de Identificación General).

    Structure: Municipality(5) + Organ(2) + Jurisdiction(1) + Year(4) + Correlative(7)

    We use fake municipality codes (99XXX) and future years to ensure
    they don't match real cases.
    """
    # Fake municipality (99XXX range doesn't exist)
    municipality = f"99{random.randint(0, 999):03d}"
    # Random organ type
    organ = f"{random.randint(10, 99):02d}"
    # Random jurisdiction (1-4)
    jurisdiction = str(random.randint(1, 4))
    # Future year (2099) to ensure it's fake
    year = "2099"
    # Random correlative
    correlative = f"{random.randint(0, 9999999):07d}"
    return f"{municipality}/{organ}/{jurisdiction}/{year}/{correlative}"


def generate_ecli() -> str:
    """
    Generate a fake ECLI (European Case Law Identifier).

    Format: ECLI:ES:Organ:Year:Number

    We use fictional organ codes and future years.
    """
    # Fictional organs (XX, ZZ don't exist)
    organs = ["XX", "ZZ", "QQ", "YY"]
    organ = random.choice(organs)
    # Future year
    year = "2099"
    # Random number
    number = random.randint(10000, 99999)
    return f"ECLI:ES:{organ}:{year}:{number}"


def generate_csv() -> str:
    """
    Generate a fake CSV (Código Seguro de Verificación).

    High-entropy alphanumeric string (16-22 characters).
    Random generation ensures it won't match real CSVs.
    """
    length = random.randint(16, 22)
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ0123456789"
    return ''.join(random.choices(chars, k=length))


def generate_health_id() -> str:
    """
    Generate a fake CIP-SNS (Spanish Health ID).

    Format: 4 letters (from surnames) + 12 digits

    We use consonant-only prefixes that are unlikely real name patterns.
    """
    # Consonant-only prefix (unlikely real surname pattern)
    consonants = "BCDFGHJKLMNPQRSTVWXZ"
    prefix = ''.join(random.choices(consonants, k=4))
    # Random digits
    digits = ''.join([str(random.randint(0, 9)) for _ in range(12)])
    return f"{prefix}{digits}"


def generate_cadastral_ref() -> str:
    """
    Generate a fake Cadastral Reference (Referencia Catastral).

    Urban format: 7 digits + 2 letters + 4 digits + 4 letters (20 chars)

    We use patterns that don't correspond to real geographic zones.
    """
    # First block: 7 digits (fake zone starting with 9999)
    block1 = f"9999{random.randint(0, 999):03d}"
    # Second block: 7 digits
    block2 = f"{random.randint(0, 9999999):07d}"
    # Control letters (2)
    letters1 = ''.join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ", k=2))
    # Final 4 digits
    digits = f"{random.randint(0, 9999):04d}"
    # Final 4 letters
    letters2 = ''.join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ", k=4))
    return f"{block1}{block2}{letters1}{digits}{letters2}"


def generate_invalid_employer_id() -> str:
    """
    Generate a Spanish CCC (Código Cuenta de Cotización) with INVALID control digits.

    Format: Province(2) + Regime(2) + Number(7) + Control(2) = 13 digits

    The control digits are calculated from Province + Number (mod 97).
    We intentionally use wrong control digits.
    """
    # Random province (01-52)
    province = f"{random.randint(1, 52):02d}"
    # Random regime (usually 11 for general)
    regime = f"{random.randint(10, 99):02d}"
    # Random employer number
    number = f"{random.randint(1000000, 9999999):07d}"
    # Calculate what would be valid control
    full_num = int(f"{province}{number}")
    valid_control = full_num % 97
    # Use invalid control (add offset)
    invalid_control = (valid_control + random.randint(1, 96)) % 97
    return f"{province}/{regime}/{number}/{invalid_control:02d}"


# Categories that use CODE generators (guaranteed invalid checksums)
CODE_GENERATORS = {
    "DNI_NIE": lambda: random.choice([generate_invalid_dni, generate_invalid_nie])(),
    "IBAN": generate_invalid_iban,
    "BANK_ACCOUNT": generate_invalid_iban,
    "SOCIAL_SECURITY": generate_invalid_nss,
    "CREDIT_CARD": generate_invalid_credit_card,
    "PHONE": generate_phone,
    "LICENSE_PLATE": generate_license_plate,
    # Sector Legal Español
    "ID_SUPPORT": generate_id_support,
    "NIG": generate_nig,
    "ECLI": generate_ecli,
    "CSV": generate_csv,
    "HEALTH_ID": generate_health_id,
    "CADASTRAL_REF": generate_cadastral_ref,
    "EMPLOYER_ID": generate_invalid_employer_id,
}

# Categories that use LLM for semantic coherence
LLM_CATEGORIES = {
    "PERSON_NAME",
    "ORGANIZATION",
    "ADDRESS",
    "LOCATION",
    "EMAIL",
}


# =============================================================================
# GENDER DETECTION FOR NAME CONSISTENCY
# =============================================================================

FEMALE_NAMES = {
    "maria", "maría", "ana", "carmen", "laura", "isabel", "rosa", "teresa",
    "elena", "cristina", "lucia", "lucía", "marta", "sara", "paula", "eva",
    "raquel", "silvia", "nuria", "pilar", "dolores", "mercedes", "angeles",
    "ángeles", "francisca", "josefa", "antonia", "julia", "beatriz",
    "alicia", "patricia", "mónica", "monica", "susana", "rocío", "rocio",
    "esther", "ester", "irene", "natalia", "sandra", "yolanda", "diana",
    "carolina", "adriana", "gloria", "luisa", "manuela", "consuelo",
    "inmaculada", "concepción", "concepcion", "amparo", "victoria",
}

MALE_NAMES = {
    "juan", "jose", "josé", "antonio", "manuel", "francisco", "david",
    "carlos", "jesus", "jesús", "javier", "daniel", "miguel", "rafael",
    "pedro", "pablo", "luis", "alberto", "fernando", "sergio", "jorge",
    "enrique", "andres", "andrés", "ramon", "ramón", "diego", "alejandro",
    "victor", "víctor", "mario", "alfonso", "eduardo", "ignacio", "adrian",
    "adrián", "ivan", "iván", "ruben", "rubén", "oscar", "óscar", "jaime",
}

MALE_NAMES_ENDING_A = {"borja", "garcia", "garcía", "joshua", "luca", "nikita"}


def detect_gender(name: str) -> str:
    """
    Detect the gender of a Spanish name.

    Returns: "male", "female", or "unknown"
    """
    import re

    name_lower = name.lower().strip()

    # By prefix
    if re.match(r"^(?:d\.|don)\s+", name_lower):
        return "male"
    if re.match(r"^(?:dña\.|doña)\s+", name_lower):
        return "female"

    # Extract first name
    clean_name = re.sub(
        r"^(?:d\.?ª?|dña\.?|don|doña|sr\.?|sra\.?)\s+", "", name_lower
    )
    first_name = clean_name.split()[0] if clean_name.split() else ""

    if first_name in FEMALE_NAMES:
        return "female"
    if first_name in MALE_NAMES:
        return "male"
    if first_name in MALE_NAMES_ENDING_A:
        return "male"

    # Heuristic by ending
    if first_name.endswith("a") and first_name not in MALE_NAMES_ENDING_A:
        return "female"
    if first_name.endswith(("o", "os", "io")):
        return "male"

    return "unknown"


def detect_organization_sector(name: str) -> str:
    """
    Detect the sector of an organization for semantic coherence.

    Returns sector hint like "banco", "abogados", "hospital", etc.
    """
    name_lower = name.lower()

    # Banking/Financial
    if any(w in name_lower for w in ["banco", "caja", "bankia", "bbva", "santander",
                                       "ibercaja", "kutxa", "laboral", "credit", "financ"]):
        return "banco o caja de ahorros"

    # Legal
    if any(w in name_lower for w in ["abogado", "letrado", "bufete", "legal",
                                       "jurídic", "juridic", "asesor", "slp"]):
        return "despacho de abogados"

    # Healthcare
    if any(w in name_lower for w in ["hospital", "clínica", "clinica", "médic",
                                       "medic", "sanitar", "salud", "dental"]):
        return "centro médico o clínica"

    # Insurance
    if any(w in name_lower for w in ["seguro", "mutua", "asegurador", "mapfre",
                                       "axa", "allianz", "zurich"]):
        return "compañía de seguros"

    # Technology
    if any(w in name_lower for w in ["tech", "software", "sistemas", "informátic",
                                       "digital", "datos", "cloud"]):
        return "empresa tecnológica"

    # Construction/Real Estate
    if any(w in name_lower for w in ["construc", "inmobil", "promo", "edifici"]):
        return "empresa constructora o inmobiliaria"

    return "empresa"


# =============================================================================
# LLM PROMPTS WITH SEMANTIC COHERENCE
# =============================================================================

def get_person_name_prompt(original: str) -> str:
    """Generate prompt for person name with gender consistency."""
    gender = detect_gender(original)

    if gender == "female":
        return f"""Genera un nombre completo FEMENINO español (nombre + dos apellidos).
Debe sonar natural y plausible: "María Solana Ruiz", "Carmen López García".
El nombre DEBE ser femenino. Solo escribe el nombre, nada más."""
    elif gender == "male":
        return f"""Genera un nombre completo MASCULINO español (nombre + dos apellidos).
Debe sonar natural y plausible: "Carlos Mendive Ortega", "Juan García López".
El nombre DEBE ser masculino. Solo escribe el nombre, nada más."""
    else:
        return f"""Genera un nombre completo español (nombre + dos apellidos).
Debe sonar natural y plausible: "María Solana Ruiz", "Carlos Mendive Ortega".
Solo escribe el nombre, nada más."""


def get_organization_prompt(original: str) -> str:
    """Generate prompt for organization with sector coherence."""
    sector = detect_organization_sector(original)
    original_lower = original.lower()

    # Detect legal form suffix
    legal_form = ""
    if "s.l.p" in original_lower or "slp" in original_lower:
        legal_form = "S.L.P."
    elif "s.l.u" in original_lower or "slu" in original_lower:
        legal_form = "S.L.U."
    elif "s.l" in original_lower or " sl" in original_lower:
        legal_form = "S.L."
    elif "s.a" in original_lower or " sa" in original_lower:
        legal_form = "S.A."

    # Build examples based on sector
    if "abogado" in sector:
        examples = '"Roldán Abogados", "Bufete Castilla", "Asesoría Jurídica Norte"'
    elif "banco" in sector:
        examples = '"Caja del Valle", "Banco Tramontana", "Ibérica Ahorro"'
    elif "médic" in sector or "clínica" in sector:
        examples = '"Clínica Salud Norte", "Centro Médico Tramontana"'
    else:
        examples = '"Servicios Integrales Norte", "Comercial Ibérica"'

    form_instruction = f"\nMantén la forma jurídica: {legal_form}" if legal_form else ""

    return f"""Genera un nombre de empresa española INVENTADO del sector: {sector}.
El nombre debe ser SIMILAR en estilo al original pero DIFERENTE.
Ejemplos válidos: {examples}{form_instruction}
IMPORTANTE: El nombre debe sonar profesional y coherente con el sector.
Solo escribe el nombre de la empresa, nada más."""


CATEGORY_PROMPTS = {
    "ADDRESS": """Genera una dirección española plausible pero inventada.
Usa patrones reales: "Calle del Almendro 15, 3ºB", "Avenida de los Rosales 42".
Solo escribe la dirección, nada más.""",

    "LOCATION": """Genera un nombre de pueblo o ciudad española que suene auténtico pero sea inventado.
Usa patrones reales: "Villanueva del Prado", "San Martín de la Vega", "Fuente del Olmo".
Solo escribe el nombre del lugar, nada más.""",

    "EMAIL": """Genera un email plausible con nombre inventado.
Usa patrones comunes: nombre.apellido@empresa.es, n.apellido@mail.com
Solo escribe el email, nada más.""",
}


# =============================================================================
# SYNTHETIC STRATEGY
# =============================================================================

class SyntheticStrategy(AnonymizationStrategy):
    """
    Level 3: Synthetic data generation.

    ARCHITECTURE: Level 3 = Level 2 (complete) + synthetic transformation

    Flow:
    1. Use adapter.get_or_create_alias() - SAME as Level 2
    2. Transform alias into synthetic value:
       - LLM for names/orgs (with semantic coherence)
       - Code for numbers (with INVALID checksums)
    3. Store mapping: original → synthetic (for reversibility)

    This ensures Level 3 ALWAYS works even if LLM fails (falls back to Level 2).
    """

    def __init__(
        self,
        ollama_url: str = "http://localhost:11434",
        model: str = "qwen2:1.5b",
        timeout: float = 30.0,
        use_gpu: bool = False,
        adapter: "InMemoryAnonymizationAdapter | None" = None,
    ):
        """Initialize synthetic strategy."""
        self._ollama_url = ollama_url
        self._model = model
        self._timeout = timeout
        self._use_gpu = use_gpu
        self._adapter = adapter
        # Cache: (category, normalized_original) -> synthetic
        self._synthetic_cache: dict[tuple[str, str], str] = {}
        self._http_client: httpx.AsyncClient | None = None
        # NOTE: Removed _ollama_available cache - was causing silent fallback to Level 2

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=self._timeout)
        return self._http_client

    async def _check_ollama_available(self) -> bool:
        """
        Check if Ollama is available.

        NO CACHE: Always check on each call to handle Ollama restarts.
        Previous cache caused silent fallback to Level 2 for ALL entities
        if first check failed, even if Ollama became available later.
        """
        try:
            client = await self._get_client()
            response = await client.get(f"{self._ollama_url}/api/tags", timeout=5.0)
            available = response.status_code == 200
            if available:
                logger.info(f"Ollama available at {self._ollama_url}")
            else:
                logger.warning(f"Ollama returned {response.status_code}")
            return available
        except Exception as e:
            logger.warning(f"Ollama not available at {self._ollama_url}: {e}")
            return False

    async def _generate_with_ollama(self, prompt: str) -> str:
        """Call Ollama API to generate synthetic data."""
        if not await self._check_ollama_available():
            return ""

        client = await self._get_client()

        try:
            options = {"temperature": 0.7, "num_predict": 50}
            if not self._use_gpu:
                options["num_gpu"] = 0

            response = await client.post(
                f"{self._ollama_url}/api/generate",
                json={
                    "model": self._model,
                    "prompt": prompt,
                    "stream": False,
                    "options": options,
                },
            )
            response.raise_for_status()
            data = response.json()
            generated = data.get("response", "").strip()

            # Clean up
            generated = generated.strip('"\'')
            generated = generated.split('\n')[0]

            logger.debug(f"Ollama generated synthetic ({len(generated)} chars)")
            return generated

        except Exception as e:
            logger.warning(f"Ollama generation failed: {e}")
            return ""

    def _generate_with_powershell(self, prompt: str) -> str:
        """Call Ollama via PowerShell (WSL→Windows fallback)."""
        if not HAS_POWERSHELL:
            return ""

        try:
            options = {"temperature": 0.7, "num_predict": 50}
            if not self._use_gpu:
                options["num_gpu"] = 0

            body = {
                "model": self._model,
                "prompt": prompt,
                "stream": False,
                "options": options,
            }
            body_json = json.dumps(body, ensure_ascii=False)

            ps_command = f"""
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$body = @'
{body_json}
'@
$response = Invoke-RestMethod -Uri 'http://localhost:11434/api/generate' -Method Post -Body $body -ContentType 'application/json; charset=utf-8'
$response.response
"""

            result = subprocess.run(
                ["powershell.exe", "-Command", ps_command],
                capture_output=True,
                timeout=self._timeout,
            )

            try:
                stdout = result.stdout.decode('utf-8').strip()
            except UnicodeDecodeError:
                stdout = result.stdout.decode('latin-1').strip()

            if result.returncode == 0 and stdout:
                generated = stdout.strip('"\'').split('\n')[0]
                logger.debug(f"PowerShell Ollama generated synthetic ({len(generated)} chars)")
                return generated

            return ""

        except Exception as e:
            logger.warning(f"PowerShell Ollama error: {e}")
            return ""

    async def _get_synthetic_for_category(
        self,
        category: str,
        original: str,
    ) -> str:
        """
        Generate synthetic value for a category.

        Returns empty string if generation fails (caller should use pseudonym).
        """
        # Priority 1: Code generators for numbers (INVALID checksums)
        if category in CODE_GENERATORS:
            synthetic = CODE_GENERATORS[category]()
            logger.info(f"Code-generated {category}: {synthetic} (invalid checksum)")
            return synthetic

        # Priority 2: LLM for text categories
        if category not in LLM_CATEGORIES:
            return ""  # Not a category we transform

        # Build prompt with semantic coherence
        if category == "PERSON_NAME":
            prompt = get_person_name_prompt(original)
        elif category == "ORGANIZATION":
            prompt = get_organization_prompt(original)
        else:
            prompt = CATEGORY_PROMPTS.get(category, "")

        if not prompt:
            return ""

        # Add context hint
        prompt += f"\n\nContexto (para referencia, genera algo DIFERENTE): {original}"

        # Try Ollama HTTP first
        print(f"[LLM] Calling Ollama for {category}: {original[:30]}...")
        synthetic = await self._generate_with_ollama(prompt)
        print(f"[LLM] Ollama returned: {synthetic[:50] if synthetic else '(empty)'}")

        # Fallback to PowerShell if in WSL and HTTP failed
        if not synthetic and IS_WSL and HAS_POWERSHELL:
            logger.info("Trying PowerShell fallback for Ollama...")
            synthetic = self._generate_with_powershell(prompt)

        # Validate: don't return if same as original
        if synthetic and synthetic.lower() != original.lower():
            return synthetic

        return ""

    async def generate_replacement(
        self,
        detection: "NerDetection",
        project_id: str,
    ) -> ReplacementResult:
        """
        Generate synthetic replacement.

        ARCHITECTURE: Level 3 = Level 2 + synthetic transformation

        1. FIRST: Get/create alias via adapter (SAME as Level 2)
           - This ensures detection works even if LLM fails
           - The adapter handles name unification (Alberto Baxeras = Alberto Baxeras Aizpún)
        2. THEN: Try to transform into synthetic value
           - LLM for names/orgs (semantic coherence)
           - Code for numbers (invalid checksums)
        3. If transformation fails: use Level 2 alias (guaranteed fallback)

        CRITICAL: Cache uses base_alias as key to ensure consistency.
        "D. Alberto Baxeras" and "D. Alberto Baxeras Aizpún" get the same
        base_alias from the adapter, so they get the same synthetic value.
        """
        category = detection.category.value
        original = detection.value

        # ================================================================
        # STEP 1: Get Level 2 alias as BASE (guaranteed to work)
        # This is the SAME as PseudonymStrategy
        # The adapter handles name unification via find_matching_value()
        # ================================================================
        if self._adapter is None:
            raise RuntimeError("SyntheticStrategy requires adapter reference")

        base_alias = await self._adapter.get_or_create_alias(
            category=category,
            original_value=original,
            project_id=project_id,
            level="ADVANCED",
        )

        logger.debug(f"Level 2 base alias: {original} → {base_alias}")

        # ================================================================
        # CACHE KEY: Use base_alias instead of normalized value
        # This ensures that "Alberto Baxeras" and "Alberto Baxeras Aizpún"
        # (which get the same base_alias) also get the same synthetic value.
        # ================================================================
        cache_key = (category, base_alias)

        # Check cache first (AFTER getting base_alias)
        if cache_key in self._synthetic_cache:
            synthetic = self._synthetic_cache[cache_key]
            logger.debug(f"Cache hit for {base_alias}: {synthetic}")
            return ReplacementResult(
                original=original,
                replacement=synthetic,
                category=category,
                glossary_entry={
                    "original_text": original,
                    "alias": synthetic,
                    "category": category,
                },
            )

        # ================================================================
        # STEP 2: Try to transform into synthetic value
        # ================================================================
        synthetic = await self._get_synthetic_for_category(category, original)

        # ================================================================
        # STEP 3: Use synthetic if available, else fall back to Level 2
        # ================================================================
        if synthetic:
            final_replacement = synthetic
            logger.debug(f"Level 3 synthetic: [REDACTED] → {synthetic}")
        else:
            final_replacement = base_alias
            logger.debug(f"Level 3 fallback to Level 2: [REDACTED] → {base_alias}")

        # Cache for consistency (keyed by base_alias)
        self._synthetic_cache[cache_key] = final_replacement

        return ReplacementResult(
            original=original,
            replacement=final_replacement,
            category=category,
            glossary_entry={
                "original_text": original,
                "alias": final_replacement,
                "category": category,
            },
        )

    @property
    def creates_glossary_entries(self) -> bool:
        """Synthetic strategy creates glossary entries for reversibility."""
        return True

    async def close(self) -> None:
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
