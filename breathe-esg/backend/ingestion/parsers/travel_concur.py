"""
Corporate travel data parser (Concur-style JSON).

Handles JSON exports modeled after the SAP Concur v4 Expense Reports API.

Real-world Concur export characteristics handled here:
- Expense types with codes: AIRFR (Airfare), HOTEL, TAXIX, CARRT, TRAIN
- Multi-currency: transactionAmount (local) + postedAmount (home currency)
- Exchange rates with operation (MULTIPLY)
- Airport IATA codes for flights (origin/destination)
- Vendor details for airlines, hotels, etc.
- Nested report → expenses structure
"""

import json
from datetime import datetime
from decimal import Decimal

from core.models import IngestionLog, ActivityRecord
from .base import BaseParser
from ingestion.normalizers import airport_distance_km, normalize_unit


# Map Concur expense type codes to our categories
EXPENSE_TYPE_MAP = {
    "AIRFR": ActivityRecord.Category.FLIGHT,
    "HOTEL": ActivityRecord.Category.HOTEL,
    "TAXIX": ActivityRecord.Category.GROUND_TRANSPORT,
    "CARRT": ActivityRecord.Category.GROUND_TRANSPORT,
    "TRAIN": ActivityRecord.Category.GROUND_TRANSPORT,
    "LIMOX": ActivityRecord.Category.GROUND_TRANSPORT,
    "BUSFR": ActivityRecord.Category.GROUND_TRANSPORT,
}


