# Source Format Research & Sample Data

To build realistic parsers, we researched the actual data formats produced by these three systems.

## 1. SAP Fuel & Procurement
- **Format Modeled**: Flat file CSV export (pipe-delimited) from SAP transaction `ME2M` (Purchasing Documents by Material).
- **Real-World Messiness Handled**:
  - German column headers (e.g., `Mengeneinheit` for unit).
  - Date format `DD.MM.YYYY`.
  - Implicit/internal units: `TO` (metric tons), `GAL` (gallons).
  - Amount encoding: SAP sometimes exports currency amounts without decimal points (e.g. `425000` = `4250.00`).
  - Extracted plant codes (`Werk`) into `source_metadata` since they are critical for facility-level reporting.

## 2. Utility Electricity
- **Format Modeled**: Standard CSV export from a commercial utility billing portal (e.g., Tata Power, PG&E).
- **Real-World Messiness Handled**:
  - Utility data rarely maps perfectly to a calendar month (e.g., billing period `15-Mar` to `12-Apr`).
  - Consumption must often be calculated by subtracting the `Previous Reading` from the `Current Reading`.
  - Estimates: Flags estimated reads (`E`) vs actual reads (`A`).
  - Separates Demand charges (kW) from Energy usage (kWh), storing kW in metadata to avoid confusing the primary Scope 2 activity quantity.

## 3. Corporate Travel (SAP Concur)
- **Format Modeled**: JSON array matching the SAP Concur v4 Expense Reports API schema.
- **Real-World Messiness Handled**:
  - Hierarchical data (Reports -> Expenses).
  - Normalising flights: The raw data contains airport IATA codes (`BOM`, `LHR`). Our parser implements a lookup table of major airport coordinates and calculates the Haversine distance in `km` to generate the normalized activity quantity.
  - Normalising hotels: Extracts the `nights` field to produce a `room-nights` quantity.
  - Multi-currency: Handles `transactionAmount` vs home currency.
