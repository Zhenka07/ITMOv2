# Design: Audit Logging System (After Rule Applied)

## Context
See proposal.md - Why. Current system lacks centralized audit trail for state-mutating requests.

## Goals / Non-Goals

**Goals:**
- Record audit event on every POST, PATCH, DELETE and export request.
- Log event timestamp, actor, action, and resource id.

**Non-Goals:**
- External SIEM integration.

## Decisions

- **Decision 1: Synchronous logging to audit journal buffer**
  - *Rationale*: Low complexity, zero external dependencies.
- **Decision 2: JSONLines format for audit logs**
  - *Rationale*: Easy to parse and stream.

## Architecture and Interaction (Mermaid Diagram)

```mermaid
sequenceDiagram
    autonumber
    actor Client as Client / Operator
    participant Server as HTTP Handler (server.py)
    participant Validator as Validator (models.py)
    participant Store as ItemStore (storage.py)
    participant Audit as Audit Journal
    
    Client->>Server: HTTP Mutation Request (POST / PATCH / DELETE)
    Server->>Validator: validate_item_input(data)
    alt Validation Failure
        Validator-->>Server: ValidationError (invalid_params)
        Server-->>Client: 400 Problem Details (RFC 7807)
    else Validation Success
        Validator-->>Server: Clean Data
        Server->>Store: execute_mutation()
        Store-->>Server: Mutation Result (Item)
        Server->>Audit: record_event(action, actor, resource_id, timestamp)
        Audit-->>Server: Event Acknowledged
        Server-->>Client: 200 / 201 Success Response
    end
```

## Risks / Trade-offs

- *[Risk: Disk I/O bottleneck]* → *Mitigation*: Append-only JSONL writes with buffered stream flush.
