"""
Utility electricity data parser.

Handles CSV exports from utility company portals.

Real-world utility data characteristics handled here:
- Meter readings (not consumption) — consumption = current - previous reading
- Billing periods that don't align to calendar months (e.g., 15-Mar to 12-Apr)
- Read types: A (Actual) vs E (Estimated)
- Multiple meters per facility (main + sub-meters)
- Demand charges in kW alongside energy in kWh
- Tariff codes for rate classification
"""

import csv
import io
from datetime import datetime
from decimal import Decimal

from core.models import IngestionLog, ActivityRecord
from .base import BaseParser
from ingestion.normalizers import normalize_unit


COLUMN_MAP = {
    "Account Number": "account_number",
    "Meter ID": "meter_id",
    "Service Address": "service_address",
    "Read Date": "read_date",
    "Previous Read Date": "previous_read_date",
    "Read Type": "read_type",
    "Previous Reading (kWh)": "previous_reading",
    "Current Reading (kWh)": "current_reading",
    "Usage (kWh)": "usage_kwh",
    "Demand (kW)": "demand_kw",
    "Tariff Code": "tariff_code",
    "Rate ($/kWh)": "rate",
    "Amount ($)": "amount",
    "Billing Period Start": "period_start",
    "Billing Period End": "period_end",
}


class UtilityElectricityParser(BaseParser):
    """Parser for utility company electricity portal CSV exports."""

    source_type = IngestionLog.SourceType.UTILITY_ELECTRICITY

    def parse_file(self, file_content: bytes) -> list[dict]:
        """Parse standard CSV with header row."""
        text = file_content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))

        rows = []
        for row in reader:
            cleaned = {k.strip(): v.strip() for k, v in row.items() if k}
            if any(v for v in cleaned.values()):
                rows.append(cleaned)
        return rows

    def get_field_mapping(self) -> dict:
        return COLUMN_MAP

    def normalize_row(
        self, raw_row: dict, row_number: int, log: IngestionLog
    ) -> ActivityRecord | None:
        """
        Convert a utility electricity row into a normalized ActivityRecord.

        Key transformations:
        - Calculate consumption from meter readings if Usage column is empty
        - Parse non-standard billing period dates
        - Flag estimated reads in source_metadata
        - Store demand (kW) separately from energy (kWh) in source_metadata
        """
        # Parse dates
        read_date_str = raw_row.get("Read Date", "")
        period_start_str = raw_row.get("Billing Period Start", "")
        period_end_str = raw_row.get("Billing Period End", "")

        try:
            activity_date = self._parse_date(read_date_str)
        except ValueError:
            raise ValueError(f"Cannot parse read date: '{read_date_str}'")

        period_start = None
        period_end = None
        try:
            if period_start_str:
                period_start = self._parse_date(period_start_str)
            if period_end_str:
                period_end = self._parse_date(period_end_str)
        except ValueError:
            pass  # Non-critical — billing period dates are informational

        # Get consumption — prefer explicit Usage column, fall back to reading delta
        usage_str = raw_row.get("Usage (kWh)", "").strip()
        if usage_str:
            quantity = self.safe_decimal(usage_str, "Usage (kWh)")
        else:
            # Calculate from meter readings
            current = self.safe_decimal(
                raw_row.get("Current Reading (kWh)", ""), "Current Reading"
            )
            previous = self.safe_decimal(
                raw_row.get("Previous Reading (kWh)", ""), "Previous Reading"
            )
            quantity = current - previous
            if quantity < 0:
                raise ValueError(
                    f"Negative consumption ({quantity} kWh) — "
                    f"possible meter rollover or data error"
                )

        original_unit = "kWh"
        normalized_qty, normalized_unit = normalize_unit(quantity, original_unit)

        # Read type detection
        read_type = raw_row.get("Read Type", "A").strip().upper()
        is_estimated = read_type == "E"

        # Demand (kW) — stored in metadata, not the primary quantity
        demand_str = raw_row.get("Demand (kW)", "").strip()
        demand_kw = None
        if demand_str:
            try:
                demand_kw = str(self.safe_decimal(demand_str, "Demand (kW)"))
            except ValueError:
                pass

        # Amount
        amount_str = raw_row.get("Amount ($)", "").strip()
        amount = None
        if amount_str:
            try:
                amount = str(self.safe_decimal(amount_str, "Amount"))
            except ValueError:
                pass

        # Build description
        meter_id = raw_row.get("Meter ID", "?")
        address = raw_row.get("Service Address", "")
        description = (
            f"Electricity consumption: {quantity} kWh — "
            f"Meter {meter_id}"
            f"{' (ESTIMATED)' if is_estimated else ''}"
        )

        source_metadata = {
            "account_number": raw_row.get("Account Number", ""),
            "meter_id": meter_id,
            "service_address": address,
            "read_type": read_type,
            "is_estimated": is_estimated,
            "previous_reading_kwh": raw_row.get("Previous Reading (kWh)", ""),
            "current_reading_kwh": raw_row.get("Current Reading (kWh)", ""),
            "demand_kw": demand_kw,
            "tariff_code": raw_row.get("Tariff Code", ""),
            "rate_per_kwh": raw_row.get("Rate ($/kWh)", ""),
            "amount": amount,
        }

        return ActivityRecord(
            client=self.client,
            ingestion_log=log,
            source_type=self.source_type,
            source_row_number=row_number,
            raw_data=raw_row,
            ghg_scope=ActivityRecord.GHGScope.SCOPE_2,
            category=ActivityRecord.Category.ELECTRICITY,
            activity_date=activity_date,
            period_start=period_start,
            period_end=period_end,
            quantity=quantity,
            original_unit=original_unit,
            normalized_quantity=normalized_qty,
            normalized_unit=normalized_unit,
            description=description,
            source_metadata=source_metadata,
        )

    @staticmethod
    def _parse_date(date_str: str):
        """Try multiple date formats common in utility exports."""
        date_str = date_str.strip()
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Unrecognized date format: '{date_str}'")
