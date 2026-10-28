# Spec-Kit: UI Team Specification (Draft v1 - Pre-Reconciliation)

**Team**: Frontend UI Team  
**Status**: Draft (Initial Proposal before Backend Negotiation)  
**Feature**: DataHub Console - Interactive Filter, Search & Export View

---

## 1. User Interface Overview and Screens

The UI consists of a Single Page Application (SPA) dashboard designed for operators to inspect system records.

### 1.1 Layout Components
1. **Header**: Brand title, overall system status, global action buttons (`Export`, `+ Add Item`).
2. **KPI Stats Bar**: 4 stat counters displaying Total, Active, Pending, and Archived counts.
3. **Filter Control Bar**:
   - Free text search input with instant feedback.
   - Category dropdown (`All`, `Engineering`, `DevOps`, `Security`, `Product`, `Analytics`).
   - Sort selector (`Created Date`, `Priority`, `Title`).
   - Status toggle pill tabs (`All`, `Active`, `Pending`, `Archived`).
4. **Data Grid (Table)**:
   - Columns: `ID`, `Title`, `Category`, `Status`, `Priority`, `Tags`, `Date Created`, `Actions`.
   - Action buttons per row: `Toggle Status`, `Delete`.
5. **Modal Dialog**:
   - Modal for creating a new record with form fields.

---

## 2. Assumed API Calls and Data Model (Frontend Assumptions)

### 2.1 Fetch Items Endpoint
- **URL**: `GET /api/items`
- **Query Parameters (camelCase)**:
  - `searchQuery`: string
  - `filterCategory`: string (values: `Engineering`, `DevOps`, `Security`, etc.)
  - `sortBy`: string (`date`, `priority`, `title`)
  - `sortOrder`: string (`asc`, `desc`)
- **Assumed Response**:
  ```json
  [
    {
      "id": 101,
      "title": "Configure OpenSpec Root",
      "category": "Engineering",
      "status": "Active",
      "priority": 4,
      "tags": ["openspec", "sdd"],
      "createdAt": "2026-10-20"
    }
  ]
  ```
- *Pagination Assumption*: Frontend loads all items into memory and paginates locally on client side.

### 2.2 Create Item Endpoint
- **URL**: `POST /api/items`
- **Payload**:
  ```json
  {
    "title": "New Task",
    "category": "Engineering",
    "status": "Active",
    "priority": 3,
    "tags": ["ci", "tests"]
  }
  ```

### 2.3 Export Data
- **URL**: `GET /api/items/export?format=json` (or `format=csv`)
- Direct browser redirect to download link.

---

## 3. UI State Handling and Error Display

- **Loading State**: Show text "Loading..." in the table body.
- **Empty State**: Show "No items found" when the list is empty.
- **Error State**:
  - If server returns HTTP status != 200, parse body as `{ "error": "error message" }`.
  - Display popup alert: `alert(error.error)`.

---

## 4. Open Questions & Ambiguities Identified for Contract Meeting
- What happens if the server has 10,000 items? Client-side pagination will choke.
- Does the backend use uppercase (`Active`) or lowercase (`active`) for statuses and categories?
- Are IDs integer numbers or string UUIDs?
- How are field validation errors communicated so we can highlight specific inputs in the modal?
