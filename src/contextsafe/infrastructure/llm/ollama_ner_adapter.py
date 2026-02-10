"""
Ollama LLM-based NER adapter for enhanced PII detection.

Uses local LLM (Qwen, Llama, etc.) via Ollama for semantic entity detection.
Designed to run BEFORE Presidio as primary detection (Option B architecture).

Traceability:
- Port: ports.NerService
- Architecture: Pre-Presidio LLM detection
"""

from __future__ import annotations

import json
import re
import subprocess
from typing import Any

import httpx

from contextsafe.application.ports import NerDetection, NerService
from contextsafe.domain.shared.value_objects import (
    ConfidenceScore,
    PiiCategory,
    TextSpan,
)


# System prompt for PII detection in Spanish legal documents
SYSTEM_PROMPT = """Eres un experto en detección de datos personales (PII) en documentos legales españoles.

Tu tarea es identificar TODAS las entidades que contienen información personal identificable.

CATEGORÍAS A DETECTAR:
- PERSON_NAME: Nombres completos de personas físicas, INCLUYENDO:
  - Nombres con título nobiliario: "D. Ignacio Sancho Gargallo", "Dña. María López"
  - Nombres con título profesional: "Agustín Pardillo Hernández, Letrado del Gabinete Técnico"
  - Nombres en funciones judiciales: "Excmo. Sr. D. Fernando Cerdá Albero"
  - DETECTAR EL NOMBRE COMPLETO incluyendo el título (D., Dña., Don, Doña, Excmo., etc.)
- ORGANIZATION: Empresas, sociedades, entidades (ej: "MENTOR ABOGADOS SLP", "Telefónica S.A.")
- DNI_NIE: Documentos de identidad españoles (ej: "12345678Z", "X1234567A")
- SOCIAL_SECURITY: Números de Seguridad Social (ej: "28/12345678/89")
- ADDRESS: Direcciones postales completas (ej: "C/ Gran Vía 45, 3º B, 28001 Madrid")
- POSTAL_CODE: Códigos postales (ej: "28001", "08080")
- PHONE: Números de teléfono (ej: "+34 612 345 678", "91 123 45 67")
- EMAIL: Direcciones de correo electrónico
- BANK_ACCOUNT: IBAN y cuentas bancarias (ej: "ES91 2100 0418 4502 0005 1332")
- DATE: Fechas que puedan identificar personas o eventos privados (ej: fechas de contratos, citas, etc.)
  NOTA: NO detectar fechas de sentencias judiciales ni documentos públicos (son información pública)

NO DETECTAR como PII (EXCLUIR ESTOS CASOS):
- Referencias de sentencias y autos: "Sentencia 61/2019", "Sentencia 1947/2025", "Auto 123/2020"
- Números de sentencia dentro del texto: "n.º 61/2019", "n.º 456/2020"
- Referencias legales: "Ley 39/2015", "R.D. 1234/2021", "art. 367 LSC", "art. 1301 CC"
- Nombres de ciudades públicas (Madrid, Barcelona, Valencia)
- Nombres de tribunales: "TRIBUNAL SUPREMO", "SALA PRIMERA"
- El rol sin nombre: "el Magistrado", "el Letrado", "el Procurador"
- Años simples: "2025", "2026"

REGLAS CRÍTICAS:
1. Para PERSON_NAME: detecta el nombre COMPLETO incluyendo honoríficos (D., Dña., Excmo.)
2. Para fechas de sentencias (ej: "DE 23 DE DICIEMBRE"): NO detectar, son fechas de documentos públicos
3. Números con formato XX/YYYY (ej: "61/2019") son SIEMPRE referencias de casos, NUNCA personas

FORMATO DE RESPUESTA (JSON estricto):
{
  "entities": [
    {"text": "texto exacto encontrado", "category": "CATEGORY", "start": 0, "end": 10}
  ]
}

IMPORTANTE:
- "start" y "end" son posiciones de caracteres en el texto original
- Devuelve SOLO el JSON, sin explicaciones
- Si no hay entidades, devuelve {"entities": []}
"""


