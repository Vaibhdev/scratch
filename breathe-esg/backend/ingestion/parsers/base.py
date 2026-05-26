"""
Abstract base parser for emissions data ingestion.

Each source type (SAP, utility, travel) implements a concrete parser
that inherits from BaseParser. The base class handles:
- File hashing for duplicate detection
- IngestionLog lifecycle management
- Per-row error collection
- Audit trail creation
"""

import hashlib
from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation
from core.models import IngestionLog, ActivityRecord, AuditEntry, Client


class ParseError:
    """Structured error for a single row parsing failure."""

    def __init__(self, row: int, field: str, message: str):
        self.row = row
        self.field = field
        self.message = message

    def to_dict(self):
        return {"row": self.row, "field": self.field, "error": self.message}


class BaseParser(ABC):
    """
    Abstract parser that orchestrates the ingest pipeline:
    1. Hash the file for duplicate detection
    2. Create an IngestionLog
    3. Parse rows (subclass responsibility)
    4. Normalize each row (subclass responsibility)
    5. Create ActivityRecords + AuditEntries
    6. Update IngestionLog with results
    """

    source_type: str = ""  # Override in subclass

    def __init__(self, client: Client, uploaded_by: str = "system"):
        self.client = client
        self.uploaded_by = uploaded_by
        self.errors: list[ParseError] = []
        self.records_created: list[ActivityRecord] = []

    def compute_file_hash(self, file_content: bytes) -> str:
        """SHA-256 hash of file contents for duplicate detection."""
        return hashlib.sha256(file_content).hexdigest()

    def ingest(self, file_name: str, file_content: bytes) -> IngestionLog:
        """
        Main entry point. Parses the file and returns an IngestionLog
        summarizing what happened.
        """
        file_hash = self.compute_file_hash(file_content)

        # Check for duplicate uploads
        existing = IngestionLog.objects.filter(
            client=self.client,
            file_hash_sha256=file_hash,
            status=IngestionLog.Status.COMPLETED,
        ).first()
        if existing:
            # Return the existing log rather than re-processing
            return existing

        # Create ingestion log
        log = IngestionLog.objects.create(
            client=self.client,
            source_type=self.source_type,
            file_name=file_name,
            file_hash_sha256=file_hash,
            status=IngestionLog.Status.PROCESSING,
            uploaded_by=self.uploaded_by,
        )

        try:
            # Subclass parses the raw file into row dicts
            raw_rows = self.parse_file(file_content)
            log.total_rows = len(raw_rows)
            log.field_mapping = self.get_field_mapping()

            # Process each row
            for idx, raw_row in enumerate(raw_rows, start=1):
                try:
                    record = self.normalize_row(raw_row, idx, log)
                    if record:
                        self.records_created.append(record)
                except Exception as e:
                    self.errors.append(
                        ParseError(row=idx, field="*", message=str(e))
                    )

            # Bulk create records and audit entries
            if self.records_created:
                ActivityRecord.objects.bulk_create(self.records_created)
                audit_entries = [
                    AuditEntry(
                        activity_record=record,
                        action=AuditEntry.Action.CREATED,
                        changed_by=self.uploaded_by,
                    )
                    for record in self.records_created
                ]
                AuditEntry.objects.bulk_create(audit_entries)

            # Update log
            log.successful_rows = len(self.records_created)
            log.failed_rows = len(self.errors)
            log.validation_errors = [e.to_dict() for e in self.errors]
            log.status = IngestionLog.Status.COMPLETED
            log.save()

        except Exception as e:
            log.status = IngestionLog.Status.FAILED
            log.validation_errors = [{"row": 0, "field": "*", "error": str(e)}]
            log.save()

        return log

    @abstractmethod
    def parse_file(self, file_content: bytes) -> list[dict]:
        """Parse raw file bytes into a list of row dictionaries."""
        pass

    @abstractmethod
    def normalize_row(
        self, raw_row: dict, row_number: int, log: IngestionLog
    ) -> ActivityRecord | None:
        """
        Convert a raw row dict into a normalized ActivityRecord.
        Should return None if the row should be skipped.
        Should raise an exception if the row is invalid.
        """
        pass

    @abstractmethod
    def get_field_mapping(self) -> dict:
        """Return the column name mapping used by this parser."""
        pass

    @staticmethod
    def safe_decimal(value, field_name: str = "value") -> Decimal:
        """Safely convert a value to Decimal, handling SAP integer-encoded amounts."""
        if value is None or str(value).strip() == "":
            raise ValueError(f"Empty value for {field_name}")
        try:
            cleaned = str(value).strip().replace(",", "")
            return Decimal(cleaned)
        except InvalidOperation:
            raise ValueError(f"Cannot convert '{value}' to number for {field_name}")
