# Tomorrow Plan: Logic Apps Integration

Date: 2026-02-24
Goal: Complete Logic Apps connection to workflow endpoints and run end-to-end verification.

## 0) 5-Minute Kickoff
1. Run endpoint preflight:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\logic_apps\preflight_workflow_endpoints.ps1 -ApiBaseUrl "https://<your-api-host>" -WorkflowSharedKey "<your-workflow-shared-key>" -CustomerId "C0000481"
   ```
2. Confirm both calls pass: `platform-health` and `customer-packet`.
3. Use payload file `logic_apps/sample_trigger_payload.json` for manual Logic Apps trigger.
4. Compare output envelope with `logic_apps/sample_expected_response_shape.json`.

## 1) What to do tomorrow (Checklist)
- [ ] Confirm API is running and reachable from Logic Apps environment.
- [ ] Set `WORKFLOW_SHARED_KEY` in API runtime settings.
- [ ] Import workflow definition from `logic_apps/customer_packet_workflow.template.json`.
- [ ] Configure workflow parameters (`apiBaseUrl`, `workflowSharedKey`).
- [ ] Run a manual trigger with a known customer ID.
- [ ] Validate response envelope fields and status behavior.
- [ ] Add retries/timeouts tuning if needed from first run telemetry.
- [ ] Capture final screenshots/log snippets for handoff.

## 2) Prerequisites
- Deployed API host URL (example: `https://<app>.azurewebsites.net`).
- Workflow key value matching API env var `WORKFLOW_SHARED_KEY`.
- At least one valid customer ID (example: `C0000481`).
- Access to Logic Apps designer (Consumption or Standard).
- Local helper files ready:
   - `logic_apps/preflight_workflow_endpoints.ps1`
   - `logic_apps/sample_trigger_payload.json`
   - `logic_apps/sample_expected_response_shape.json`

## 3) Integration Steps (Logic Apps)
1. Open Logic Apps and create/open your target workflow app.
2. Import `logic_apps/customer_packet_workflow.template.json`.
3. Set parameters:
   - `apiBaseUrl` = deployed API base URL
   - `workflowSharedKey` = same value configured in API as `WORKFLOW_SHARED_KEY`
4. Save the workflow.
5. Trigger the request with payload:
   ```json
   { "customer_id": "C0000481" }
   ```
6. Review action results in run history:
   - `Get_Platform_Health`
   - `Check_Platform_Health`
   - `Get_Customer_Packet` (if health is `healthy`)
7. Confirm expected status outcomes:
   - `200` when platform is healthy and customer packet succeeds
   - `503` when platform health is degraded/non-healthy
   - `502` when health call or customer packet call fails/times out

## 4) Quick Validation Checklist
- [ ] `platform_health.status` is present.
- [ ] `customer_packet.request_id` is present.
- [ ] `customer_packet.status` is one of `success`, `partial_success`, `failed`.
- [ ] `customer_packet.meta.components_returned` is present.
- [ ] `customer_packet.errors` is an array (possibly empty).

## 5) Troubleshooting Quick Notes
- `401 Unauthorized`: `x-workflow-key` value does not match `WORKFLOW_SHARED_KEY`.
- `503 response`: Data layer is not healthy; check `/api/workflows/platform-health` directly.
- `502 response`: Upstream call failed/timed out; inspect action outputs and API logs.
- Empty packet data: test with known-valid customer ID and verify backend data layer connectivity.

## 6) End-of-Day Definition of Done
- [ ] Workflow runs successfully at least once with `200` and valid packet shape.
- [ ] Failure paths (`503` and one `502` scenario) are verified/documented.
- [ ] Final parameter values and run-history evidence captured.
