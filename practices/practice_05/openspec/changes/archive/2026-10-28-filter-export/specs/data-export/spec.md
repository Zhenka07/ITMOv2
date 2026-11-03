# Spec Delta: data-export

## Purpose
The data-export capability enables exporting system items into standard portable formats such as JSON arrays and RFC 4180 CSV files with appropriate MIME headers and disposition.

## ADDED Requirements

### Requirement: Export items in JSON format
The system SHALL provide an export endpoint that returns filtered items serialized as a formatted JSON array.

#### Scenario: Successful JSON export
- **WHEN** client sends POST to `/api/v1/items/export` with payload `{"format": "json"}`
- **THEN** server returns status 200 with Content-Type `application/json; charset=utf-8` and attachment header

### Requirement: Export items in CSV format
The system SHALL provide an export endpoint that returns filtered items serialized in RFC 4180 compliant CSV format with header columns.

#### Scenario: Successful CSV export
- **WHEN** client sends POST to `/api/v1/items/export` with payload `{"format": "csv"}`
- **THEN** server returns status 200 with Content-Type `text/csv; charset=utf-8` and CSV column row

### Requirement: Rejection of unsupported export format
The system SHALL reject any requested export format other than json or csv with RFC 7807 problem details.

#### Scenario: Unsupported format rejection
- **WHEN** client sends POST to `/api/v1/items/export` with payload `{"format": "xml"}`
- **THEN** server returns status 400 with Content-Type `application/problem+json` and validation detail
