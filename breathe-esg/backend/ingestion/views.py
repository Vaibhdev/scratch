"""
Ingestion API views — file upload and ingestion history.
"""

import hashlib
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import status

from core.models import Client, IngestionLog
from core.serializers import IngestionLogSerializer
from .parsers.sap_procurement import SAPProcurementParser
from .parsers.utility_electricity import UtilityElectricityParser
from .parsers.travel_concur import TravelConcurParser


# Registry of source type → parser class
PARSER_REGISTRY = {
    IngestionLog.SourceType.SAP_PROCUREMENT: SAPProcurementParser,
    IngestionLog.SourceType.UTILITY_ELECTRICITY: UtilityElectricityParser,
    IngestionLog.SourceType.TRAVEL_CONCUR: TravelConcurParser,
}


@api_view(["POST"])
@parser_classes([MultiPartParser])
def upload_file(request):
    """
    Upload a data file for ingestion.

    Required fields:
    - file: The data file (CSV or JSON)
    - source_type: SAP_PROCUREMENT | UTILITY_ELECTRICITY | TRAVEL_CONCUR
    - client_id: UUID of the client

    Returns the IngestionLog with parsing results.
    """
    # Validate required fields
    uploaded_file = request.FILES.get("file")
    source_type = request.data.get("source_type", "")
    client_id = request.data.get("client_id", "")

    if not uploaded_file:
        return Response(
            {"error": "No file provided"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if source_type not in PARSER_REGISTRY:
        return Response(
            {
                "error": f"Invalid source_type: '{source_type}'. "
                f"Must be one of: {', '.join(PARSER_REGISTRY.keys())}"
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        client = Client.objects.get(id=client_id)
    except (Client.DoesNotExist, ValueError):
        return Response(
            {"error": f"Client not found: '{client_id}'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Read file content
    file_content = uploaded_file.read()

    # Instantiate appropriate parser and run ingestion
    parser_class = PARSER_REGISTRY[source_type]
    parser = parser_class(client=client, uploaded_by="analyst")
    ingestion_log = parser.ingest(
        file_name=uploaded_file.name,
        file_content=file_content,
    )

    serializer = IngestionLogSerializer(ingestion_log)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def ingestion_list(request):
    """
    List all ingestion logs, optionally filtered by client_id or source_type.
    """
    queryset = IngestionLog.objects.select_related("client").all()

    client_id = request.query_params.get("client_id")
    if client_id:
        queryset = queryset.filter(client_id=client_id)

    source_type = request.query_params.get("source_type")
    if source_type:
        queryset = queryset.filter(source_type=source_type)

    serializer = IngestionLogSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def ingestion_detail(request, pk):
    """Get details of a specific ingestion log."""
    try:
        log = IngestionLog.objects.select_related("client").get(id=pk)
    except IngestionLog.DoesNotExist:
        return Response(
            {"error": "Ingestion log not found"},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = IngestionLogSerializer(log)
    return Response(serializer.data)
