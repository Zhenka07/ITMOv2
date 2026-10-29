# Spec-Kit: Logic Team Specification (Aligned v2 - Post-Reconciliation)

**Team**: Backend API & Logic Team  
**Status**: Approved & Reconciled (Contract Signed)  
**Feature**: DataHub Backend - Query Engine, REST API & Persistence Layer

---

## 1. Domain Entities and Schema

### 1.1 Item Entity
- `id`: string (Unique identifier, pattern: `itm-[a-f0-9]{3,8}`, e.g. `itm-001`)
- `title`: string (Normalized, 3 to 120 characters, non-empty, leading/trailing whitespace trimmed)
- `category`: string enum (`engineering`, `devops`, `security`, `product`, `analytics`)
- `status`: string enum (`active`, `pending`, `archived`)
- `description`: string (optional, max 1000 characters)
- `tags`: array of string (normalized lowercase, regex: `^[a-z0-9\-_]{1,30}$`)
- `priority`: integer between 1 (lowest) and 5 (critical), default: 1
- `metadata`: dictionary of arbitrary key-value pairs
- `created_at`: ISO 8601 UTC timestamp string
- `updated_at`: ISO 8601 UTC timestamp string

---

## 2. API Endpoints & Protocols

### 2.1 GET `/api/v1/items`
- Supports query filtering: `search`, `category`, `status`, `tag`, `sort_by`, `sort_order`, `offset`, `limit`.
- Computes `total` matching records.
- Sets response headers:
  - `X-Total-Count`: `<total>`
  - `X-Offset`: `<offset>`
  - `X-Limit`: `<limit>`
- Returns JSON object with keys `items`, `total`, `offset`, `limit`.

### 2.2 POST `/api/v1/items`
- Validates request payload against item schema.
- Throws `ValidationError` if any constraints fail.
- Assigns unique `id`, timestamps, saves record, records audit event.
- Returns HTTP 201 Created with created Item representation.

### 2.3 POST `/api/v1/items/export`
- Request payload: `{"format": "json" | "csv", "category": ..., "status": ..., "search": ...}`
- Formats:
  - `json`: Pretty-printed JSON array with MIME `application/json; charset=utf-8`
  - `csv`: RFC 4180 compliant CSV table with header row and MIME `text/csv; charset=utf-8`
- Header: `Content-Disposition: attachment; filename=items_export.<fmt>`

### 2.4 Error Handling Protocol (RFC 7807)
All errors return MIME `application/problem+json` with body:
```json
{
  "type": "https://api.datahub.local/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "Request parameters failed validation checks.",
  "instance": "/api/v1/items",
  "invalid_params": [
    {
      "name": "title",
      "reason": "Title must be at least 3 characters long."
    }
  ]
}
```
HTTP Status Mapping:
- **400 Bad Request**: Validation failure or malformed payload.
- **404 Not Found**: Resource does not exist.
- **409 Conflict**: Duplicate or incompatible state transition.
- **500 Internal Server Error**: Unhandled system exception.
