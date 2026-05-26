# Technical Decisions & Rationale

## 1. Why Flat Files for SAP?
Instead of building a live OData or BAPI integration with SAP, we built a flat file (CSV) parser.
**Reasoning**: In enterprise environments, giving a third-party startup direct live access to an SAP ERP system (which sits behind firewalls and requires complex SAP PI/PO middleware or SAP Gateway configuration) is a multi-month compliance process. However, any SAP user can immediately export a table from transaction `SE16` or run an ALV report and click "Export to Local File". Supporting CSV uploads maps to how data actually moves in the early stages of enterprise onboarding.

## 2. Why JSON for Corporate Travel?
We modeled the travel ingestion after the SAP Concur v4 Expense API JSON schema.
**Reasoning**: While Concur does offer CSV exports, integrating via their standard JSON schema demonstrates readiness to convert this file-upload pipeline into a live webhook/API pull pipeline in the future without changing the core normalisation logic.

## 3. Why Column-based Multi-tenancy?
**Reasoning**: The assignment asked to "handle multi-tenancy". Options were Database-per-tenant, Schema-per-tenant (e.g. `django-tenant-schemas`), or Column-based. For a 4-day prototype, Schema/DB multi-tenancy introduces massive devops and migration complexity. Column-based (`client_id` FK) provides logical isolation that is trivial to query and verify.

## 4. Why preserve `raw_data` as JSON?
**Reasoning**: In ESG reporting, auditability is critical. If an auditor asks "Where did this 4,200 kg of CO2 come from?", we must be able to trace it back to the exact row in the exact spreadsheet the client uploaded. The `raw_data` JSON field ensures we never lose the original fidelity of the data, even if our parsing logic drops columns we didn't think were important.

## 5. What would we clarify with the Product Manager?
If this were a real project kickoff, we would ask:
1. **User Roles**: Who is uploading this data? Is it a client facility manager, or a Breathe ESG implementation manager? This dictates the complexity of the upload UI and error handling.
2. **Emission Factors**: Does the system need to calculate the actual CO2e (kg) upon ingestion, or is this platform purely for activity data staging before passing to a calculation engine?
3. **Data Correction**: If an analyst spots an error in the raw data, should they edit the `ActivityRecord` directly in our platform, or reject the record and ask the client to re-upload the corrected file?
