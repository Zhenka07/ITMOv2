# Proposal: Audit Logging System

## Why
Security and compliance standards require recording state changes, deletions, and exports in a tamper-evident audit journal. Adding audit logging provides traceability for administrative actions.

## What Changes
- Add asynchronous event emitter for state changes (`item.created`, `item.updated`, `item.deleted`, `data.exported`).
- Record audit trails with timestamp, actor IP/ID, action type, and target resource ID.
- Provide query interface for security operators to inspect audit events.

## Capabilities

### New Capabilities
- `audit-trail`: Immutable event log capturing mutating actions on DataHub items.

### Modified Capabilities
<!-- None -->

## Impact
- Adds audit interceptor to `server.py` and `storage.py`.
- No disruption to existing GET endpoints.
