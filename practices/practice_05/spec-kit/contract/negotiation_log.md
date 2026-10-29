# Negotiation Log: Contract Reconciliation between UI & Logic Teams

**Date**: 2026-10-28  
**Participants**:
- **Team 1 (UI / Frontend)**: Lead Frontend Engineer, UX Designer
- **Team 2 (Logic / Backend)**: Lead Backend Architect, Data Platform Engineer  
**Framework**: Spec-Kit Multi-Team SDD  
**Objective**: Resolve divergences between `team1-ui/spec_v1_draft.md` and `team2-logic/spec_v1_draft.md` to produce an authoritative `unified_contract.yaml` before generating any code.

---

## 1. Divergence Matrix & Reconciliation Decisions

| # | Topic | Team 1 (UI) Initial Draft | Team 2 (Logic) Initial Draft | Agreed Contract Decision | Rationale |
|---|---|---|---|---|---|
| **1** | **API Versioning** | `/api/items` (Unversioned) | `/api/v1/items` (Strict v1) | **`/api/v1/items`** | Guarantees backwards compatibility for future breaking changes. |
| **2** | **Parameter Naming & Casing** | camelCase (`filterCategory`, `sortBy`, `searchQuery`) | snake_case (`category`, `sort_by`, `search`) | **snake_case for HTTP API** | Follows Python, REST, and RFC 3986 conventions; UI deserializes into JS model. |
| **3** | **Entity Identifiers** | Integer numbers (`101`, `102`) | Prefixed string `itm-xxxx` (`item_id`) | **`id: string` with `itm-xxxx`** | Field name `id` standardizes across UI, while prefixed alphanumeric prevents collision. |
| **4** | **Pagination Model** | Client-side memory pagination | Opaque cursor tokens (`next_cursor`) | **`offset` & `limit` with `total` count** | UI data tables require jumping to pages; dataset size (<10k) makes offset pagination optimal. |
| **5** | **Export Workflow** | Synchronous direct GET download | Asynchronous job queue (`/export-jobs`) | **Synchronous `POST /api/v1/items/export`** | For filtered subsets (<=100 records), synchronous streaming simplifies UI without polling complexity. |
| **6** | **Error Format** | Simple `{ "error": "msg" }` | Custom 422 `{ "errors": {...} }` | **RFC 7807 Problem Details** (`application/problem+json`) | Industry standard; provides `type`, `title`, `status`, `detail`, and structured `invalid_params` array. |
| **7** | **Category & Status Enums** | Capitalized strings (`Active`, `DevOps`) | Lowercase strings (`active`, `devops`) | **Strict lowercase in API, localized in UI** | Eliminates serialization bugs; UI translates `active` to badge "Active". |
| **8** | **Validation Boundary** | Title required | Title 3..120 chars; priority 1..5; tags regex | **Enforced strict validation schema** | UI runs client-side validation; server acts as source of truth and returns field-level error pointers. |

---

## 2. Detailed Discussion Notes

### Issue 1: Pagination vs Data Volume
- *Team 1 Argument*: "If we use opaque cursors, our table cannot display 'Page 2 of 5' or allow the user to see the total number of matching items."
- *Team 2 Argument*: "Running `COUNT(*)` in SQL or scanning large datasets is an anti-pattern under high load."
- *Resolution*: Team 2 agreed to compute and return `"total"` in the response body as well as send `X-Total-Count` header, while Team 1 agreed to accept `offset` (default 0) and `limit` (max 100).

### Issue 2: Error Feedback in Modal Dialogs
- *Team 1 Argument*: "When a user submits invalid data in the '+ New Item' modal, an alert popup with a generic message gives terrible UX. We need to highlight which exact input failed."
- *Team 2 Argument*: "We will adopt RFC 7807 (`application/problem+json`). When validation fails with HTTP 400, we provide an `invalid_params` list containing `name` and `reason`."
- *Resolution*: Adopted RFC 7807 with `invalid_params`. Team 1 binds each error to the corresponding form field ID (`errTitle`, `errTags`).

### Issue 3: Direct Download vs Async Queue
- *Team 1 Argument*: "Users expect clicking 'Export CSV' to immediately trigger a browser file download dialog, not a spinner waiting for a background worker."
- *Team 2 Argument*: "Asynchronous jobs prevent thread starvation for giant files."
- *Resolution*: A compromise was established: for the current feature scope, synchronous export generates and streams up to 100 items directly with `Content-Disposition: attachment; filename=...`. If dataset exceeds 10,000 items in future milestones, an async worker will be introduced.

---

## 3. Consensus Sign-Off
Both teams formally signed off on the reconciled specifications (`team1-ui/spec_v2_aligned.md` and `team2-logic/spec_v2_aligned.md`) and the master contract (`unified_contract.yaml`).
