# Implementation Tradeoffs

Per the assignment rubric ("what you chose not to build"), here are the deliberate omissions made to deliver a robust prototype within the 4-day limit.

## 1. No Live Carbon Calculation (Emission Factors)
**Omission**: The platform normalises activity data (e.g., "500 liters of diesel", "2000 km flight") but does *not* multiply these by emission factors to produce final CO2e (Carbon Dioxide Equivalent) metrics.
**Why**: Managing an emission factor database (EPA, DEFRA, Ecoinvent) requires complex temporal and geographic lookups (e.g., the grid emission factor for Mumbai in 2023 is different from Delhi in 2024). Building a dummy version of this detracts from the core ingestion challenge.

## 2. No OCR / PDF Parsing for Utility Bills
**Omission**: The utility ingestion expects a structured CSV portal export, not a scanned PDF of a monthly electricity bill.
**Why**: Reliable OCR for tabular data in PDFs is a notoriously difficult machine learning problem requiring tools like AWS Textract or custom LayoutLM models. Standard regex/text-extraction fails on multi-page, varied-format utility bills. We assume the client can download a CSV from their utility provider's portal.

## 3. Simplified Authentication & Role-Based Access Control
**Omission**: The prototype does not implement a full JWT/OAuth2 login flow with distinct "Client Uploader" vs "Breathe ESG Analyst" roles.
**Why**: Auth boilerplate consumes significant time but doesn't demonstrate domain knowledge of emissions data. The API endpoints act as if they are authenticated as a super-analyst capable of seeing all tenants, to facilitate easy testing and review.