class OllamaNerAdapter(NerService):
    """
    NER service using local LLM via Ollama.

    Provides semantic understanding for PII detection in Spanish legal documents.
    Designed as primary detector (Pre-Presidio) for Option B architecture.

    Uses PowerShell as transport when running in WSL to bypass firewall issues.
    """

    def __init__(
        self,
        model_name: str = "hf.co/Qwen/Qwen3-14B-GGUF:Q6_K",
        ollama_host: str = "http://localhost:11434",
        timeout: float = 120.0,
        temperature: float = 0.1,
        use_powershell: bool = True,
    ) -> None:
        """
        Initialize the Ollama NER adapter.

        Args:
            model_name: Ollama model to use
            ollama_host: Ollama API endpoint (localhost for PowerShell mode)
            timeout: Request timeout in seconds
            temperature: LLM temperature (lower = more deterministic)
            use_powershell: Use PowerShell for API calls (WSL workaround)
        """
        self._model_name = model_name
        self._ollama_host = ollama_host.rstrip("/")
        self._timeout = timeout
        self._temperature = temperature
        self._use_powershell = use_powershell
        self._client: httpx.AsyncClient | None = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    def _call_via_powershell(self, endpoint: str, payload: dict | None = None) -> str:
        """Call Ollama API via PowerShell (WSL workaround)."""
        import tempfile
        import os

        url = f"{self._ollama_host}{endpoint}"

        if payload:
            # Write JSON to temp file to avoid escaping issues
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                json.dump(payload, f, ensure_ascii=False)
                temp_path = f.name

            # Convert WSL path to Windows path
            win_path = subprocess.run(
                ["wslpath", "-w", temp_path],
                capture_output=True,
                text=True
            ).stdout.strip()

            ps_cmd = f'''
            $body = Get-Content -Raw -Encoding UTF8 "{win_path}"
            $response = Invoke-WebRequest -Uri "{url}" -Method POST -Body $body -ContentType "application/json; charset=utf-8" -UseBasicParsing
            $response.Content
            '''

            try:
                result = subprocess.run(
                    ["powershell.exe", "-Command", ps_cmd],
                    capture_output=True,
                    timeout=self._timeout,
                )
            finally:
                os.unlink(temp_path)
        else:
            # GET request
            ps_cmd = f'''
            $response = Invoke-WebRequest -Uri "{url}" -UseBasicParsing
            $response.Content
            '''
            result = subprocess.run(
                ["powershell.exe", "-Command", ps_cmd],
                capture_output=True,
                timeout=self._timeout,
            )

        if result.returncode != 0:
            raise RuntimeError(f"PowerShell error: {result.stderr.decode('utf-8', errors='replace')}")

        # Handle Windows encoding (UTF-8 with BOM or CP1252)
        stdout = result.stdout
        try:
            return stdout.decode('utf-8').strip()
        except UnicodeDecodeError:
            try:
                return stdout.decode('utf-8-sig').strip()
            except UnicodeDecodeError:
                return stdout.decode('cp1252', errors='replace').strip()

    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API with the given prompt."""
        payload = {
            "model": self._model_name,
            "prompt": prompt,
            "system": SYSTEM_PROMPT,
            "stream": False,
            "options": {
                "temperature": self._temperature,
                "num_predict": 4096,
            },
        }

        if self._use_powershell:
            response_text = self._call_via_powershell("/api/generate", payload)
            result = json.loads(response_text)
            return result.get("response", "")
        else:
            client = await self._ensure_client()
            response = await client.post(
                f"{self._ollama_host}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")

    def _parse_llm_response(self, response: str, original_text: str) -> list[dict[str, Any]]:
        """Parse LLM JSON response into entity list."""
        # Try to extract JSON from response
        try:
            # Find JSON in response (LLM might add extra text)
            json_match = re.search(r'\{[\s\S]*"entities"[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return data.get("entities", [])
        except json.JSONDecodeError:
            pass

        # Fallback: try to parse entire response as JSON
        try:
            data = json.loads(response.strip())
            return data.get("entities", [])
        except json.JSONDecodeError:
            return []

    def _validate_entity(
        self, entity: dict[str, Any], original_text: str
    ) -> dict[str, Any] | None:
        """Validate and correct entity positions."""
        text = entity.get("text", "")
        category = entity.get("category", "")
        start = entity.get("start", -1)
        end = entity.get("end", -1)

        if not text or not category:
            return None

        # Verify or find the text in original
        if start >= 0 and end > start:
            # Check if positions are correct
            if original_text[start:end] == text:
                return entity

        # Try to find the text in the original
        pos = original_text.find(text)
        if pos >= 0:
            return {
                "text": text,
                "category": category,
                "start": pos,
                "end": pos + len(text),
            }

        return None

    async def detect_entities(
        self,
        text: str,
        categories: list[PiiCategory] | None = None,
        min_confidence: float = 0.5,
    ) -> list[NerDetection]:
        """
        Detect PII entities using LLM.

        Args:
            text: The text to analyze
            categories: Optional filter for specific categories
            min_confidence: Minimum confidence threshold (LLM always returns 0.9)

        Returns:
            List of detected entities
        """
        if not text or not text.strip():
            return []

        # For very long texts, process in chunks
        max_chunk_size = 4000  # Characters
        if len(text) > max_chunk_size:
            return await self._detect_chunked(text, categories, min_confidence)

        try:
            # Call LLM
            prompt = f"Analiza el siguiente texto y detecta todas las entidades PII:\n\n{text}"
            response = await self._call_ollama(prompt)

            # Parse response
            raw_entities = self._parse_llm_response(response, text)

            detections: list[NerDetection] = []
            for raw_entity in raw_entities:
                # Validate and correct positions
                validated = self._validate_entity(raw_entity, text)
                if not validated:
                    continue

                # Map category
                category_str = validated["category"]
                category_result = PiiCategory.from_string(category_str)
                if category_result.is_err():
                    continue
                category = category_result.unwrap()

                # Filter by requested categories
                if categories and category not in categories:
                    continue

                # Create span
                span_result = TextSpan.create(
                    validated["start"],
                    validated["end"],
                    validated["text"],
                )
                if span_result.is_err():
                    continue

                # LLM detections get high confidence (0.9)
                conf_result = ConfidenceScore.create(0.9)
                if conf_result.is_err():
                    continue

                detections.append(
                    NerDetection(
                        category=category,
                        value=validated["text"],
                        span=span_result.unwrap(),
                        confidence=conf_result.unwrap(),
                    )
                )

            return detections

        except Exception as e:
            # Log error but don't fail - return empty list
            print(f"[OllamaNerAdapter] Error: {e}")
            return []

    async def _detect_chunked(
        self,
        text: str,
        categories: list[PiiCategory] | None,
        min_confidence: float,
    ) -> list[NerDetection]:
        """Process long text in chunks."""
        chunk_size = 3500
        overlap = 200
        all_detections: list[NerDetection] = []
        seen_spans: set[tuple[int, int]] = set()

        pos = 0
        while pos < len(text):
            chunk_end = min(pos + chunk_size, len(text))
            chunk = text[pos:chunk_end]

            # Detect in chunk
            chunk_detections = await self.detect_entities(
                chunk, categories, min_confidence
            )

            # Adjust positions and deduplicate
            for detection in chunk_detections:
                adjusted_start = detection.span.start + pos
                adjusted_end = detection.span.end + pos

                span_key = (adjusted_start, adjusted_end)
                if span_key in seen_spans:
                    continue
                seen_spans.add(span_key)

                # Create new detection with adjusted span
                span_result = TextSpan.create(
                    adjusted_start, adjusted_end, detection.value
                )
                if span_result.is_ok():
                    all_detections.append(
                        NerDetection(
                            category=detection.category,
                            value=detection.value,
                            span=span_result.unwrap(),
                            confidence=detection.confidence,
                        )
                    )

            pos += chunk_size - overlap

        return all_detections

    async def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            if self._use_powershell:
                result = self._call_via_powershell("/api/tags")
                return bool(result and "models" in result)
            else:
                client = await self._ensure_client()
                response = await client.get(
                    f"{self._ollama_host}/api/tags",
                    timeout=5.0,
                )
                return response.status_code == 200
        except Exception:
            return False

    async def get_model_info(self) -> dict:
        """Get information about the LLM configuration."""
        available = await self.is_available()
        return {
            "type": "ollama_llm",
            "model": self._model_name,
            "host": self._ollama_host,
            "is_available": available,
            "temperature": self._temperature,
            "architecture": "pre-presidio",
        }
