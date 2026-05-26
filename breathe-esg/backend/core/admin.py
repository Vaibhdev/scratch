from django.contrib import admin
from .models import Client, IngestionLog, ActivityRecord, AuditEntry


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["name", "industry", "country", "created_at"]
    search_fields = ["name"]


@admin.register(IngestionLog)
class IngestionLogAdmin(admin.ModelAdmin):
    list_display = [
        "file_name",
        "client",
        "source_type",
        "status",
        "total_rows",
        "successful_rows",
        "failed_rows",
        "uploaded_at",
    ]
    list_filter = ["source_type", "status", "client"]


@admin.register(ActivityRecord)
class ActivityRecordAdmin(admin.ModelAdmin):
    list_display = [
        "category",
        "activity_date",
        "quantity",
        "original_unit",
        "ghg_scope",
        "review_status",
        "client",
    ]
    list_filter = ["source_type", "ghg_scope", "category", "review_status", "client"]
    search_fields = ["description"]


@admin.register(AuditEntry)
class AuditEntryAdmin(admin.ModelAdmin):
    list_display = ["action", "activity_record", "changed_by", "changed_at"]
    list_filter = ["action"]
