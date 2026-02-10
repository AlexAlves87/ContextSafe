"""
WebSocket handler for progress updates.

Streams real-time processing progress to frontend.

Traceability:
- Contract: CNT-T4-PROGRESS-WS-001
- Binding: UI-BIND-003 (ProcessingProgress)
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect


logger = logging.getLogger(__name__)

# Message types matching frontend expectations
MessageType = Literal["progress", "complete", "error", "connected", "ping"]
ProcessingStage = Literal["ingesting", "detecting", "anonymizing"]


class WebSocketMessage:
    """WebSocket message matching frontend interface."""

    @staticmethod
    def progress(
        document_id: UUID,
        stage: ProcessingStage,
        progress: float,
        current_entity: Optional[str] = None,
    ) -> str:
        """Create progress message."""
        msg = {
            "type": "progress",
            "documentId": str(document_id),
            "stage": stage,
            "progress": progress,
        }
        if current_entity:
            msg["currentEntity"] = current_entity
        return json.dumps(msg)

    @staticmethod
    def complete(document_id: UUID) -> str:
        """Create complete message."""
        return json.dumps({
            "type": "complete",
            "documentId": str(document_id),
        })

    @staticmethod
    def error(document_id: UUID, message: str) -> str:
        """Create error message."""
        return json.dumps({
            "type": "error",
            "documentId": str(document_id),
            "message": message,
        })

    @staticmethod
    def connected(document_id: UUID) -> str:
        """Create connected acknowledgment."""
        return json.dumps({
            "type": "connected",
            "documentId": str(document_id),
        })

    @staticmethod
    def ping() -> str:
        """Create ping message."""
        return json.dumps({"type": "ping"})


class ProgressWebSocketHandler:
    """
    WebSocket handler for streaming progress updates.

    Features:
    - Connection management per document
    - Progress broadcasting
    - Graceful disconnect handling
    """

    def __init__(self) -> None:
        """Initialize the handler."""
        self._active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, document_id: UUID) -> None:
        """
        Accept WebSocket connection and subscribe to document events.

        Args:
            websocket: The WebSocket connection
            document_id: Document to monitor
        """
        await websocket.accept()
        connection_id = f"{document_id}:{id(websocket)}"
        self._active_connections[connection_id] = websocket

        # CRITICAL: Log with print to ensure it shows in console
        print(f"[WS-HANDLER] *** CONNECTED *** doc={document_id} conn_id={connection_id}")
        print(f"[WS-HANDLER] Total active connections: {len(self._active_connections)}")
        print(f"[WS-HANDLER] Connection IDs: {list(self._active_connections.keys())}")
        logger.info(f"WebSocket connected for document {document_id}")

        try:
            # Send initial connection acknowledgment
            await websocket.send_text(WebSocketMessage.connected(document_id))

            # Keep connection alive until disconnect
            while True:
                try:
                    # Wait for any message (ping/pong)
                    await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=60.0,
                    )
                except asyncio.TimeoutError:
                    # Send keepalive ping
                    await websocket.send_text(WebSocketMessage.ping())

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for document {document_id}")
        finally:
            self._active_connections.pop(connection_id, None)

    async def send_progress(
        self,
        document_id: UUID,
        stage: ProcessingStage,
        progress: float,
        current_entity: Optional[str] = None,
    ) -> None:
        """
        Send progress update to all connected clients for a document.

        Args:
            document_id: Document being processed
            stage: Processing stage (ingesting, detecting, anonymizing)
            progress: Progress percentage (0.0-1.0)
            current_entity: Currently processing entity (optional)
        """
        # Log connection status for debugging - USE PRINT to guarantee visibility
        conn_count = self.get_document_connections(document_id)
        print(f"[WS-SEND] doc={document_id} stage={stage} progress={progress:.0%} connections={conn_count}")
        print(f"[WS-SEND] All connections: {list(self._active_connections.keys())}")

        if conn_count == 0:
            print(f"[WS-SEND] *** WARNING *** NO CONNECTIONS for document {document_id}!")
            print(f"[WS-SEND] Looking for prefix: {str(document_id)}")

        logger.info(f"[WS] send_progress doc={document_id} stage={stage} progress={progress:.0%} connections={conn_count}")

        message = WebSocketMessage.progress(
            document_id=document_id,
            stage=stage,
            progress=progress,
            current_entity=current_entity,
        )
        await self._broadcast_to_document(document_id, message)

    async def send_complete(self, document_id: UUID) -> None:
        """Send completion message to all connected clients for a document."""
        message = WebSocketMessage.complete(document_id)
        await self._broadcast_to_document(document_id, message)

    async def send_error(self, document_id: UUID, error_message: str) -> None:
        """Send error message to all connected clients for a document."""
        message = WebSocketMessage.error(document_id, error_message)
        await self._broadcast_to_document(document_id, message)

    async def _broadcast_to_document(self, document_id: UUID, message: str) -> None:
        """Broadcast message to all connections for a specific document."""
        dead_connections = []

        for conn_id, websocket in self._active_connections.items():
            if conn_id.startswith(str(document_id)):
                try:
                    await websocket.send_text(message)
                except Exception as e:
                    logger.warning(f"Failed to send to {conn_id}: {e}")
                    dead_connections.append(conn_id)

        # Clean up dead connections
        for conn_id in dead_connections:
            self._active_connections.pop(conn_id, None)

    def get_active_count(self) -> int:
        """Get number of active connections."""
        return len(self._active_connections)

    def get_document_connections(self, document_id: UUID) -> int:
        """Get number of connections for a specific document."""
        prefix = str(document_id)
        return sum(1 for conn_id in self._active_connections if conn_id.startswith(prefix))


# Global handler instance
progress_handler = ProgressWebSocketHandler()


async def handle_progress_websocket(websocket: WebSocket, document_id: UUID) -> None:
    """
    FastAPI WebSocket endpoint handler.

    Args:
        websocket: WebSocket connection
        document_id: Document to monitor
    """
    await progress_handler.connect(websocket, document_id)
