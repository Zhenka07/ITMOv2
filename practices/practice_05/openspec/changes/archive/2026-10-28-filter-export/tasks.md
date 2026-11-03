# Tasks

## 1. Storage Filtering and Query Engine

- [x] 1.1 Implement multi-field query filtering (category, status, tags, search) in `ItemStore` and verify unit tests pass.
- [x] 1.2 Implement multi-field sorting and pagination boundaries validation in `ItemStore` and verify edge cases.

## 2. Export Capability

- [x] 2.1 Implement JSON array export in `ItemStore.export` and verify serialized payload.
- [x] 2.2 Implement RFC 4180 CSV export in `ItemStore.export` and verify headers and delimiter escaping.
- [x] 2.3 Expose `/api/v1/items/export` endpoint in HTTP server with Content-Disposition headers.

## 3. UI Dashboard and Verification

- [x] 3.1 Implement search debouncing, category filter dropdown, and status pills in Web UI.
- [x] 3.2 Add export download triggers for JSON and CSV in Web UI.
- [x] 3.3 Validate full integration workflow with automated E2E tests.

## Workflow follow-up

- Validate change proposal using `openspec validate filter-export --type change --strict`.
- Archive change using `openspec archive filter-export` to promote specs to project main specs.
