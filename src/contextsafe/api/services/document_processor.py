"""
Document processing logic.

Extracted from routes/documents.py for cohesion.
Handles NER detection, anonymization, and glossary updates.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from uuid import UUID, uuid4

from contextsafe.api.services.ner_registry import (
    get_anonymization_service,
    get_ner_service,
)
from contextsafe.api.session_manager import session_manager
from contextsafe.api.websocket.progress_handler import progress_handler

logger = logging.getLogger(__name__)

# Processing tasks tracking
processing_tasks: dict[str, asyncio.Task] = {}


async def process_document_real(document_id: str, project_id: str, session_id: str):
    """
    Process document using real NER detection and anonymization.

    Uses Presidio with Spanish recognizers for PII detection.
    Broadcasts progress updates via WebSocket.
    """
    doc = session_manager.get_document(session_id, document_id)
    if not doc:
        return

    doc_uuid = UUID(document_id)

    try:
        # Stage 1: Ingesting (0-10%)
        session_manager.update_document(session_id, document_id, state="ingesting", progress=0.0, current_entity="Iniciando procesamiento...")
        await progress_handler.send_progress(doc_uuid, "ingesting", 0.0)

        # Get text content
        original_text = doc.content or ""
        if not original_text:
            session_manager.update_document(session_id, document_id, state="error", progress=0.0, error="No text content to process")
            await progress_handler.send_error(doc_uuid, "No text content to process")
            return

        session_manager.update_document(session_id, document_id, progress=0.1, current_entity="Texto extraído")
        await progress_handler.send_progress(doc_uuid, "ingesting", 0.1)

        # Stage 2: Detecting PII entities (10-40%)
        session_manager.update_document(session_id, document_id, state="detecting", progress=0.1, current_entity="Detectando entidades PII...")
        await progress_handler.send_progress(doc_uuid, "detecting", 0.1)

        # Progress callback for NER detection
        # NER reports 0-100, we map to 0.1-0.4 range (detecting phase = 30% of total)
        # IMPORTANT: entity_info may contain PII — never store or send it to clients
        async def detection_progress(current: int, total: int, entity_info: str):
            # NER now reports current/100, total=100
            # Map NER's 0-100% to our 10%-40% range
            ner_progress = current / 100.0 if total == 100 else (current / total if total > 0 else 0)
            progress = 0.1 + (0.3 * ner_progress)  # 0.1 to 0.4
            safe_status = f"Analizando texto... {current}%"
            logger.debug(f"[NER-PROGRESS] {document_id}: {current}% -> {progress:.0%}")
            session_manager.update_document(
                session_id, document_id,
                progress=progress,
                current_entity=safe_status
            )
            await progress_handler.send_progress(
                doc_uuid, "detecting", progress,
                current_entity=safe_status
            )

        ner_service = get_ner_service()
        detections = await ner_service.detect_entities(
            text=original_text,
            min_confidence=0.5,
            progress_callback=detection_progress,
        )

        await progress_handler.send_progress(
            doc_uuid, "detecting", 0.4,
            current_entity=f"Detectadas {len(detections)} entidades"
        )

        # Get anonymization level from project
        project_data = session_manager.get_project(session_id, project_id)
        anonymization_level = (project_data.get("anonymization_level", "INTERMEDIATE") if project_data else "INTERMEDIATE").upper()

        # Stage 3: Anonymizing (20-80%)
        # IMPORTANT: We perform anonymization FIRST to get the correct aliases
        # based on the anonymization level (BASIC/INTERMEDIATE/ADVANCED).
        # Previously, aliases were created prematurely with get_or_create_alias()
        # which always created pseudonyms (Persona_001), causing Level 3 (ADVANCED)
        # to never call Ollama because it found "existing" pseudonym aliases.
        session_manager.update_document(session_id, document_id, state="anonymizing")
        await progress_handler.send_progress(doc_uuid, "anonymizing", 0.2)

        anonymization_service = get_anonymization_service()
        is_masking_level = anonymization_level == "BASIC"

        # Progress callback for granular updates during anonymization
        # Level 3 (ADVANCED) makes LLM calls for each entity - this shows progress
        # CRITICAL: Updates BOTH WebSocket AND document for polling-based frontends
        # IMPORTANT: entity_info may contain PII — never store or send it to clients
        async def anonymization_progress(current: int, total: int, entity_info: str):
            if total > 0:
                # Map 0.2-0.9 range for anonymization phase (expanded range for visibility)
                progress = 0.2 + (0.7 * current / total)
                safe_status = f"Anonimizando entidad {current}/{total}"
                logger.debug(f"[PROGRESS] {document_id}: {current}/{total} ({progress:.0%})")
                # Update document progress for polling
                session_manager.update_document(
                    session_id, document_id,
                    progress=progress,
                    current_entity=safe_status
                )
                # Also send via WebSocket for real-time frontends
                await progress_handler.send_progress(
                    doc_uuid, "anonymizing", progress,
                    current_entity=safe_status
                )

        logger.info(f"[ANON] Starting anonymization level={anonymization_level} for {len(detections)} detections")

        # Perform anonymization with the project's level
        # This creates the correct aliases based on strategy:
        # - BASIC: asterisks
        # - INTERMEDIATE: pseudonyms (Persona_001)
        # - ADVANCED: synthetic names via Ollama (Carlos Mendive)
        # Get compute mode for anonymization strategy (GPU/CPU)
        from contextsafe.api.services.compute_state import get_effective_compute_mode
        effective_compute_mode = get_effective_compute_mode()

        result = await anonymization_service.anonymize_text(
            text=original_text,
            detections=detections,
            project_id=project_id,
            level=anonymization_level,
            progress_callback=anonymization_progress,
            compute_mode=effective_compute_mode,
        )

        logger.info(f"[ANON] Completed anonymization - {len(result.replacements)} replacements")
        await progress_handler.send_progress(doc_uuid, "anonymizing", 0.6)

        # Now build entities list using the ACTUAL aliases from anonymization result
        # This ensures Level 3 shows synthetic names, not pseudonyms
        total_detections = len(detections)
        entities = []

        # Build a lookup map from (start, end, value) -> alias from replacements
        replacement_map: dict[tuple[int, int, str], str] = {}
        for repl in result.replacements:
            key = (repl.start_offset, repl.end_offset, repl.original_value)
            replacement_map[key] = repl.alias

        for i, detection in enumerate(detections):
            category = detection.category.value
            original_value = detection.value

            # Look up the actual alias used in anonymization
            key = (detection.span.start, detection.span.end, original_value)
            alias = replacement_map.get(key)

            if alias is None:
                # Detection was filtered (overlapping) - still show with placeholder
                if is_masking_level:
                    alias = "*" * max(len(original_value), 5)
                else:
                    # Should not happen, but fallback to pseudonym format
                    alias = f"[{category[:3]}]"

            entities.append({
                "id": str(uuid4()),
                "document_id": document_id,
                "category": category,
                "original_text": original_value,
                "alias": alias,
                "confidence": round(detection.confidence.value, 2),
                "start_offset": detection.span.start,
                "end_offset": detection.span.end,
            })

        # Progress already reported via callback during anonymize_text()

        # Store entities in document (0.6 -> 0.7)
        await progress_handler.send_progress(
            doc_uuid, "anonymizing", 0.65,
            current_entity="Guardando entidades detectadas"
        )
        session_manager.update_document(session_id, document_id, detected_pii=entities)

        # Store anonymized text (0.7 -> 0.8)
        await progress_handler.send_progress(
            doc_uuid, "anonymizing", 0.75,
            current_entity="Guardando texto anonimizado"
        )
        session_manager.update_document(
            session_id, document_id,
            anonymized={"original": original_text, "anonymized": result.anonymized_text}
        )

        # Update glossary for project (90-100%)
        # NOTE: ALL levels create glossary entries:
        # - BASIC: For audit/manual editing only (not for reversibility - shows asterisks)
        # - INTERMEDIATE/ADVANCED: For reversibility and editing
        await progress_handler.send_progress(
            doc_uuid, "anonymizing", 0.9,
            current_entity="Actualizando glosario"
        )

        # Get current glossary
        current_glossary = session_manager.get_glossary(session_id, project_id)

        # Count occurrences of each alias from the ACTUAL replacements
        # (not pre-calculated entities, which may differ from MaskingStrategy output)
        alias_counts: dict[str, int] = {}
        alias_data: dict[str, dict] = {}
        for replacement in result.replacements:
            alias = replacement.alias  # The ACTUAL alias used in anonymized text
            if alias not in alias_counts:
                alias_counts[alias] = 0
                alias_data[alias] = {
                    "original_text": replacement.original_value,
                    "alias": alias,
                    "category": replacement.category,
                    "confidence": replacement.confidence,
                }
            alias_counts[alias] += 1

        existing_aliases = {e["alias"] for e in current_glossary}
        for alias, count in alias_counts.items():
            if alias not in existing_aliases:
                entity = alias_data[alias]
                session_manager.add_glossary_entry(session_id, project_id, {
                    "id": str(uuid4()),
                    "original_text": entity["original_text"],
                    "alias": entity["alias"],
                    "category": entity["category"],
                    "occurrences": count,
                    "created_at": datetime.utcnow().isoformat(),
                    # BASIC level: mark as not reversible (audit only)
                    "reversible": not is_masking_level,
                    "masking_level": anonymization_level,
                })
                existing_aliases.add(alias)
            else:
                # Update occurrence count for existing entry
                glossary = session_manager.get_glossary(session_id, project_id)
                for entry in glossary:
                    if entry["alias"] == alias:
                        entry["occurrences"] = entry.get("occurrences", 0) + count
                        break

        # Complete
        session_manager.update_document(
            session_id, document_id,
            state="completed",
            entity_count=len(entities)
        )

        # Send completion
        await progress_handler.send_complete(doc_uuid)
        logger.info(f"Document {document_id} processed: {len(entities)} entities detected")

    except Exception as e:
        session_manager.update_document(
            session_id, document_id,
            state="error",
            error=str(e)
        )
        await progress_handler.send_error(doc_uuid, str(e))
        logger.error(f"Error processing document {document_id}: {e}")
    finally:
        # Prevent memory leak: remove completed/failed task reference
        processing_tasks.pop(document_id, None)
