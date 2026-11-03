# Spec-Kit: UI Team Specification (Aligned v2 - Post-Reconciliation)

**Team**: Frontend UI Team  
**Status**: Approved & Reconciled (Contract Signed)  
**Feature**: DataHub Console - Interactive Filter, Search & Export View

---

## 1. Reconciled Screen Architecture & State Machine

The UI follows a deterministic state machine:

```text
[IDLE / MOUNT]
      │
      ▼
  [LOADING] ──────────► (Fetch /api/v1/items)
      │
      ├─── HTTP 200 (items.length > 0) ──► [SUCCESS / RENDER_TABLE]
      ├─── HTTP 200 (items.length == 0) ──► [EMPTY_STATE]
      └─── HTTP 4xx / 5xx / Network ─────► [ERROR_BANNER / RFC_7807]
```

### 1.1 State Definitions
- **LOADING**: Display table row skeleton with text `"Загрузка данных..."`. Disable export buttons temporarily.
- **SUCCESS**: Render item rows, bind status toggles and delete triggers. Update top summary statistics.
- **EMPTY_STATE**: Display centered message `"Записей не найдено по заданным фильтрам."`.
- **ERROR_BANNER**: Parse `application/problem+json` payload, extract `title` and `detail`, display prominent red alert banner with error message.

---

## 2. Reconciled API Integration Contracts

### 2.1 Query Items
- **URL**: `GET /api/v1/items`
- **Query Parameters**:
  - `search` (string, debounced by 250ms)
  - `category` (lowercase enum: `engineering`, `devops`, `security`, `product`, `analytics`)
  - `status` (lowercase enum: `active`, `pending`, `archived`)
  - `sort_by` (`created_at`, `priority`, `title`)
  - `sort_order` (`asc`, `desc`)
  - `offset` (integer >= 0)
  - `limit` (integer 1..100)
- **Response**:
  ```json
  {
    "items": [
      {
        "id": "itm-001",
        "title": "Configure OpenSpec Root Profile",
        "category": "engineering",
        "status": "active",
        "priority": 4,
        "tags": ["openspec", "sdd"],
        "created_at": "2026-10-20T10:00:00Z",
        "updated_at": "2026-10-20T10:00:00Z"
      }
    ],
    "total": 5,
    "offset": 0,
    "limit": 20
  }
  ```

### 2.2 Create Item Modal & Field Validation Error Binding
- **URL**: `POST /api/v1/items`
- **Request**:
  ```json
  {
    "title": "string (3..120 chars)",
    "category": "engineering",
    "status": "active",
    "priority": 1..5,
    "tags": ["tag1", "tag2"],
    "description": "optional string"
  }
  ```
- **Error Handling (RFC 7807 Binding)**:
  When response status is 400 (`application/problem+json`):
  Iterate over `invalid_params`:
  - If `name == "title"`: display inline red label under `#fTitle` with `param.reason`.
  - If `name == "tags"`: display inline red label under `#fTags` with `param.reason`.

### 2.3 Direct Data Export
- **URL**: `POST /api/v1/items/export`
- **Request Body**:
  ```json
  {
    "format": "json" | "csv",
    "category": null | "engineering",
    "status": null | "active",
    "search": null | "query"
  }
  ```
- **Handling**:
  Read response as `Blob`, construct temporary object URL via `window.URL.createObjectURL(blob)`, click virtual `<a download="datahub_export.ext">` tag to initiate native browser download.
