# Design: Filter and Export System

## Context
See proposal.md for motivation and problem statement. The brownfield application currently stores item records in memory with JSON persistence. We need to introduce multi-parameter filtering, sorting, and multi-format export without adding external heavyweight dependencies or breaking backwards compatibility.

## Goals / Non-Goals

**Goals:**
- Provide zero-dependency filtering and sorting inside `ItemStore`.
- Implement streaming/in-memory CSV generation following RFC 4180 standard.
- Return structured RFC 7807 problem details for invalid query or export payloads.
- Connect interactive frontend dashboard to query endpoints.

**Non-Goals:**
- External relational database migration (SQLite/PostgreSQL) is out of scope for this change.
- Server-side full-text search indexing engines (Elasticsearch/Lucene) are deferred.

## Decisions

- **Decision 1: Use Python standard library `csv` module for CSV export**
  - *Rationale*: Guarantees RFC 4180 compliance, handles comma escaping, quotes, and newlines without third-party dependencies.
  - *Alternative considered*: Manual string formatting (rejected due to CSV injection and delimiter bugs).

- **Decision 2: Return RFC 7807 `application/problem+json` for errors**
  - *Rationale*: Conforms to modern industry standard for HTTP API errors, giving machines and UI clear `invalid_params` arrays.
  - *Alternative considered*: Ad-hoc `{"error": "message"}` (rejected due to lack of standardization and poor UI parsing).

- **Decision 3: Thread-safe in-memory store with file sync**
  - *Rationale*: RLock ensures thread safety across concurrent HTTP requests while keeping zero-config simplicity.

## Risks / Trade-offs

- *[Risk: Memory pressure on large export]* → *Mitigation*: Cap export limit at 100 items per export request in v1.
- *[Risk: Special characters in CSV breaking Excel]* → *Mitigation*: UTF-8 with standard comma separation and clean field quoting.
