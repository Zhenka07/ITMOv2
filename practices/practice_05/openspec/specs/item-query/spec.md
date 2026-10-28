# item-query Specification

## Purpose
The item-query capability allows searching, category and status filtering, tag isolation, and multi-field sorting over the system item collection with strict pagination parameters.

## Requirements

### Requirement: Filter items by status and category
The system SHALL filter items according to query parameters category and status, returning only records matching all specified criteria.

#### Scenario: Filter by category and status
- **WHEN** client sends GET to `/api/v1/items?category=devops&status=active`
- **THEN** server returns status 200 with list of items whose category is devops and status is active

### Requirement: Search items by text query
The system SHALL match substring search terms against item title, description, and tags case-insensitively.

#### Scenario: Substring text search
- **WHEN** client sends GET to `/api/v1/items?search=runner`
- **THEN** server returns status 200 containing items that match the term runner

### Requirement: Pagination boundaries validation
The system SHALL validate limit and offset parameters and reject invalid values with RFC 7807 problem details.

#### Scenario: Negative offset rejection
- **WHEN** client sends GET to `/api/v1/items?offset=-5`
- **THEN** server returns status 400 with Content-Type `application/problem+json`
