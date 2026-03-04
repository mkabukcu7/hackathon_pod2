# Logic Apps Connection (Pre-Wired)

This folder contains a starter workflow template that connects Logic Apps to the new API workflow contracts.

## Files
- `customer_packet_workflow.template.json`: Request-triggered Logic App workflow template.

## API Contracts Used
- `GET /api/workflows/platform-health`
- `GET /api/workflows/customer-packet/{customer_id}`

## Deploy / Use
1. Create a Logic App (Consumption or Standard).
2. Import workflow definition from `customer_packet_workflow.template.json`.
3. Set parameters:
   - `apiBaseUrl` = your deployed API base URL (for example, `https://<app>.azurewebsites.net`)
   - `workflowSharedKey` = value of `WORKFLOW_SHARED_KEY` configured on the API (or leave empty if not enforced).
4. Save workflow.
5. Trigger with payload:
   ```json
   { "customer_id": "C0000481" }
   ```

## Workflow Behavior
- Calls `platform-health` first with retries (exponential backoff).
- If health is `healthy`, calls `customer-packet` with retries.
- Returns `200` on success with both payloads.
- Returns `503` when platform status is non-healthy.
- Returns `502` when health check or customer packet calls fail/time out.

## Expected Response Envelope
- `platform_health`: API/data-layer readiness payload.
- `customer_packet`: deterministic customer packet containing:
  - `request_id`, `generated_at`, `customer_id`
  - `status` (`success`, `partial_success`, `failed`)
  - `data` (profile, insights, retention score, cross-sell, optional risk)
  - `errors` (component-level failures)
  - `meta` (components returned, error count)

## Notes
- This is the connection-ready layer; comprehensive validation can be run at final QA stage.
- Workflow endpoint header used by this template: `x-workflow-key`.
