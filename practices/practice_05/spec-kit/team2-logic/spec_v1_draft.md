# Spec-Kit: Logic Team Specification (Draft v1 - Pre-Reconciliation)

**Team**: Backend API & Logic Team  
**Status**: Draft (Initial Specification before Frontend Negotiation)  
**Feature**: DataHub Backend - Query Engine, REST API & Persistence Layer

---

## 1. Domain Entities and Schema

### 1.1 Item Entity
- `item_id`: string (Format: `itm-[a-f0-9]{6}`, e.g. `itm-001`)
- `title`: string (min 3, max 120 chars, trimmed)
- `category`: string enum (`engineering`, `devops`, `security`, `product`, `analytics` - lowercase strictly)
- `status`: string enum (`active`, `pending`, `archived` - lowercase strictly)
- `priority`: integer (1 to 5)
- `tags`: array of string (regex: `^[a-zA-Z0-9\-_]{1,30}$`)
- `created_at`: ISO 8601 UTC timestamp string
- `updated_at`: ISO 8601 UTC timestamp string

---

## 2. API Endpoints & Contract (Backend Assumptions)

### 2.1 Query Items Endpoint
- **URL**: `GET /api/v1/items` (Strict API versioning required)
- **Query Parameters (snake_case)**:
  - `search`: string (case-insensitive substring filter)
  - `category`: string (exact match against lowercase enum)
  - `status`: string (exact match against lowercase enum)
  - `sort_by`: string (`created_at`, `priority`, `title`, `updated_at`)
  - `sort_order`: string (`asc`, `desc`, default: `desc`)
  - `cursor`: string (opaque base64 cursor token for keyset pagination)
  - `page_size`: integer (default: 20, max: 50)
- **Assumed Response**:
  ```json
  {
    "data": [
      {
        "item_id": "itm-001",
        "title": "Configure OpenSpec Root Profile",
        "category": "engineering",
        "status": "active",
        "priority": 4,
        "tags": ["openspec", "sdd"],
        "created_at": "2026-10-20T10:00:00Z"
      }
    ],
    "next_cursor": "eyJpdG1faWQiOiAiaXRtLTAwMSJ9",
    "has_more": true
  }
  ```
- *Note*: Keyset pagination without total record counts is used to avoid expensive `COUNT(*)` database scans.

### 2.2 Create Item Endpoint
- **URL**: `POST /api/v1/items`
- **Request Body**:
  ```json
  {
    "title": "Migrate CI Runner to Ubuntu 24.04",
    "category": "devops",
    "status": "active",
    "priority": 3,
    "tags": ["ci-cd", "infra"]
  }
  ```
- **Response**: HTTP 201 Created with full entity representation.

### 2.3 Export Architecture
- **URL**: `POST /api/v1/export-jobs`
- *Design*: Asynchronous batch job returning `{ "job_id": "job-1092" }`, requiring the client to poll `GET /api/v1/export-jobs/{id}` until download URL is ready.

---

## 3. Error Model & Status Codes

- Validation errors return HTTP 422 Unprocessable Entity:
  ```json
  {
    "error_code": "ERR_VALIDATION",
    "message": "Payload schema failed validation",
    "errors": {
      "title": "Field required and must be >= 3 characters"
    }
  }
  ```
- Not found returns HTTP 404 with plain message.

---

## 4. Open Questions & Ambiguities Identified for Contract Meeting
- Frontend wants synchronous file download, but backend designed an asynchronous export job queue. Can we compromise on a direct synchronous export for up to 100 items?
- Frontend requested camelCase parameters, while backend standard is snake_case and RFC 3986 URLs.
- Frontend table pagination expects offset/limit and total item count (`X-Total-Count` or `total`), but backend proposed opaque cursor tokens.
- We need a standardized error format like RFC 7807 (Problem Details) instead of custom ad-hoc error JSON.
