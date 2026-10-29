# Spec Delta: audit-trail

## Purpose
The audit-trail capability provides immutable event logging for mutating operations on items and data exports.

## ADDED Requirements

### Requirement: Record event on item mutation
The system SHALL append an audit record whenever an item is created, updated, or deleted.

#### Scenario: Successful audit log on item creation
- **GIVEN** an active DataHub server with audit logging enabled
- **WHEN** client sends POST to `/api/v1/items` with a valid item payload
- **THEN** an audit event of type `item.created` is committed to the audit journal

### Requirement: Record event on data export
The system SHALL append an audit record whenever data is exported from the system.

#### Scenario: Audit log on export request
- **GIVEN** an active DataHub server
- **WHEN** client requests data export via `/api/v1/items/export`
- **THEN** an audit event of type `data.exported` is recorded with filter parameters
