"""
Core data models for the Breathe ESG emissions data platform.

Data model design rationale:
- ActivityRecord is the central normalized entity: every source (SAP, utility, travel)
  produces activity records that share a common shape (date, quantity, unit, scope, category).
- raw_data preserves the verbatim original row for audit/traceability.
- source_metadata stores source-specific fields (SAP plant codes, meter IDs, airport codes)
  that don't fit the normalized schema but are essential context.
- Unit normalization stores both original and converted values so auditors can trace back.
- AuditEntry tracks every state change for compliance.
"""

import uuid
from django.db import models
from django.utils import timezone


class Client(models.Model):
    """
    Tenant entity. Every ingested record belongs to a client.
    Multi-tenancy is column-based: querysets filter by client_id.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    industry = models.CharField(max_length=100, blank=True, default="")
    country = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class IngestionLog(models.Model):
    """
    Tracks each file upload: what was uploaded, parsing results, errors.
    Enables re-upload detection via file_hash and detailed error inspection.
    """

    class SourceType(models.TextChoices):
        SAP_PROCUREMENT = "SAP_PROCUREMENT", "SAP Fuel & Procurement"
        UTILITY_ELECTRICITY = "UTILITY_ELECTRICITY", "Utility Electricity"
        TRAVEL_CONCUR = "TRAVEL_CONCUR", "Corporate Travel (Concur)"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="ingestion_logs"
    )
    source_type = models.CharField(max_length=30, choices=SourceType.choices)
    file_name = models.CharField(max_length=255)
    file_hash_sha256 = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="SHA-256 hash for duplicate detection",
    )
    total_rows = models.IntegerField(default=0)
    successful_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    field_mapping = models.JSONField(
        default=dict,
        blank=True,
        help_text="Mapping from original column names to normalized field names",
    )
    validation_errors = models.JSONField(
        default=list,
        blank=True,
        help_text="Per-row validation errors: [{row: int, field: str, error: str}]",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    uploaded_by = models.CharField(max_length=100, default="system")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return f"{self.source_type} — {self.file_name} ({self.status})"


class ActivityRecord(models.Model):
    """
    The core normalized record representing an emissions-related activity.

    Every source maps to this shape:
    - SAP procurement → fuel purchase (Scope 1)
    - Utility electricity → energy consumption (Scope 2)
    - Corporate travel → flights/hotels/ground transport (Scope 3)

    Design decisions:
    - raw_data: verbatim JSON of the original row/entry, never modified after creation.
    - source_metadata: structured source-specific data (plant codes, meter IDs, routes).
    - Dual units: original_unit + normalized_unit with normalized_quantity for conversions.
    """

    class GHGScope(models.TextChoices):
        SCOPE_1 = "SCOPE_1", "Scope 1 — Direct Emissions"
        SCOPE_2 = "SCOPE_2", "Scope 2 — Purchased Energy"
        SCOPE_3 = "SCOPE_3", "Scope 3 — Other Indirect"

    class Category(models.TextChoices):
        FUEL_COMBUSTION = "FUEL_COMBUSTION", "Fuel Combustion"
        ELECTRICITY = "ELECTRICITY", "Electricity"
        FLIGHT = "FLIGHT", "Flight"
        HOTEL = "HOTEL", "Hotel"
        GROUND_TRANSPORT = "GROUND_TRANSPORT", "Ground Transport"

    class ReviewStatus(models.TextChoices):
        PENDING = "PENDING", "Pending Review"
        APPROVED = "APPROVED", "Approved"
        FLAGGED = "FLAGGED", "Flagged for Review"
        REJECTED = "REJECTED", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="activity_records"
    )
    ingestion_log = models.ForeignKey(
        IngestionLog, on_delete=models.CASCADE, related_name="records"
    )
    source_type = models.CharField(
        max_length=30, choices=IngestionLog.SourceType.choices
    )
    source_row_number = models.IntegerField(
        help_text="Row/entry index in the original file (1-based)"
    )

    # Raw data preservation — the original row exactly as received
    raw_data = models.JSONField(
        help_text="Verbatim original row/entry from source file"
    )

    # GHG Protocol classification
    ghg_scope = models.CharField(max_length=10, choices=GHGScope.choices)
    category = models.CharField(max_length=30, choices=Category.choices)

    # Temporal fields
    activity_date = models.DateField(
        help_text="Primary date of the activity"
    )
    period_start = models.DateField(
        null=True,
        blank=True,
        help_text="Start of billing/reporting period (for utility data)",
    )
    period_end = models.DateField(
        null=True,
        blank=True,
        help_text="End of billing/reporting period",
    )

    # Quantity and units — dual storage for traceability
    quantity = models.DecimalField(
        max_digits=16,
        decimal_places=4,
        help_text="Quantity in original units",
    )
    original_unit = models.CharField(
        max_length=20,
        help_text="Unit as it appeared in the source (e.g., L, TO, kWh, GAL)",
    )
    normalized_quantity = models.DecimalField(
        max_digits=16,
        decimal_places=4,
        help_text="Quantity converted to normalized unit",
    )
    normalized_unit = models.CharField(
        max_length=20,
        help_text="Standardized unit (e.g., liters, kg, kWh, km, room-nights)",
    )

    # Description for human readability
    description = models.TextField(
        blank=True,
        default="",
        help_text="Human-readable summary of this activity",
    )

    # Source-specific metadata (SAP plant, meter ID, airport codes, etc.)
    source_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Source-specific fields: plant codes, meter IDs, flight routes, etc.",
    )

    # Review workflow
    review_status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.PENDING,
    )
    reviewed_by = models.CharField(max_length=100, blank=True, default="")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True, default="")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-activity_date", "-created_at"]
        indexes = [
            models.Index(fields=["client", "source_type"]),
            models.Index(fields=["client", "ghg_scope"]),
            models.Index(fields=["client", "review_status"]),
            models.Index(fields=["activity_date"]),
            models.Index(fields=["ingestion_log"]),
        ]

    def __str__(self):
        return f"{self.category} | {self.quantity} {self.original_unit} | {self.activity_date}"


class AuditEntry(models.Model):
    """
    Immutable log of every state change on an ActivityRecord.
    Supports compliance requirements: who changed what, when, and why.
    """

    class Action(models.TextChoices):
        CREATED = "CREATED", "Created"
        EDITED = "EDITED", "Edited"
        STATUS_CHANGED = "STATUS_CHANGED", "Status Changed"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        FLAGGED = "FLAGGED", "Flagged"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity_record = models.ForeignKey(
        ActivityRecord, on_delete=models.CASCADE, related_name="audit_entries"
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    field_changed = models.CharField(max_length=100, blank=True, default="")
    old_value = models.TextField(blank=True, default="")
    new_value = models.TextField(blank=True, default="")
    changed_by = models.CharField(max_length=100, default="system")
    changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.action} on {self.activity_record_id} by {self.changed_by}"
