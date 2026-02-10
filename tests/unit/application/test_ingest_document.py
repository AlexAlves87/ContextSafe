"""
Unit tests for IngestDocument use case.

Tests the complete document ingestion workflow including:
- Input validation
- Document creation
- Text extraction
- Event publishing
- Error handling
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from dataclasses import dataclass

from contextsafe.application.use_cases.ingest_document import (
    IngestDocument,
    IngestDocumentRequest,
    IngestDocumentResponse,
)
from contextsafe.domain.shared.errors import DocumentError, InvalidIdError
from contextsafe.domain.shared.types import Ok, Err


@dataclass
class MockTextExtraction:
    """Mock text extraction result."""
    text: str
    format_detected: str


@pytest.mark.asyncio
class TestIngestDocument:
    """Test IngestDocument use case."""

    @pytest.fixture
    def mock_document_repository(self) -> AsyncMock:
        """Create mock document repository."""
        repo = AsyncMock()
        repo.save = AsyncMock()
        return repo

    @pytest.fixture
    def mock_text_extractor(self) -> AsyncMock:
        """Create mock text extractor."""
        extractor = AsyncMock()
        extractor.extract = AsyncMock()
        return extractor

    @pytest.fixture
    def mock_event_publisher(self) -> AsyncMock:
        """Create mock event publisher."""
        publisher = AsyncMock()
        publisher.publish = AsyncMock()
        return publisher

    @pytest.fixture
    def use_case(
        self,
        mock_document_repository: AsyncMock,
        mock_text_extractor: AsyncMock,
        mock_event_publisher: AsyncMock,
    ) -> IngestDocument:
        """Create IngestDocument use case with mocks."""
        return IngestDocument(
            document_repository=mock_document_repository,
            text_extractor=mock_text_extractor,
            event_publisher=mock_event_publisher,
        )

    @pytest.fixture
    def valid_request(self) -> IngestDocumentRequest:
        """Create a valid ingestion request."""
        return IngestDocumentRequest(
            project_id=str(uuid4()),
            content=b"This is a test document with some content.",
            filename="test.txt",
            metadata={"source": "upload"},
        )

    async def test_successful_ingestion(
        self,
        use_case: IngestDocument,
        valid_request: IngestDocumentRequest,
        mock_document_repository: AsyncMock,
        mock_text_extractor: AsyncMock,
        mock_event_publisher: AsyncMock,
    ):
        """Test successful document ingestion flow."""
        # Arrange
        extracted_text = "This is extracted text from the document."
        mock_text_extractor.extract.return_value = MockTextExtraction(
            text=extracted_text,
            format_detected="text/plain",
        )

        # Mock repository to return the saved aggregate
        def mock_save(aggregate):
            return Ok(aggregate)

        mock_document_repository.save = AsyncMock(side_effect=mock_save)

        # Act
        result = await use_case.execute(valid_request)

        # Assert
        assert result.is_ok()
        response = result.unwrap()

        assert isinstance(response, IngestDocumentResponse)
        assert response.project_id == valid_request.project_id
        assert response.filename == valid_request.filename
        assert response.text_length == len(extracted_text)
        assert response.format_detected == "text/plain"
        assert response.state == "INGESTED"

        # Verify text extractor was called
        mock_text_extractor.extract.assert_called_once_with(
            content=valid_request.content,
            filename=valid_request.filename,
            ocr_fallback=True,
        )

        # Verify repository save was called
        assert mock_document_repository.save.call_count == 1

        # Verify event was published
        assert mock_event_publisher.publish.call_count == 1

    async def test_invalid_project_id(
        self,
        use_case: IngestDocument,
        mock_text_extractor: AsyncMock,
    ):
        """Test that invalid project ID is rejected."""
        # Arrange
        request = IngestDocumentRequest(
            project_id="invalid-uuid",
            content=b"Test content",
            filename="test.txt",
        )

        # Act
        result = await use_case.execute(request)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, DocumentError)
        assert "Invalid project ID" in error.detail

        # Verify no text extraction occurred
        mock_text_extractor.extract.assert_not_called()

    async def test_empty_content_rejected(
        self,
        use_case: IngestDocument,
        mock_text_extractor: AsyncMock,
    ):
        """Test that empty content is rejected."""
        # Arrange
        request = IngestDocumentRequest(
            project_id=str(uuid4()),
            content=b"",  # empty
            filename="test.txt",
        )

        # Act
        result = await use_case.execute(request)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, DocumentError)

        # Verify no text extraction occurred
        mock_text_extractor.extract.assert_not_called()

    async def test_invalid_file_extension(
        self,
        use_case: IngestDocument,
        mock_text_extractor: AsyncMock,
    ):
        """Test that invalid file extension is rejected."""
        # Arrange
        request = IngestDocumentRequest(
            project_id=str(uuid4()),
            content=b"Test content",
            filename="test.xyz",  # invalid extension
        )

        # Act
        result = await use_case.execute(request)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, DocumentError)

        # Verify no text extraction occurred
        mock_text_extractor.extract.assert_not_called()

    async def test_text_extraction_failure(
        self,
        use_case: IngestDocument,
        valid_request: IngestDocumentRequest,
        mock_text_extractor: AsyncMock,
        mock_document_repository: AsyncMock,
    ):
        """Test handling of text extraction failure."""
        # Arrange
        mock_text_extractor.extract.side_effect = Exception("OCR failed")

        # Act
        result = await use_case.execute(valid_request)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, DocumentError)
        assert "Text extraction failed" in error.detail

        # Verify document was saved in failed state
        assert mock_document_repository.save.call_count == 1
        saved_aggregate = mock_document_repository.save.call_args[0][0]
        assert saved_aggregate.is_failed is True

    async def test_repository_save_failure(
        self,
        use_case: IngestDocument,
        valid_request: IngestDocumentRequest,
        mock_text_extractor: AsyncMock,
        mock_document_repository: AsyncMock,
    ):
        """Test handling of repository save failure."""
        # Arrange
        mock_text_extractor.extract.return_value = MockTextExtraction(
            text="Extracted text",
            format_detected="text/plain",
        )

        # Mock repository to return error
        mock_document_repository.save = AsyncMock(
            return_value=Err(DocumentError("Database connection failed"))
        )

        # Act
        result = await use_case.execute(valid_request)

        # Assert
        assert result.is_err()
        error = result.unwrap_err()
        assert isinstance(error, DocumentError)
        assert "Database connection failed" in error.detail

    async def test_pdf_document_ingestion(
        self,
        use_case: IngestDocument,
        mock_text_extractor: AsyncMock,
        mock_document_repository: AsyncMock,
    ):
        """Test ingesting a PDF document."""
        # Arrange
        request = IngestDocumentRequest(
            project_id=str(uuid4()),
            content=b"%PDF-1.4...",  # PDF content
            filename="document.pdf",
        )

        mock_text_extractor.extract.return_value = MockTextExtraction(
            text="Extracted PDF content",
            format_detected="application/pdf",
        )

        def mock_save(aggregate):
            return Ok(aggregate)

        mock_document_repository.save = AsyncMock(side_effect=mock_save)

        # Act
        result = await use_case.execute(request)

        # Assert
        assert result.is_ok()
        response = result.unwrap()
        assert response.format_detected == "application/pdf"
        assert response.filename == "document.pdf"

    async def test_image_document_ingestion(
        self,
        use_case: IngestDocument,
        mock_text_extractor: AsyncMock,
        mock_document_repository: AsyncMock,
    ):
        """Test ingesting an image document (requires OCR)."""
        # Arrange
        request = IngestDocumentRequest(
            project_id=str(uuid4()),
            content=b"\x89PNG\r\n\x1a\n...",  # PNG content
            filename="scan.png",
        )

        mock_text_extractor.extract.return_value = MockTextExtraction(
            text="Text extracted via OCR",
            format_detected="image/png",
        )

        def mock_save(aggregate):
            return Ok(aggregate)

        mock_document_repository.save = AsyncMock(side_effect=mock_save)

        # Act
        result = await use_case.execute(request)

        # Assert
        assert result.is_ok()
        response = result.unwrap()
        assert response.format_detected == "image/png"

        # Verify OCR fallback was requested
        mock_text_extractor.extract.assert_called_once()
        call_kwargs = mock_text_extractor.extract.call_args[1]
        assert call_kwargs["ocr_fallback"] is True

    async def test_metadata_preservation(
        self,
        use_case: IngestDocument,
        mock_text_extractor: AsyncMock,
        mock_document_repository: AsyncMock,
    ):
        """Test that metadata is preserved through ingestion."""
        # Arrange
        metadata = {
            "source": "upload",
            "user_id": "user-123",
            "upload_timestamp": "2024-01-15T10:30:00Z",
        }

        request = IngestDocumentRequest(
            project_id=str(uuid4()),
            content=b"Test content",
            filename="test.txt",
            metadata=metadata,
        )

        mock_text_extractor.extract.return_value = MockTextExtraction(
            text="Extracted text",
            format_detected="text/plain",
        )

        def mock_save(aggregate):
            return Ok(aggregate)

        mock_document_repository.save = AsyncMock(side_effect=mock_save)

        # Act
        result = await use_case.execute(request)

        # Assert
        assert result.is_ok()

        # Verify metadata was passed to document creation
        saved_aggregate = mock_document_repository.save.call_args[0][0]
        assert saved_aggregate.document.metadata == metadata

    async def test_event_contains_correct_data(
        self,
        use_case: IngestDocument,
        valid_request: IngestDocumentRequest,
        mock_text_extractor: AsyncMock,
        mock_document_repository: AsyncMock,
        mock_event_publisher: AsyncMock,
    ):
        """Test that published event contains correct data."""
        # Arrange
        extracted_text = "Extracted text content"
        mock_text_extractor.extract.return_value = MockTextExtraction(
            text=extracted_text,
            format_detected="text/plain",
        )

        def mock_save(aggregate):
            return Ok(aggregate)

        mock_document_repository.save = AsyncMock(side_effect=mock_save)

        # Act
        result = await use_case.execute(valid_request)

        # Assert
        assert result.is_ok()

        # Verify event was published with correct data
        mock_event_publisher.publish.assert_called_once()
        event = mock_event_publisher.publish.call_args[0][0]

        assert event.project_id == valid_request.project_id
        assert event.filename == valid_request.filename
        assert event.text_length == len(extracted_text)
        assert event.format_detected == "text/plain"