class TravelConcurParser(BaseParser):
    """Parser for Concur-style travel expense JSON exports."""

    source_type = IngestionLog.SourceType.TRAVEL_CONCUR

    def parse_file(self, file_content: bytes) -> list[dict]:
        """
        Parse JSON file. Supports two structures:
        1. Array of report objects, each with nested expenses
        2. Single report object with nested expenses

        Flattens to a list of individual expense entries,
        each carrying its parent report metadata.
        """
        text = file_content.decode("utf-8-sig")
        data = json.loads(text)

        # Normalize to list of reports
        if isinstance(data, dict):
            reports = [data]
        elif isinstance(data, list):
            # Could be list of reports or list of flat expenses
            if data and "expenses" in data[0]:
                reports = data
            else:
                # Flat list of expenses — wrap each as its own "report"
                reports = [{"reportId": "UNKNOWN", "expenses": data}]
        else:
            raise ValueError("Unexpected JSON structure: expected object or array")

        # Flatten: each expense becomes a row, enriched with report-level fields
        flat_expenses = []
        for report in reports:
            report_meta = {
                "reportId": report.get("reportId", ""),
                "reportDate": report.get("reportDate", ""),
                "employeeName": report.get("employeeName", ""),
                "departmentCode": report.get("departmentCode", ""),
                "businessPurpose": report.get("businessPurpose", ""),
            }
            for expense in report.get("expenses", []):
                entry = {**report_meta, **expense}
                flat_expenses.append(entry)

        return flat_expenses

    def get_field_mapping(self) -> dict:
        return {
            "expenseType.id": "category",
            "transactionDate": "activity_date",
            "transactionAmount.value": "quantity/amount",
            "origin + destination": "distance_km (calculated)",
            "vendor.name": "vendor",
        }

    def normalize_row(
        self, raw_row: dict, row_number: int, log: IngestionLog
    ) -> ActivityRecord | None:
        """
        Convert a Concur expense entry into a normalized ActivityRecord.

        Key transformations:
        - Map expense type code to category (FLIGHT, HOTEL, GROUND_TRANSPORT)
        - For flights: calculate distance from airport codes
        - For hotels: quantity = number of nights (estimated from dates if needed)
        - For ground transport: quantity = trip count or distance
        """
        # Determine category from expense type
        expense_type = raw_row.get("expenseType", {})
        if isinstance(expense_type, str):
            type_code = expense_type
        else:
            type_code = expense_type.get("id", "")

        category = EXPENSE_TYPE_MAP.get(type_code)
        if not category:
            # Skip non-travel expenses (meals, office supplies, etc.)
            return None

        # Parse date
        date_str = raw_row.get("transactionDate", "")
        try:
            activity_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            raise ValueError(f"Cannot parse transaction date: '{date_str}'")

        # Get amount
        tx_amount = raw_row.get("transactionAmount", {})
        if isinstance(tx_amount, dict):
            amount_value = self.safe_decimal(tx_amount.get("value", 0), "amount")
            currency = tx_amount.get("currencyCode", "")
        else:
            amount_value = self.safe_decimal(tx_amount, "amount")
            currency = ""

        # Category-specific normalization
        if category == ActivityRecord.Category.FLIGHT:
            return self._process_flight(
                raw_row, row_number, log, activity_date, amount_value, currency
            )
        elif category == ActivityRecord.Category.HOTEL:
            return self._process_hotel(
                raw_row, row_number, log, activity_date, amount_value, currency
            )
        else:
            return self._process_ground_transport(
                raw_row, row_number, log, activity_date, amount_value, currency,
                type_code,
            )

    def _process_flight(
        self, raw_row, row_number, log, activity_date, amount, currency
    ):
        """Process a flight expense — calculate distance from airport codes."""
        origin = raw_row.get("origin", "")
        destination = raw_row.get("destination", "")

        # Calculate distance
        distance = airport_distance_km(origin, destination) if origin and destination else None

        if distance:
            quantity = distance
            original_unit = "km"
            normalized_qty = distance
            normalized_unit = "km"
        else:
            # Fallback: store amount as quantity (no distance available)
            quantity = amount
            original_unit = currency or "trip"
            normalized_qty = Decimal("1")
            normalized_unit = "trip"

        vendor = raw_row.get("vendor", {})
        vendor_name = vendor.get("name", "") if isinstance(vendor, dict) else str(vendor)
        vendor_desc = vendor.get("description", "") if isinstance(vendor, dict) else ""

        description = (
            f"Flight {origin}→{destination} — "
            f"{vendor_name} {vendor_desc}".strip()
        )

        travel_class = raw_row.get("travelClass", "")
        source_metadata = {
            "report_id": raw_row.get("reportId", ""),
            "expense_id": raw_row.get("expenseId", ""),
            "employee_name": raw_row.get("employeeName", ""),
            "department": raw_row.get("departmentCode", ""),
            "business_purpose": raw_row.get("businessPurpose", ""),
            "origin_airport": origin,
            "destination_airport": destination,
            "distance_km": str(distance) if distance else None,
            "airline": vendor_name,
            "flight_number": vendor_desc,
            "travel_class": travel_class,
            "amount": str(amount),
            "currency": currency,
        }

        return ActivityRecord(
            client=self.client,
            ingestion_log=log,
            source_type=self.source_type,
            source_row_number=row_number,
            raw_data=raw_row,
            ghg_scope=ActivityRecord.GHGScope.SCOPE_3,
            category=ActivityRecord.Category.FLIGHT,
            activity_date=activity_date,
            quantity=quantity,
            original_unit=original_unit,
            normalized_quantity=normalized_qty,
            normalized_unit=normalized_unit,
            description=description,
            source_metadata=source_metadata,
        )

    def _process_hotel(
        self, raw_row, row_number, log, activity_date, amount, currency
    ):
        """Process a hotel expense — quantity = room-nights."""
        nights = raw_row.get("nights")
        if nights:
            quantity = self.safe_decimal(nights, "nights")
        else:
            quantity = Decimal("1")  # Default to 1 night if not specified

        vendor = raw_row.get("vendor", {})
        vendor_name = vendor.get("name", "") if isinstance(vendor, dict) else str(vendor)
        location = raw_row.get("location", {})
        city = location.get("city", "") if isinstance(location, dict) else ""

        description = f"Hotel stay: {quantity} night(s) at {vendor_name}, {city}".strip(", ")

        source_metadata = {
            "report_id": raw_row.get("reportId", ""),
            "expense_id": raw_row.get("expenseId", ""),
            "employee_name": raw_row.get("employeeName", ""),
            "department": raw_row.get("departmentCode", ""),
            "business_purpose": raw_row.get("businessPurpose", ""),
            "hotel_name": vendor_name,
            "city": city,
            "country_code": location.get("countryCode", "") if isinstance(location, dict) else "",
            "amount": str(amount),
            "currency": currency,
        }

        return ActivityRecord(
            client=self.client,
            ingestion_log=log,
            source_type=self.source_type,
            source_row_number=row_number,
            raw_data=raw_row,
            ghg_scope=ActivityRecord.GHGScope.SCOPE_3,
            category=ActivityRecord.Category.HOTEL,
            activity_date=activity_date,
            quantity=quantity,
            original_unit="room-nights",
            normalized_quantity=quantity,
            normalized_unit="room-nights",
            description=description,
            source_metadata=source_metadata,
        )

    def _process_ground_transport(
        self, raw_row, row_number, log, activity_date, amount, currency, type_code
    ):
        """Process ground transport (taxi, car rental, train)."""
        distance = raw_row.get("distance_km")
        if distance:
            quantity = self.safe_decimal(distance, "distance_km")
            original_unit = "km"
            normalized_qty, normalized_unit = normalize_unit(quantity, "km")
        else:
            quantity = Decimal("1")
            original_unit = "trip"
            normalized_qty = Decimal("1")
            normalized_unit = "trip"

        vendor = raw_row.get("vendor", {})
        vendor_name = vendor.get("name", "") if isinstance(vendor, dict) else str(vendor)

        type_names = {
            "TAXIX": "Taxi",
            "CARRT": "Car Rental",
            "TRAIN": "Train",
            "LIMOX": "Limo",
            "BUSFR": "Bus",
        }
        transport_type = type_names.get(type_code, "Ground Transport")

        location = raw_row.get("location", {})
        city = location.get("city", "") if isinstance(location, dict) else ""

        description = f"{transport_type} — {vendor_name} in {city}".strip(" —")

        source_metadata = {
            "report_id": raw_row.get("reportId", ""),
            "expense_id": raw_row.get("expenseId", ""),
            "employee_name": raw_row.get("employeeName", ""),
            "department": raw_row.get("departmentCode", ""),
            "business_purpose": raw_row.get("businessPurpose", ""),
            "transport_type": transport_type,
            "vendor_name": vendor_name,
            "city": city,
            "amount": str(amount),
            "currency": currency,
        }

        return ActivityRecord(
            client=self.client,
            ingestion_log=log,
            source_type=self.source_type,
            source_row_number=row_number,
            raw_data=raw_row,
            ghg_scope=ActivityRecord.GHGScope.SCOPE_3,
            category=ActivityRecord.Category.GROUND_TRANSPORT,
            activity_date=activity_date,
            quantity=quantity,
            original_unit=original_unit,
            normalized_quantity=normalized_qty,
            normalized_unit=normalized_unit,
            description=description,
            source_metadata=source_metadata,
        )
