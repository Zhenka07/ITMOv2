# Diff Summary: Spec-Kit Pre- vs Post-Reconciliation Changes

This document summarizes the contractual changes made between Draft v1 and Aligned v2 specifications across both the UI and Logic teams.

---

## 1. UI Specification Changes (Team 1)

### Key Modifications:
- **Endpoints**: Updated `/api/items` → `/api/v1/items`, `/api/items/export` → `/api/v1/items/export`.
- **Query Parameters**: Renamed `filterCategory` → `category`, `sortBy` → `sort_by`, `sortOrder` → `sort_order`, `searchQuery` → `search`.
- **Pagination Architecture**: Replaced client-side array slicing with server-side offset pagination (`offset`, `limit`) and consumed `total` property.
- **Enums**: Converted uppercase values (`Engineering`, `Active`) to lowercase (`engineering`, `active`) in network payloads; added client-side display mapping.
- **Error Handling**: Replaced generic `alert(error.error)` with RFC 7807 problem details parser and form field error highlighter (`invalid_params`).

---

## 2. Logic Specification Changes (Team 2)

### Key Modifications:
- **Pagination Model**: Replaced opaque cursor tokens (`next_cursor`) with standard `offset` / `limit` and computed `total` response count to satisfy UI data grid needs.
- **Export Mechanism**: Replaced asynchronous job polling (`POST /api/v1/export-jobs`) with a direct streaming `POST /api/v1/items/export` endpoint for immediate browser downloads (<=100 records).
- **Identifier Naming**: Renamed internal `item_id` key to standard `id` in JSON output.
- **Error Response Protocol**: Formally adopted RFC 7807 (`application/problem+json`) with standard `invalid_params` array.
- **Headers**: Added `X-Total-Count`, `X-Offset`, `X-Limit` headers to `GET /api/v1/items` responses.

---

## 3. Side-by-Side Parameter Mapping

| Dimension | Team 1 (UI) Draft v1 | Team 2 (Logic) Draft v1 | Unified Contract v2 |
|---|---|---|---|
| Item ID | `id: 101` (Number) | `item_id: "itm-001"` (String) | `id: "itm-001"` (String) |
| Category Param | `filterCategory` | `category` | `category` |
| Sort Field | `sortBy` | `sort_by` | `sort_by` |
| Sort Direction | `sortOrder` | `sort_order` | `sort_order` |
| Search Query | `searchQuery` | `search` | `search` |
| Pagination Keys | (none, client-side) | `cursor`, `page_size` | `offset`, `limit`, `total` |
| Error Schema | `{ "error": "msg" }` | `{ "error_code": "ERR", ... }` | RFC 7807 Problem Details |
| Export Endpoint | `GET /api/items/export` | `POST /api/v1/export-jobs` | `POST /api/v1/items/export` |
