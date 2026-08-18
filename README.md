# Lab API

Minimal FastAPI/PostgreSQL vertical slice for:

```text
experiment → sample → print job → printer event → notification → form submission
```

This deliberately excludes authentication, artifact storage, direct printer control, push-provider delivery, and Vault/LIMS synchronization. Notifications are persisted as an API-backed inbox for the mobile app; a push delivery worker can be added later without changing the workflow records.

## Run locally

1. Copy `.env.example` to `.env` and point `LAB_DATABASE_URL` at PostgreSQL.
2. Install project dependencies with your preferred Python environment manager.
3. Apply the schema: `alembic upgrade head`.
4. Start the API: `uvicorn app.main:app --reload`.

The interactive OpenAPI UI is at `/docs`.

## Endpoint surface

- `POST /api/v1/experiments`
- `POST /api/v1/samples`
- `POST /api/v1/print-jobs`
- `POST /api/v1/print-jobs/{id}/events` (requires `Idempotency-Key`)
- `GET /api/v1/notifications`
- `POST /api/v1/notifications/{id}/read`
- `POST /api/v1/form-submissions`

Printer events update print-job status and create one inbox notification per idempotency key. All IDs are UUIDs.
