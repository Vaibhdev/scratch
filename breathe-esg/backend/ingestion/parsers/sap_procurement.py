"""
SAP Fuel & Procurement data parser.

Handles pipe-delimited CSV exports from SAP with German column headers.
Typical source: Transaction ME2M/MIGO export or scheduled ABAP report.

Real-world SAP export characteristics handled here:
- German column headers (Belegnummer, Buchungsdatum, Materialnummer, etc.)
- Pipe (|) delimiter
- Date format: DD.MM.YYYY
- Plant codes (4-char, e.g. '1000') — preserved in source_metadata
- Material numbers: 18-digit zero-padded internal codes
- Amounts may be integer-encoded (no decimal point): 425000 = 4250.00
- Units: L (liters), TO (metric tons), KG, GAL, M3
"""

import csv
import io
from datetime import datetime
from decimal import Decimal

from core.models import IngestionLog, ActivityRecord
from .base import BaseParser
from ingestion.normalizers import normalize_unit


# German header → internal field name mapping
COLUMN_MAP = {
    "Belegnummer": "document_number",
    "Buchungsdatum": "posting_date",
    "Materialnummer": "material_number",
    "Materialbezeichnung": "material_description",
    "Werk": "plant_code",
    "Menge": "quantity",
    "Mengeneinheit": "unit",
    "Lieferant": "vendor_code",
    "Betrag": "amount",
    "Waehrung": "currency",
    "Kostenart": "cost_type",
    "Einkaufsorganisation": "purchasing_org",
}

# Material keyword → fuel type mapping for normalization
FUEL_TYPE_KEYWORDS = {
    "diesel": "diesel",
    "petrol": "petrol",
    "gasoline": "gasoline",
    "benzin": "petrol",       # German for petrol
    "natural gas": "natural_gas",
    "erdgas": "natural_gas",  # German for natural gas
    "lng": "natural_gas",
    "cng": "natural_gas",
    "heating oil": "heating_oil",
    "heizöl": "heating_oil",  # German
    "lpg": "lpg",
    "flüssiggas": "lpg",     # German for LPG
    "kerosene": "kerosene",
    "kerosin": "kerosene",    # German
}


def detect_fuel_type(material_description: str) -> str:
    """
    Detect fuel type from material description text.
    Falls back to 'unknown' if no keyword matches.
    """
    desc_lower = material_description.lower()
    for keyword, fuel_type in FUEL_TYPE_KEYWORDS.items():
        if keyword in desc_lower:
            return fuel_type
    return "unknown"


class SAPProcurementParser(BaseParser):
    """Parser for SAP fuel and procurement flat file exports."""

    source_type = IngestionLog.SourceType.SAP_PROCUREMENT

    def parse_file(self, file_content: bytes) -> list[dict]:
        """Parse pipe-delimited CSV with German headers."""
        text = file_content.decode("utf-8-sig")  # Handle BOM from Windows exports
        reader = csv.DictReader(io.StringIO(text), delimiter="|")

        rows = []
        for row in reader:
            # Strip whitespace from keys and values
            cleaned = {k.strip(): v.strip() for k, v in row.items() if k}
            if any(v for v in cleaned.values()):  # Skip completely empty rows
                rows.append(cleaned)
        return rows

    def get_field_mapping(self) -> dict:
        return COLUMN_MAP

    def normalize_row(
        self, raw_row: dict, row_number: int, log: IngestionLog
    ) -> ActivityRecord | None:
        """
        Convert a SAP procurement row into a normalized ActivityRecord.

        Key transformations:
        - Parse DD.MM.YYYY dates
        - Detect fuel type from material description
        - Normalize units (L→liters, TO→kg, GAL→liters)
        - SAP amounts: divide by 100 if they appear integer-encoded
        """
        # Map German headers to internal names
        mapped = {}
        for german_key, internal_key in COLUMN_MAP.items():
            mapped[internal_key] = raw_row.get(german_key, "")

        # Parse date (DD.MM.YYYY format)
        date_str = mapped.get("posting_date", "")
        try:
            if "." in date_str:
                activity_date = datetime.strptime(date_str, "%d.%m.%Y").date()
            elif len(date_str) == 8 and date_str.isdigit():
                # SAP internal YYYYMMDD format
                activity_date = datetime.strptime(date_str, "%Y%m%d").date()
            else:
                activity_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            raise ValueError(f"Cannot parse date: '{date_str}'")

        # Parse quantity
        quantity = self.safe_decimal(mapped.get("quantity"), "Menge/quantity")

        # Parse unit
        original_unit = mapped.get("unit", "").strip()
        if not original_unit:
            raise ValueError("Missing unit (Mengeneinheit)")

        # Detect fuel type from material description
        material_desc = mapped.get("material_description", "")
        fuel_type = detect_fuel_type(material_desc)

        # Normalize unit
        normalized_qty, normalized_unit = normalize_unit(
            quantity, original_unit, fuel_type
        )

        # Parse amount — SAP sometimes encodes as integer (425000 = 4250.00)
        amount_raw = mapped.get("amount", "0")
        amount = self.safe_decimal(amount_raw, "Betrag/amount")
        # Heuristic: if amount > 10000 and no decimal point in original, divide by 100
        if amount > 10000 and "." not in str(amount_raw) and "," not in str(amount_raw):
            amount = amount / 100

        # Build description
        description = (
            f"{material_desc} — {quantity} {original_unit} "
            f"from plant {mapped.get('plant_code', '?')}"
        )

        # Source-specific metadata
        source_metadata = {
            "document_number": mapped.get("document_number", ""),
            "material_number": mapped.get("material_number", ""),
            "plant_code": mapped.get("plant_code", ""),
            "vendor_code": mapped.get("vendor_code", ""),
            "amount": str(amount),
            "currency": mapped.get("currency", ""),
            "cost_type": mapped.get("cost_type", ""),
            "purchasing_org": mapped.get("purchasing_org", ""),
            "fuel_type_detected": fuel_type,
        }

        return ActivityRecord(
            client=self.client,
            ingestion_log=log,
            source_type=self.source_type,
            source_row_number=row_number,
            raw_data=raw_row,
            ghg_scope=ActivityRecord.GHGScope.SCOPE_1,
            category=ActivityRecord.Category.FUEL_COMBUSTION,
            activity_date=activity_date,
            quantity=quantity,
            original_unit=original_unit,
            normalized_quantity=normalized_qty,
            normalized_unit=normalized_unit,
            description=description,
            source_metadata=source_metadata,
        )
