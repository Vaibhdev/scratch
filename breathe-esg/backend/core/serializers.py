"""Serializers for the core data models."""

from rest_framework import serializers
from .models import Client, IngestionLog, ActivityRecord, AuditEntry


class ClientSerializer(serializers.ModelSerializer):
    record_count = serializers.SerializerMethodField()

    class Meta:
        model = Client
        fields = ["id", "name", "industry", "country", "created_at", "record_count"]

    def get_record_count(self, obj):
        return obj.activity_records.count()


class IngestionLogSerializer(serializers.ModelSerializer):
    client_name = serializers.CharField(source="client.name", read_only=True)
    source_type_display = serializers.CharField(
        source="get_source_type_display", read_only=True
    )
    status_display = serializers.CharField(
        source="get_status_display", read_only=True
    )

    class Meta:
        model = IngestionLog
        fields = [
            "id",
            "client",
            "client_name",
            "source_type",
            "source_type_display",
            "file_name",
            "file_hash_sha256",
            "total_rows",
            "successful_rows",
            "failed_rows",
            "field_mapping",
            "validation_errors",
            "status",
            "status_display",
            "uploaded_by",
            "uploaded_at",
        ]


class AuditEntrySerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(
        source="get_action_display", read_only=True
    )

    class Meta:
        model = AuditEntry
        fields = [
            "id",
            "action",
            "action_display",
            "field_changed",
            "old_value",
            "new_value",
            "changed_by",
            "changed_at",
        ]


class ActivityRecordListSerializer(serializers.ModelSerializer):
    """Compact serializer for list views — excludes heavy JSON fields."""

    client_name = serializers.CharField(source="client.name", read_only=True)
    source_type_display = serializers.CharField(
        source="get_source_type_display", read_only=True
    )
    ghg_scope_display = serializers.CharField(
        source="get_ghg_scope_display", read_only=True
    )
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )
    review_status_display = serializers.CharField(
        source="get_review_status_display", read_only=True
    )

    class Meta:
        model = ActivityRecord
        fields = [
            "id",
            "client",
            "client_name",
            "source_type",
            "source_type_display",
            "ghg_scope",
            "ghg_scope_display",
            "category",
            "category_display",
            "activity_date",
            "period_start",
            "period_end",
            "quantity",
            "original_unit",
            "normalized_quantity",
            "normalized_unit",
            "description",
            "review_status",
            "review_status_display",
            "reviewed_by",
            "reviewed_at",
            "created_at",
        ]


class ActivityRecordDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail views — includes raw_data, metadata, audit trail."""

    client_name = serializers.CharField(source="client.name", read_only=True)
    source_type_display = serializers.CharField(
        source="get_source_type_display", read_only=True
    )
    ghg_scope_display = serializers.CharField(
        source="get_ghg_scope_display", read_only=True
    )
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )
    review_status_display = serializers.CharField(
        source="get_review_status_display", read_only=True
    )
    audit_entries = AuditEntrySerializer(many=True, read_only=True)
    ingestion_file = serializers.CharField(
        source="ingestion_log.file_name", read_only=True
    )

    class Meta:
        model = ActivityRecord
        fields = [
            "id",
            "client",
            "client_name",
            "ingestion_log",
            "ingestion_file",
            "source_type",
            "source_type_display",
            "source_row_number",
            "raw_data",
            "ghg_scope",
            "ghg_scope_display",
            "category",
            "category_display",
            "activity_date",
            "period_start",
            "period_end",
            "quantity",
            "original_unit",
            "normalized_quantity",
            "normalized_unit",
            "description",
            "source_metadata",
            "review_status",
            "review_status_display",
            "reviewed_by",
            "reviewed_at",
            "review_notes",
            "created_at",
            "updated_at",
            "audit_entries",
        ]
