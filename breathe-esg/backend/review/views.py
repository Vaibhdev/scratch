"""
Review dashboard API views.
Provides endpoints for analysts to view, filter, and approve/reject activity records.
"""

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from core.models import ActivityRecord, AuditEntry
from core.serializers import ActivityRecordListSerializer, ActivityRecordDetailSerializer


class RecordPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


@api_view(["GET"])
def record_list(request):
    """
    List activity records with filtering.

    Query params:
    - source_type: SAP_PROCUREMENT | UTILITY_ELECTRICITY | TRAVEL_CONCUR
    - ghg_scope: SCOPE_1 | SCOPE_2 | SCOPE_3
    - category: FUEL_COMBUSTION | ELECTRICITY | FLIGHT | HOTEL | GROUND_TRANSPORT
    - review_status: PENDING | APPROVED | FLAGGED | REJECTED
    - client_id: UUID
    - date_from: YYYY-MM-DD
    - date_to: YYYY-MM-DD
    - search: text search in description
    """
    queryset = ActivityRecord.objects.select_related(
        "client", "ingestion_log"
    ).all()

    # Apply filters
    filters = {
        "source_type": request.query_params.get("source_type"),
        "ghg_scope": request.query_params.get("ghg_scope"),
        "category": request.query_params.get("category"),
        "review_status": request.query_params.get("review_status"),
        "client_id": request.query_params.get("client_id"),
    }

    for field, value in filters.items():
        if value:
            queryset = queryset.filter(**{field: value})

    date_from = request.query_params.get("date_from")
    if date_from:
        queryset = queryset.filter(activity_date__gte=date_from)

    date_to = request.query_params.get("date_to")
    if date_to:
        queryset = queryset.filter(activity_date__lte=date_to)

    search = request.query_params.get("search")
    if search:
        queryset = queryset.filter(description__icontains=search)

    paginator = RecordPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = ActivityRecordListSerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(["GET"])
def record_detail(request, pk):
    """Get full details of an activity record including audit trail."""
    try:
        record = ActivityRecord.objects.select_related(
            "client", "ingestion_log"
        ).prefetch_related("audit_entries").get(id=pk)
    except ActivityRecord.DoesNotExist:
        return Response(
            {"error": "Record not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = ActivityRecordDetailSerializer(record)
    return Response(serializer.data)


@api_view(["PATCH"])
def record_review(request, pk):
    """
    Update the review status of an activity record.

    Body:
    - review_status: APPROVED | FLAGGED | REJECTED
    - review_notes: optional notes explaining the decision
    - reviewed_by: name of the reviewer
    """
    try:
        record = ActivityRecord.objects.get(id=pk)
    except ActivityRecord.DoesNotExist:
        return Response(
            {"error": "Record not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    new_status = request.data.get("review_status")
    if new_status not in dict(ActivityRecord.ReviewStatus.choices):
        return Response(
            {"error": f"Invalid review_status: '{new_status}'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    old_status = record.review_status
    record.review_status = new_status
    record.reviewed_by = request.data.get("reviewed_by", "analyst")
    record.reviewed_at = timezone.now()
    record.review_notes = request.data.get("review_notes", "")
    record.save()

    # Create audit entry
    action_map = {
        "APPROVED": AuditEntry.Action.APPROVED,
        "REJECTED": AuditEntry.Action.REJECTED,
        "FLAGGED": AuditEntry.Action.FLAGGED,
        "PENDING": AuditEntry.Action.STATUS_CHANGED,
    }
    AuditEntry.objects.create(
        activity_record=record,
        action=action_map.get(new_status, AuditEntry.Action.STATUS_CHANGED),
        field_changed="review_status",
        old_value=old_status,
        new_value=new_status,
        changed_by=record.reviewed_by,
    )

    serializer = ActivityRecordDetailSerializer(record)
    return Response(serializer.data)


@api_view(["POST"])
def bulk_review(request):
    """
    Bulk update review status for multiple records.

    Body:
    - record_ids: list of UUIDs
    - review_status: APPROVED | FLAGGED | REJECTED
    - review_notes: optional
    - reviewed_by: name of reviewer
    """
    record_ids = request.data.get("record_ids", [])
    new_status = request.data.get("review_status")
    reviewed_by = request.data.get("reviewed_by", "analyst")
    review_notes = request.data.get("review_notes", "")

    if not record_ids:
        return Response(
            {"error": "No record_ids provided"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if new_status not in dict(ActivityRecord.ReviewStatus.choices):
        return Response(
            {"error": f"Invalid review_status: '{new_status}'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    records = ActivityRecord.objects.filter(id__in=record_ids)
    updated_count = 0

    audit_entries = []
    for record in records:
        old_status = record.review_status
        record.review_status = new_status
        record.reviewed_by = reviewed_by
        record.reviewed_at = timezone.now()
        record.review_notes = review_notes
        record.save()
        updated_count += 1

        action_map = {
            "APPROVED": AuditEntry.Action.APPROVED,
            "REJECTED": AuditEntry.Action.REJECTED,
            "FLAGGED": AuditEntry.Action.FLAGGED,
            "PENDING": AuditEntry.Action.STATUS_CHANGED,
        }
        audit_entries.append(
            AuditEntry(
                activity_record=record,
                action=action_map.get(new_status, AuditEntry.Action.STATUS_CHANGED),
                field_changed="review_status",
                old_value=old_status,
                new_value=new_status,
                changed_by=reviewed_by,
            )
        )

    AuditEntry.objects.bulk_create(audit_entries)

    return Response({"updated": updated_count})


@api_view(["GET"])
def record_summary(request):
    """
    Aggregation stats for the dashboard.
    Returns counts by scope, source type, category, and review status.
    """
    client_id = request.query_params.get("client_id")
    queryset = ActivityRecord.objects.all()
    if client_id:
        queryset = queryset.filter(client_id=client_id)

    total = queryset.count()

    by_scope = dict(
        queryset.values_list("ghg_scope")
        .annotate(count=Count("id"))
        .values_list("ghg_scope", "count")
    )

    by_source = dict(
        queryset.values_list("source_type")
        .annotate(count=Count("id"))
        .values_list("source_type", "count")
    )

    by_category = dict(
        queryset.values_list("category")
        .annotate(count=Count("id"))
        .values_list("category", "count")
    )

    by_status = dict(
        queryset.values_list("review_status")
        .annotate(count=Count("id"))
        .values_list("review_status", "count")
    )

    return Response(
        {
            "total": total,
            "by_scope": by_scope,
            "by_source": by_source,
            "by_category": by_category,
            "by_review_status": by_status,
        }
    )
