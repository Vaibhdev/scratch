"""
Management command to seed sample data.
Creates a demo client and ingests all three sample data files.
"""

import os
from pathlib import Path
from django.core.management.base import BaseCommand
from core.models import Client
from ingestion.parsers.sap_procurement import SAPProcurementParser
from ingestion.parsers.utility_electricity import UtilityElectricityParser
from ingestion.parsers.travel_concur import TravelConcurParser


class Command(BaseCommand):
    help = "Seed the database with sample data from all three sources"

    def handle(self, *args, **options):
        sample_dir = Path(__file__).resolve().parent.parent.parent.parent / "sample_data"

        # Create demo client
        client, created = Client.objects.get_or_create(
            name="Tata Industries Ltd",
            defaults={
                "industry": "Manufacturing & Steel",
                "country": "India",
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created client: {client.name}"))
        else:
            self.stdout.write(f"Client already exists: {client.name}")

        # Ingest SAP procurement data
        sap_file = sample_dir / "sap_procurement_export.csv"
        if sap_file.exists():
            parser = SAPProcurementParser(client=client, uploaded_by="seed_command")
            log = parser.ingest("sap_procurement_export.csv", sap_file.read_bytes())
            self.stdout.write(
                self.style.SUCCESS(
                    f"SAP: {log.successful_rows}/{log.total_rows} rows ingested "
                    f"({log.failed_rows} failed)"
                )
            )
        else:
            self.stdout.write(self.style.WARNING(f"SAP file not found: {sap_file}"))

        # Ingest utility electricity data
        util_file = sample_dir / "utility_electricity_export.csv"
        if util_file.exists():
            parser = UtilityElectricityParser(client=client, uploaded_by="seed_command")
            log = parser.ingest("utility_electricity_export.csv", util_file.read_bytes())
            self.stdout.write(
                self.style.SUCCESS(
                    f"Utility: {log.successful_rows}/{log.total_rows} rows ingested "
                    f"({log.failed_rows} failed)"
                )
            )
        else:
            self.stdout.write(self.style.WARNING(f"Utility file not found: {util_file}"))

        # Ingest travel data
        travel_file = sample_dir / "travel_concur_export.json"
        if travel_file.exists():
            parser = TravelConcurParser(client=client, uploaded_by="seed_command")
            log = parser.ingest("travel_concur_export.json", travel_file.read_bytes())
            self.stdout.write(
                self.style.SUCCESS(
                    f"Travel: {log.successful_rows}/{log.total_rows} rows ingested "
                    f"({log.failed_rows} failed)"
                )
            )
        else:
            self.stdout.write(self.style.WARNING(f"Travel file not found: {travel_file}"))

        from core.models import ActivityRecord
        total = ActivityRecord.objects.count()
        self.stdout.write(self.style.SUCCESS(f"\nTotal activity records: {total}"))
