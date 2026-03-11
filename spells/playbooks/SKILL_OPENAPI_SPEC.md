---
name: SKILL_OPENAPI_SPEC
description: "Author, validate, generate, and consume OpenAPI 3.x specifications for AEC automation APIs. Use when designing REST endpoints that expose scope extraction results, RFI/submittal logs, corpus registries, GIS features, or session state to external tools, dashboards, or inter-script communication. Covers spec structure, path/schema design, authentication patterns, code generation (client and server stubs), contract testing, and versioning. Triggers: 'OpenAPI', 'API spec', 'REST API', 'swagger', 'YAML spec', 'API design', 'endpoint', 'schema', 'code generation', 'API contract', 'FastAPI', 'inter-script API'."
---

# SKILL_OPENAPI_SPEC — OpenAPI Specification Skill

> **Scope:** Authoring and consuming OpenAPI 3.x specifications as the contract layer
> between all AEC automation scripts. Every script that exposes data to another script,
> dashboard, or external tool must have a machine-readable OpenAPI spec.
> Covers spec authoring in YAML, schema design, FastAPI auto-generation, client/server
> code generation, contract testing, and versioning strategy.
> For the data structures exposed by these APIs see:
> `SKILL_AEC_SCOPE_EXTRACTION` (scope items, RFIs, trade matrix),
> `SKILL_AEC_RFI_SUBMITTAL` (RFI/submittal records),
> `SKILL_GIS_GEOSPATIAL` (GeoJSON feature collections),
> `SKILL_LLM_SESSION_STATE` (session registers).

## Quick Reference

| Task | Section |
|------|---------|
| OpenAPI 3.x document structure | [Document Structure](#document-structure) |
| Info, servers, security blocks | [Info Servers Security](#info-servers-security) |
| Path and operation design | [Path and Operation Design](#path-and-operation-design) |
| Schema authoring — objects, arrays, enums | [Schema Authoring](#schema-authoring) |
| AEC domain schemas | [AEC Domain Schemas](#aec-domain-schemas) |
| Request/response patterns | [Request Response Patterns](#request-response-patterns) |
| FastAPI — auto-generate spec from code | [FastAPI Auto-Generation](#fastapi-auto-generation) |
| Client code generation | [Client Code Generation](#client-code-generation) |
| Server stub generation | [Server Stub Generation](#server-stub-generation) |
| Contract testing | [Contract Testing](#contract-testing) |
| Versioning strategy | [Versioning Strategy](#versioning-strategy) |
| Validation & QA | [Validation & QA](#validation--qa) |

---

## Document Structure

An OpenAPI 3.x document is a single YAML (or JSON) file with seven top-level keys.

```yaml
openapi: "3.1.0"          # spec version — use 3.1.0 (JSON Schema alignment)

info: ...                  # API identity and version
servers: ...               # base URLs for each environment
paths: ...                 # endpoint definitions
components: ...            # reusable schemas, parameters, responses, securitySchemes
security: ...              # global security requirement (can override per-operation)
tags: ...                  # grouping labels shown in documentation UIs
```

### Minimal Valid Document

```yaml
openapi: "3.1.0"
info:
  title: AEC Automation API
  version: "1.0.0"
  description: |
    Internal API connecting scope extraction, RFI management,
    corpus registry, and GIS services for AEC project automation.
servers:
  - url: http://localhost:8000
    description: Local development
paths:
  /health:
    get:
      summary: Health check
      operationId: health_check
      responses:
        "200":
          description: API is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status: { type: string, example: "ok" }
```

---

## Info Servers Security

### Info Block

```yaml
info:
  title: AEC Project Automation API
  version: "2.1.0"
  description: |
    Exposes scope baseline, RFI/submittal logs, corpus registry,
    and GIS data for the AEC project automation pipeline.
    All endpoints require project_id scoping.
  contact:
    name: Platform Team
    email: platform@example.com
  license:
    name: Proprietary
    identifier: LicenseRef-Proprietary
```

### Servers Block

```yaml
servers:
  - url: https://api.aec-platform.internal/v2
    description: Production
  - url: https://staging.aec-platform.internal/v2
    description: Staging
  - url: http://localhost:8000
    description: Local development
  - url: "{protocol}://{host}:{port}"
    description: Custom deployment
    variables:
      protocol:
        enum: [http, https]
        default: https
      host:
        default: localhost
      port:
        default: "8000"
```

### Security Schemes

```yaml
components:
  securitySchemes:

    ApiKeyHeader:
      type: apiKey
      in: header
      name: X-API-Key
      description: Static API key for service-to-service calls

    BearerJWT:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT issued by the auth service; include in Authorization header

    OAuth2:
      type: oauth2
      flows:
        clientCredentials:
          tokenUrl: https://auth.aec-platform.internal/token
          scopes:
            scope:read:    Read scope baseline and RFI logs
            scope:write:   Write extracted scope items
            rfi:read:      Read RFI/submittal logs
            rfi:write:     Create and update RFIs and submittals
            corpus:admin:  Manage document corpus

# Apply security globally (override per-operation for public endpoints)
security:
  - BearerJWT: []

# Override per-operation:
# paths:
#   /health:
#     get:
#       security: []   # public endpoint — no auth required
```

---

## Path and Operation Design

### Path Conventions for AEC APIs

```
Noun-first, resource-oriented:
  /projects/{project_id}/scope-items
  /projects/{project_id}/rfis
  /projects/{project_id}/submittals
  /projects/{project_id}/corpus
  /projects/{project_id}/gis/features

Avoid verbs in paths:
  WRONG: /projects/{project_id}/get-rfis
  RIGHT: GET /projects/{project_id}/rfis

Filtering via query parameters, not path:
  /projects/{project_id}/rfis?priority=FATAL&status=OPEN

Sub-resources:
  /projects/{project_id}/rfis/{rfi_number}/response
  /projects/{project_id}/submittals/{submittal_number}/disposition
```

### Operation Template

```yaml
paths:
  /projects/{project_id}/rfis:

    get:
      summary: List RFIs for a project
      description: |
        Returns a paginated list of RFI records. Filter by priority,
        status, discipline, or spec section. Sorted by RFI number by default.
      operationId: list_rfis
      tags: [RFIs]
      parameters:
        - $ref: "#/components/parameters/ProjectId"
        - $ref: "#/components/parameters/PageParam"
        - $ref: "#/components/parameters/PageSizeParam"
        - name: priority
          in: query
          schema:
            type: string
            enum: [FATAL, HIGH, ADVISORY]
        - name: status
          in: query
          schema:
            type: string
            enum: [DRAFT, ISSUED, UNDER_REVIEW, ANSWERED, OVERDUE,
                   ESCALATED, CLOSED_ANSWERED, CLOSED_VOID, CLOSED_SUPERSEDED]
        - name: discipline
          in: query
          schema:
            type: string
        - name: overdue_only
          in: query
          schema:
            type: boolean
            default: false
      responses:
        "200":
          description: Paginated list of RFIs
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/RFIListResponse"
        "400": { $ref: "#/components/responses/BadRequest" }
        "401": { $ref: "#/components/responses/Unauthorized" }
        "404": { $ref: "#/components/responses/NotFound" }

    post:
      summary: Create a new RFI
      operationId: create_rfi
      tags: [RFIs]
      parameters:
        - $ref: "#/components/parameters/ProjectId"
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/RFICreate"
      responses:
        "201":
          description: RFI created
          headers:
            Location:
              description: URL of the created RFI
              schema: { type: string, format: uri }
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/RFI"
        "409":
          description: RFI number already exists
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"

  /projects/{project_id}/rfis/{rfi_number}:

    get:
      summary: Get a single RFI
      operationId: get_rfi
      tags: [RFIs]
      parameters:
        - $ref: "#/components/parameters/ProjectId"
        - $ref: "#/components/parameters/RFINumber"
      responses:
        "200":
          description: RFI record
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/RFI"
        "404": { $ref: "#/components/responses/NotFound" }

    patch:
      summary: Update an RFI (partial)
      operationId: update_rfi
      tags: [RFIs]
      parameters:
        - $ref: "#/components/parameters/ProjectId"
        - $ref: "#/components/parameters/RFINumber"
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/RFIUpdate"
      responses:
        "200":
          description: Updated RFI
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/RFI"
        "404": { $ref: "#/components/responses/NotFound" }
        "409":
          description: Conflict — e.g. attempt to modify a closed RFI
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
```

### Reusable Parameters

```yaml
components:
  parameters:

    ProjectId:
      name: project_id
      in: path
      required: true
      description: Unique project identifier
      schema:
        type: string
        pattern: "^[A-Z0-9]{2,12}$"
        example: "2401"

    RFINumber:
      name: rfi_number
      in: path
      required: true
      description: RFI number — immutable after issue
      schema:
        type: string
        pattern: "^RFI-\\d{3,4}$"
        example: "RFI-042"

    SubmittalNumber:
      name: submittal_number
      in: path
      required: true
      schema:
        type: string
        pattern: "^SUB-\\d{4}$"
        example: "SUB-0142"

    PageParam:
      name: page
      in: query
      schema:
        type: integer
        minimum: 1
        default: 1

    PageSizeParam:
      name: page_size
      in: query
      schema:
        type: integer
        minimum: 1
        maximum: 200
        default: 50
```

### Standard Error Responses

```yaml
components:
  responses:

    BadRequest:
      description: Invalid request parameters or body
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/Error"

    Unauthorized:
      description: Missing or invalid authentication
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/Error"

    Forbidden:
      description: Authenticated but not authorized for this resource
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/Error"

    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/Error"

    Conflict:
      description: State conflict — e.g. duplicate ID or invalid status transition
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/Error"

    UnprocessableEntity:
      description: Validation error on request body fields
      content:
        application/json:
          schema:
            $ref: "#/components/schemas/ValidationError"
```

---

## Schema Authoring

### Core Schema Patterns

```yaml
components:
  schemas:

    # ── Primitive types ────────────────────────────────────────────────────────
    ProjectId:
      type: string
      pattern: "^[A-Z0-9]{2,12}$"
      example: "2401"

    ISODate:
      type: string
      format: date
      example: "2024-03-15"

    # ── Enum ───────────────────────────────────────────────────────────────────
    RFIPriority:
      type: string
      enum: [FATAL, HIGH, ADVISORY]
      description: |
        FATAL — blocks trade/system pricing; response required before bid.
        HIGH  — blocks specific scope items; response required before bid.
        ADVISORY — risk item; price with assumption if no response.

    RFIStatus:
      type: string
      enum:
        - DRAFT
        - ISSUED
        - UNDER_REVIEW
        - ANSWERED
        - OVERDUE
        - ESCALATED
        - CLOSED_ANSWERED
        - CLOSED_VOID
        - CLOSED_SUPERSEDED

    EvidenceStatus:
      type: string
      enum:
        - VERIFIED
        - AMBIGUOUS
        - CONTRADICTORY
        - SUPERSEDED
        - OPERATOR_DIRECTIVE
        - UNDEFINED
        - MISSING_UPSTREAM
        - INFERRED

    ConditionClass:
      type: string
      enum:
        - NEW_WORK_REQUIRED
        - EXISTING_TO_REMAIN
        - EXISTING_TO_REMOVE
        - EXISTING_REFERENCE_ONLY

    # ── Object with required fields ────────────────────────────────────────────
    Error:
      type: object
      required: [code, message]
      properties:
        code:
          type: string
          example: "RFI_NOT_FOUND"
        message:
          type: string
          example: "RFI-042 does not exist for project 2401"
        detail:
          type: string
          nullable: true
        request_id:
          type: string
          format: uuid

    ValidationError:
      type: object
      required: [code, message, fields]
      properties:
        code:    { type: string, example: "VALIDATION_ERROR" }
        message: { type: string }
        fields:
          type: array
          items:
            type: object
            properties:
              field:   { type: string }
              message: { type: string }

    # ── Pagination envelope ────────────────────────────────────────────────────
    Pagination:
      type: object
      required: [page, page_size, total_items, total_pages]
      properties:
        page:        { type: integer, minimum: 1 }
        page_size:   { type: integer, minimum: 1 }
        total_items: { type: integer, minimum: 0 }
        total_pages: { type: integer, minimum: 0 }
        next:        { type: string, format: uri, nullable: true }
        previous:    { type: string, format: uri, nullable: true }
```

### Schema Composition — allOf / oneOf / anyOf

```yaml
# allOf — combine base schema with extension (inheritance)
SubmittalReview:
  allOf:
    - $ref: "#/components/schemas/Submittal"
    - type: object
      required: [disposition, reviewed_by, date_reviewed]
      properties:
        disposition:
          $ref: "#/components/schemas/SubmittalDisposition"
        reviewed_by:   { type: string }
        date_reviewed: { type: string, format: date }
        review_comments: { type: string, nullable: true }

# oneOf — exactly one of these schemas (discriminated union)
ScopeItemOrRFI:
  oneOf:
    - $ref: "#/components/schemas/ScopeItem"
    - $ref: "#/components/schemas/RFI"
  discriminator:
    propertyName: record_type
    mapping:
      scope_item: "#/components/schemas/ScopeItem"
      rfi:        "#/components/schemas/RFI"

# anyOf — matches one or more (use sparingly — harder to validate)
```

### Nullable vs Optional

```yaml
# OpenAPI 3.1 — use JSON Schema null type union
# Field is required but can be null:
cost_impact:
  type: [string, "null"]
  example: "TBD"

# Field is optional (may be absent entirely) — omit from required list
# Field is optional AND nullable — omit from required AND use type: [T, "null"]

# OpenAPI 3.0 (older) used nullable: true — avoid for new specs
```

---

## AEC Domain Schemas

Full schemas for the core AEC data structures exposed by the pipeline APIs.

```yaml
components:
  schemas:

    # ── RFI ───────────────────────────────────────────────────────────────────
    RFI:
      type: object
      required:
        - rfi_number
        - project_id
        - priority
        - discipline
        - subject
        - question
        - status
        - date_issued
        - response_due
      properties:
        rfi_number:      { type: string, pattern: "^RFI-\\d{3,4}$" }
        project_id:      { $ref: "#/components/schemas/ProjectId" }
        priority:        { $ref: "#/components/schemas/RFIPriority" }
        discipline:      { type: string }
        spec_section:    { type: string, pattern: "^\\d{2} \\d{2} \\d{2}$" }
        drawing_ref:     { type: string }
        subject:         { type: string, maxLength: 80 }
        question:        { type: string }
        background:      { type: string }
        date_issued:     { type: string, format: date }
        response_due:    { type: string, format: date }
        date_answered:   { type: [string, "null"], format: date }
        date_closed:     { type: [string, "null"], format: date }
        issued_by:       { type: string }
        issued_to:       { type: string }
        answered_by:     { type: string }
        status:          { $ref: "#/components/schemas/RFIStatus" }
        response:        { type: string }
        cost_impact:     { type: [string, "null"] }
        schedule_impact: { type: [string, "null"] }
        affected_scope:
          type: array
          items: { type: string }
        source_register: { type: string }
        source_entry_id: { type: string }
        days_open:       { type: [integer, "null"], readOnly: true }
        days_overdue:    { type: [integer, "null"], readOnly: true }

    RFICreate:
      type: object
      required: [priority, discipline, subject, question, issued_by, issued_to]
      properties:
        priority:        { $ref: "#/components/schemas/RFIPriority" }
        discipline:      { type: string }
        spec_section:    { type: string }
        drawing_ref:     { type: string }
        subject:         { type: string, maxLength: 80 }
        question:        { type: string }
        background:      { type: string }
        issued_by:       { type: string }
        issued_to:       { type: string }
        response_days:   { type: integer, minimum: 1, default: 10 }
        affected_scope:  { type: array, items: { type: string } }
        source_register: { type: string }
        source_entry_id: { type: string }

    RFIUpdate:
      type: object
      description: Partial update — all fields optional
      properties:
        status:          { $ref: "#/components/schemas/RFIStatus" }
        response:        { type: string }
        answered_by:     { type: string }
        cost_impact:     { type: string }
        schedule_impact: { type: string }
        response_source: { type: string }

    RFIListResponse:
      type: object
      required: [items, pagination]
      properties:
        items:
          type: array
          items: { $ref: "#/components/schemas/RFI" }
        pagination: { $ref: "#/components/schemas/Pagination" }
        summary:
          type: object
          properties:
            total:   { type: integer }
            open:    { type: integer }
            overdue: { type: integer }
            fatal:   { type: integer }

    # ── Scope Item ────────────────────────────────────────────────────────────
    ScopeItem:
      type: object
      required:
        - item_id
        - trade
        - csi_division
        - description
        - condition_class
        - evidence_status
        - source_anchor
        - cost_ability
      properties:
        item_id:         { type: string, pattern: "^SCOPE-[A-Z]+-\\d{3}$" }
        trade:           { type: string }
        csi_division:    { type: string }
        description:     { type: string }
        condition_class: { $ref: "#/components/schemas/ConditionClass" }
        evidence_status: { $ref: "#/components/schemas/EvidenceStatus" }
        source_anchor:   { type: string }
        source_family:   { type: string }
        source_doc_id:   { type: string }
        quantity:        { type: [number, "null"] }
        unit:            { type: [string, "null"] }
        qualifiers:
          type: array
          items: { type: string }
        explicit_exclusions:
          type: array
          items: { type: string }
        cost_ability:
          type: string
          enum: [COSTABLE, PARTIAL, NOT_COSTABLE, NOT_SCOPE, OPERATOR_ONLY]
        rfi_required:    { type: boolean }
        rfi_id:          { type: [string, "null"] }
        active:          { type: boolean, default: true }

    # ── GeoJSON Feature Collection (pass-through) ─────────────────────────────
    GeoJSONFeatureCollection:
      type: object
      required: [type, features]
      properties:
        type:
          type: string
          enum: [FeatureCollection]
        features:
          type: array
          items:
            $ref: "#/components/schemas/GeoJSONFeature"

    GeoJSONFeature:
      type: object
      required: [type, geometry, properties]
      properties:
        type:
          type: string
          enum: [Feature]
        geometry:
          $ref: "#/components/schemas/GeoJSONGeometry"
        properties:
          type: object
          additionalProperties: true

    GeoJSONGeometry:
      oneOf:
        - $ref: "#/components/schemas/GeoJSONPoint"
        - $ref: "#/components/schemas/GeoJSONLineString"
        - $ref: "#/components/schemas/GeoJSONPolygon"
      discriminator:
        propertyName: type

    GeoJSONPoint:
      type: object
      required: [type, coordinates]
      properties:
        type:        { type: string, enum: [Point] }
        coordinates:
          type: array
          items: { type: number }
          minItems: 2
          maxItems: 3

    GeoJSONLineString:
      type: object
      required: [type, coordinates]
      properties:
        type:        { type: string, enum: [LineString] }
        coordinates:
          type: array
          items:
            type: array
            items: { type: number }
            minItems: 2

    GeoJSONPolygon:
      type: object
      required: [type, coordinates]
      properties:
        type:        { type: string, enum: [Polygon] }
        coordinates:
          type: array
          items:
            type: array
            items:
              type: array
              items: { type: number }
              minItems: 2
```

---

## Request Response Patterns

### Pagination Pattern

```yaml
# Request
GET /projects/{project_id}/scope-items?page=2&page_size=50&trade=Structural

# Response envelope — always wrap list responses
{
  "items": [ ... ],
  "pagination": {
    "page": 2,
    "page_size": 50,
    "total_items": 347,
    "total_pages": 7,
    "next": "/projects/2401/scope-items?page=3&page_size=50",
    "previous": "/projects/2401/scope-items?page=1&page_size=50"
  }
}
```

### Bulk Operations

```yaml
  /projects/{project_id}/rfis/bulk:
    post:
      summary: Create multiple RFIs in one request
      operationId: bulk_create_rfis
      tags: [RFIs]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [items]
              properties:
                items:
                  type: array
                  items:
                    $ref: "#/components/schemas/RFICreate"
                  minItems: 1
                  maxItems: 100
      responses:
        "207":
          description: Multi-status — check each item result
          content:
            application/json:
              schema:
                type: object
                properties:
                  results:
                    type: array
                    items:
                      type: object
                      properties:
                        index:   { type: integer }
                        status:  { type: integer }
                        rfi:     { $ref: "#/components/schemas/RFI" }
                        error:   { $ref: "#/components/schemas/Error" }
```

### Long-Running Operations (Async)

```yaml
  /projects/{project_id}/corpus/extract:
    post:
      summary: Trigger scope extraction (async)
      description: |
        Initiates a background extraction job. Returns a job ID.
        Poll /jobs/{job_id} for status.
      operationId: trigger_extraction
      tags: [Corpus]
      responses:
        "202":
          description: Extraction job accepted
          headers:
            Location:
              description: URL to poll for job status
              schema: { type: string, format: uri }
          content:
            application/json:
              schema:
                type: object
                required: [job_id, status]
                properties:
                  job_id:    { type: string, format: uuid }
                  status:    { type: string, enum: [QUEUED] }
                  poll_url:  { type: string, format: uri }

  /jobs/{job_id}:
    get:
      summary: Poll async job status
      operationId: get_job_status
      tags: [Jobs]
      parameters:
        - name: job_id
          in: path
          required: true
          schema: { type: string, format: uuid }
      responses:
        "200":
          description: Job status
          content:
            application/json:
              schema:
                type: object
                required: [job_id, status]
                properties:
                  job_id:     { type: string, format: uuid }
                  status:
                    type: string
                    enum: [QUEUED, RUNNING, COMPLETE, FAILED]
                  progress:   { type: integer, minimum: 0, maximum: 100 }
                  result_url: { type: [string, "null"], format: uri }
                  error:      { $ref: "#/components/schemas/Error" }
```

### File Upload (Corpus Ingestion)

```yaml
  /projects/{project_id}/corpus/documents:
    post:
      summary: Upload a document to the corpus
      operationId: upload_document
      tags: [Corpus]
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required: [file, family_code]
              properties:
                file:
                  type: string
                  format: binary
                family_code:
                  type: string
                  enum: [ADD, RFI, BID, SPEC, DWG, GEOTECH, NARRATIVE, COLLAT]
                identifier:
                  type: string
                issue_date:
                  type: string
                  format: date
```

---

## FastAPI Auto-Generation

FastAPI generates an OpenAPI spec automatically from Python type annotations.
This is the preferred approach — code is the source of truth, spec is derived.

### FastAPI App Structure

```python
from fastapi import FastAPI, HTTPException, Query, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import date
import uvicorn

app = FastAPI(
    title       = "AEC Automation API",
    version     = "2.1.0",
    description = "Scope, RFI, Submittal, Corpus, and GIS services",
    openapi_url = "/openapi.json",
    docs_url    = "/docs",         # Swagger UI
    redoc_url   = "/redoc",        # ReDoc
)
```

### Pydantic Models → OpenAPI Schemas

```python
from pydantic import BaseModel, Field, model_validator
from typing import Optional, Annotated
from datetime import date
from enum import Enum

class RFIPriority(str, Enum):
    FATAL    = "FATAL"
    HIGH     = "HIGH"
    ADVISORY = "ADVISORY"

class RFIStatus(str, Enum):
    DRAFT              = "DRAFT"
    ISSUED             = "ISSUED"
    UNDER_REVIEW       = "UNDER_REVIEW"
    ANSWERED           = "ANSWERED"
    OVERDUE            = "OVERDUE"
    CLOSED_ANSWERED    = "CLOSED_ANSWERED"
    CLOSED_VOID        = "CLOSED_VOID"
    CLOSED_SUPERSEDED  = "CLOSED_SUPERSEDED"

class RFICreate(BaseModel):
    priority:        RFIPriority
    discipline:      str
    spec_section:    str         = Field("", pattern=r"^\d{2} \d{2} \d{2}$|^$")
    drawing_ref:     str         = ""
    subject:         str         = Field(..., max_length=80)
    question:        str
    background:      str         = ""
    issued_by:       str
    issued_to:       str
    response_days:   int         = Field(10, ge=1, le=90)
    affected_scope:  list[str]   = []
    source_register: str         = ""
    source_entry_id: str         = ""

    model_config = {"json_schema_extra": {
        "example": {
            "priority":      "HIGH",
            "discipline":    "Structural",
            "spec_section":  "05 12 00",
            "subject":       "Conflicting slab thickness specification",
            "question":      "Drawing S2.1 shows 6\" slab; Spec 03 30 00 §2.1 specifies 8\". Which governs?",
            "issued_by":     "General Contractor",
            "issued_to":     "Architect of Record",
            "response_days": 10,
        }
    }}


class RFI(RFICreate):
    rfi_number:      str
    project_id:      str
    status:          RFIStatus   = RFIStatus.ISSUED
    date_issued:     date
    response_due:    date
    date_answered:   Optional[date] = None
    date_closed:     Optional[date] = None
    answered_by:     str            = ""
    response:        str            = ""
    cost_impact:     Optional[str]  = None
    schedule_impact: Optional[str]  = None
    days_open:       Optional[int]  = None    # computed, read-only
    days_overdue:    Optional[int]  = None    # computed, read-only

    model_config = {"from_attributes": True}


class PaginatedRFIResponse(BaseModel):
    items:      list[RFI]
    pagination: "Pagination"
    summary:    "RFISummary"

class Pagination(BaseModel):
    page:        int
    page_size:   int
    total_items: int
    total_pages: int
    next:        Optional[str] = None
    previous:    Optional[str] = None

class RFISummary(BaseModel):
    total:   int
    open:    int
    overdue: int
    fatal:   int
```

### FastAPI Route Definitions

```python
from fastapi import APIRouter

rfi_router = APIRouter(prefix="/projects/{project_id}/rfis", tags=["RFIs"])

@rfi_router.get("", response_model=PaginatedRFIResponse)
async def list_rfis(
    project_id:   str,
    priority:     Optional[RFIPriority] = Query(None),
    status:       Optional[RFIStatus]   = Query(None),
    discipline:   Optional[str]         = Query(None),
    overdue_only: bool                  = Query(False),
    page:         int                   = Query(1, ge=1),
    page_size:    int                   = Query(50, ge=1, le=200),
):
    """
    List RFIs for a project with filtering and pagination.
    Sorted by RFI number (ascending) by default.
    """
    # Implementation: query database/registry
    raise HTTPException(status_code=501, detail="Not implemented")


@rfi_router.post("", response_model=RFI, status_code=status.HTTP_201_CREATED)
async def create_rfi(project_id: str, body: RFICreate):
    """
    Create a new RFI. RFI number is auto-assigned as RFI-{next_seq:03d}.
    Returns 409 if a duplicate subject/question combination is detected.
    """
    raise HTTPException(status_code=501, detail="Not implemented")


@rfi_router.get("/{rfi_number}", response_model=RFI)
async def get_rfi(project_id: str, rfi_number: str):
    raise HTTPException(status_code=501, detail="Not implemented")


@rfi_router.patch("/{rfi_number}", response_model=RFI)
async def update_rfi(project_id: str, rfi_number: str, body: dict):
    raise HTTPException(status_code=501, detail="Not implemented")


app.include_router(rfi_router)


# Export spec to file
def export_openapi_spec(output_path: str = "openapi.yaml") -> None:
    """Write the auto-generated OpenAPI spec to a YAML file."""
    import yaml, json
    spec = app.openapi()
    with open(output_path, "w") as f:
        yaml.dump(spec, f, default_flow_style=False, allow_unicode=True)
    print(f"OpenAPI spec written: {output_path}")
```

---

## Client Code Generation

Generate typed Python (or other language) clients from any OpenAPI spec.

### Using openapi-generator-cli

```bash
# Install
npm install -g @openapitools/openapi-generator-cli
# or via Docker (no install):
# docker run --rm -v $(pwd):/local openapitools/openapi-generator-cli generate ...

# Generate Python client
openapi-generator-cli generate \
  -i openapi.yaml \
  -g python \
  -o ./generated/python-client \
  --additional-properties=packageName=aec_api_client,projectName=aec-api-client

# Generated structure:
# generated/python-client/
#   aec_api_client/
#     api/
#       rfis_api.py
#       submittals_api.py
#       scope_items_api.py
#     models/
#       rfi.py
#       rfi_create.py
#       scope_item.py
#     configuration.py

# Generate TypeScript (for dashboard frontends)
openapi-generator-cli generate \
  -i openapi.yaml \
  -g typescript-axios \
  -o ./generated/ts-client
```

### Using Generated Python Client

```python
import aec_api_client
from aec_api_client.api import rfis_api
from aec_api_client.models import RFICreate, RFIPriority

# Configure
config = aec_api_client.Configuration(
    host        = "https://api.aec-platform.internal/v2",
    access_token = "your-jwt-token",
)

with aec_api_client.ApiClient(config) as api_client:
    rfi_api = rfis_api.RFIsApi(api_client)

    # Create RFI
    new_rfi = RFICreate(
        priority      = RFIPriority.HIGH,
        discipline    = "Structural",
        spec_section  = "05 12 00",
        subject       = "Conflicting slab thickness",
        question      = "Which slab thickness governs: 6\" (drawing) or 8\" (spec)?",
        issued_by     = "GC",
        issued_to     = "Architect",
        response_days = 10,
    )
    result = rfi_api.create_rfi(project_id="2401", rfi_create=new_rfi)
    print(f"Created: {result.rfi_number}")

    # List overdue
    overdue = rfi_api.list_rfis(project_id="2401", overdue_only=True)
    print(f"Overdue RFIs: {overdue.summary.overdue}")
```

### Lightweight Client Without Code Generation

```python
import httpx
from typing import Optional
from datetime import date

class AECApiClient:
    """
    Minimal typed client for the AEC Automation API.
    Uses httpx; no generated code required.
    """

    def __init__(self, base_url: str, api_key: str):
        self.http = httpx.Client(
            base_url = base_url,
            headers  = {"X-API-Key": api_key,
                        "Content-Type": "application/json"},
            timeout  = 30.0,
        )

    def list_rfis(self, project_id: str,
                   priority: str = None,
                   overdue_only: bool = False,
                   page: int = 1,
                   page_size: int = 50) -> dict:
        params = {"page": page, "page_size": page_size,
                  "overdue_only": overdue_only}
        if priority:
            params["priority"] = priority
        r = self.http.get(f"/projects/{project_id}/rfis", params=params)
        r.raise_for_status()
        return r.json()

    def create_rfi(self, project_id: str, payload: dict) -> dict:
        r = self.http.post(f"/projects/{project_id}/rfis", json=payload)
        r.raise_for_status()
        return r.json()

    def get_rfi(self, project_id: str, rfi_number: str) -> dict:
        r = self.http.get(f"/projects/{project_id}/rfis/{rfi_number}")
        r.raise_for_status()
        return r.json()

    def answer_rfi(self, project_id: str, rfi_number: str,
                    response: str, answered_by: str,
                    cost_impact: str = "None",
                    schedule_impact: str = "None") -> dict:
        r = self.http.patch(
            f"/projects/{project_id}/rfis/{rfi_number}",
            json={
                "status":          "ANSWERED",
                "response":        response,
                "answered_by":     answered_by,
                "cost_impact":     cost_impact,
                "schedule_impact": schedule_impact,
            }
        )
        r.raise_for_status()
        return r.json()

    def list_scope_items(self, project_id: str,
                          trade: str = None,
                          cost_ability: str = None,
                          page: int = 1) -> dict:
        params = {"page": page}
        if trade:         params["trade"] = trade
        if cost_ability:  params["cost_ability"] = cost_ability
        r = self.http.get(f"/projects/{project_id}/scope-items", params=params)
        r.raise_for_status()
        return r.json()

    def get_gis_features(self, project_id: str,
                          feature_type: str = None) -> dict:
        params = {}
        if feature_type: params["type"] = feature_type
        r = self.http.get(f"/projects/{project_id}/gis/features", params=params)
        r.raise_for_status()
        return r.json()

    def close(self):
        self.http.close()
```

---

## Server Stub Generation

```bash
# Generate FastAPI server stubs from spec
openapi-generator-cli generate \
  -i openapi.yaml \
  -g python-fastapi \
  -o ./generated/server-stubs \
  --additional-properties=packageName=aec_api

# Generated stubs include:
# - Route handlers with correct signatures
# - Pydantic models for all schemas
# - Placeholder NotImplementedError raises
# Replace NotImplementedError with real implementation
```

### Stub Implementation Pattern

```python
# generated stub (do not edit)
# src/aec_api/apis/rfis_api_base.py

from abc import ABC, abstractmethod
from .models import RFI, RFICreate, PaginatedRFIResponse

class BaseRFIsApi(ABC):
    @abstractmethod
    async def list_rfis(self, project_id: str, **kwargs) -> PaginatedRFIResponse:
        ...
    @abstractmethod
    async def create_rfi(self, project_id: str, body: RFICreate) -> RFI:
        ...

# ── Your implementation (edit this) ──────────────────────────────────────────
# src/aec_api/impl/rfis_impl.py

from ..generated.apis.rfis_api_base import BaseRFIsApi

class RFIsImpl(BaseRFIsApi):
    def __init__(self, rfi_store):
        self.store = rfi_store

    async def list_rfis(self, project_id: str, **kwargs):
        rfis = self.store.query(project_id=project_id, **kwargs)
        return PaginatedRFIResponse(items=rfis, ...)

    async def create_rfi(self, project_id: str, body: RFICreate):
        return self.store.create(project_id=project_id, **body.model_dump())
```

---

## Contract Testing

Contract testing verifies that a live API actually matches its OpenAPI spec.

### Schemathesis — Property-Based Contract Testing

```bash
pip install schemathesis

# Test against live server
schemathesis run openapi.yaml \
  --url http://localhost:8000 \
  --checks all \
  --validate-schema true

# Test specific endpoint
schemathesis run openapi.yaml \
  --url http://localhost:8000 \
  --endpoint "/projects/{project_id}/rfis" \
  --method GET

# CI mode — exit 1 on failures
schemathesis run openapi.yaml --url $API_URL --checks all --exitfirst
```

### Pytest + Schemathesis

```python
import schemathesis
import pytest

schema = schemathesis.from_path("openapi.yaml", base_url="http://localhost:8000")

@schema.parametrize()
def test_api_contract(case):
    """
    Auto-generates test cases for every operation in the spec.
    Checks: 5xx responses, schema conformance, response time.
    """
    response = case.call_and_validate()
    assert response.status_code < 500, (
        f"Server error on {case.method} {case.path}: {response.text}"
    )


@schema.parametrize(endpoint="/projects/{project_id}/rfis")
def test_rfi_list_contract(case):
    response = case.call_and_validate()
    # Additional domain assertions
    if response.status_code == 200:
        body = response.json()
        assert "items" in body
        assert "pagination" in body
        assert isinstance(body["items"], list)
```

### Response Validation in Client Code

```python
from jsonschema import validate, ValidationError
import json, yaml

def load_schema_from_spec(spec_path: str, schema_name: str) -> dict:
    """Extract a single schema from an OpenAPI spec for validation."""
    with open(spec_path) as f:
        spec = yaml.safe_load(f)
    return spec["components"]["schemas"][schema_name]

def validate_response(response_body: dict, spec_path: str,
                       schema_name: str) -> bool:
    """Validate an API response against its OpenAPI schema."""
    schema = load_schema_from_spec(spec_path, schema_name)
    try:
        validate(instance=response_body, schema=schema)
        return True
    except ValidationError as e:
        print(f"Response validation failed: {e.message}")
        return False

# Usage
rfi_response = client.get_rfi("2401", "RFI-042")
assert validate_response(rfi_response, "openapi.yaml", "RFI")
```

---

## Versioning Strategy

### URL Path Versioning (recommended for AEC pipelines)

```
/v1/projects/{project_id}/rfis   — stable, supported
/v2/projects/{project_id}/rfis   — current
/v3/projects/{project_id}/rfis   — beta (if applicable)

Rules:
  - Major version bump (v1 → v2) for breaking changes only
  - Minor changes (new optional fields, new endpoints) = no version bump
  - Deprecated versions: serve for minimum 6 months after v+1 ships
  - Signal deprecation via Deprecation and Sunset response headers
```

### Deprecation Headers

```python
from fastapi import Response
from datetime import date

@app.get("/v1/projects/{project_id}/rfis",
         deprecated=True,    # marks as deprecated in OpenAPI spec
         tags=["RFIs (v1 — deprecated)"])
async def list_rfis_v1(project_id: str, response: Response):
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"]      = "Sat, 01 Jan 2026 00:00:00 GMT"
    response.headers["Link"]        = '</v2/projects/{project_id}/rfis>; rel="successor-version"'
    # ... forward to v2 implementation
```

### Breaking vs Non-Breaking Changes

```
NON-BREAKING (no version bump):
  + Add new optional request field
  + Add new optional response field
  + Add new endpoint
  + Add new enum value (if consumers use unknown-value handling)
  + Relax a constraint (raise maxLength, remove a required field)

BREAKING (requires major version bump):
  - Remove or rename a field
  - Change a field type
  - Change a field from optional to required
  - Remove an endpoint
  - Change status code semantics
  - Add required field to request body
  - Change authentication scheme
```

### Spec Changelog in info.description

```yaml
info:
  title: AEC Automation API
  version: "2.1.0"
  description: |
    ## Changelog

    ### 2.1.0 (2024-03-15)
    - Added `bulk_create_rfis` endpoint (POST /rfis/bulk)
    - Added `days_open` and `days_overdue` computed fields to RFI response
    - Added `overdue_only` filter to list_rfis

    ### 2.0.0 (2024-01-10)
    - BREAKING: `status` field renamed from `state`
    - BREAKING: Removed v1 `/rfis/list` endpoint (use GET /rfis)
    - Added GIS endpoints (/gis/features)
    - Added scope-items endpoints

    ### 1.0.0 (2023-11-01)
    - Initial release
```

---

## Validation & QA

### Spec Linting

```bash
pip install openapi-spec-validator pyyaml

# Validate spec structure
python -c "
from openapi_spec_validator import validate_spec
from openapi_spec_validator.readers import read_from_filename
spec_dict, _ = read_from_filename('openapi.yaml')
validate_spec(spec_dict)
print('Spec valid')
"

# Lint for design quality (spectral)
npm install -g @stoplight/spectral-cli
spectral lint openapi.yaml --ruleset @stoplight/spectral-owasp-rules
```

### Spec Validation in Python

```python
from openapi_spec_validator import validate_spec
from openapi_spec_validator.readers import read_from_filename
import yaml

def validate_openapi_spec(spec_path: str) -> dict:
    """Validate an OpenAPI spec file. Returns validation report."""
    errors, warnings = [], []

    # Parse YAML
    try:
        with open(spec_path) as f:
            spec = yaml.safe_load(f)
    except Exception as e:
        return {"pass": False, "errors": [f"YAML parse error: {e}"], "warnings": []}

    # Structural validation
    try:
        spec_dict, _ = read_from_filename(spec_path)
        validate_spec(spec_dict)
    except Exception as e:
        errors.append(f"OpenAPI validation: {e}")

    # AEC-specific checks
    paths = spec.get("paths", {})

    # All paths should have operationId
    for path, methods in paths.items():
        for method, op in methods.items():
            if method in ("get","post","put","patch","delete","head"):
                if not op.get("operationId"):
                    warnings.append(f"Missing operationId: {method.upper()} {path}")
                if not op.get("tags"):
                    warnings.append(f"Missing tags: {method.upper()} {path}")
                if not op.get("summary"):
                    warnings.append(f"Missing summary: {method.upper()} {path}")

    # All POST/PUT/PATCH should document 4xx responses
    for path, methods in paths.items():
        for method, op in methods.items():
            if method in ("post","put","patch"):
                responses = op.get("responses", {})
                if "400" not in responses and "422" not in responses:
                    warnings.append(
                        f"No 400/422 response documented: {method.upper()} {path}"
                    )

    # Security defined globally or per-operation
    global_sec = spec.get("security")
    if not global_sec:
        unsecured = []
        for path, methods in paths.items():
            for method, op in methods.items():
                if method in ("get","post","put","patch","delete"):
                    if "security" not in op:
                        unsecured.append(f"{method.upper()} {path}")
        if unsecured:
            warnings.append(
                f"{len(unsecured)} operations have no security defined: "
                f"{unsecured[:3]}{'...' if len(unsecured)>3 else ''}"
            )

    print(f"OpenAPI Spec Validation: {spec_path}")
    print(f"  Paths: {len(paths)}  |  Version: {spec.get('info',{}).get('version','?')}")
    for e in errors:   print(f"  ERROR: {e}")
    for w in warnings: print(f"  WARN:  {w}")
    print(f"  Verdict: {'FAIL' if errors else 'WARN' if warnings else 'PASS'}")

    return {"pass": not errors, "errors": errors, "warnings": warnings}
```

### QA Checklist

- [ ] Spec parses without YAML errors — `yaml.safe_load()` succeeds
- [ ] `validate_spec()` passes — structural OpenAPI 3.x compliance
- [ ] Every operation has `operationId`, `summary`, and `tags`
- [ ] Every mutating operation (POST/PUT/PATCH) documents 400/422 responses
- [ ] Every operation documents 401 and 404 where applicable
- [ ] All list endpoints return a pagination envelope
- [ ] All schemas have `required` arrays declared explicitly
- [ ] No inline schemas on paths — all schemas in `components/schemas` with `$ref`
- [ ] `always_xy` note (lon, lat order) documented on all GeoJSON endpoints
- [ ] Breaking changes increment major version; changelog updated
- [ ] Contract tests (`schemathesis`) pass against local server before merge
- [ ] Deprecated endpoints carry `Deprecation` and `Sunset` headers
- [ ] Generated clients rebuild cleanly after spec changes

---

## Common Issues & Fixes

| Issue | Cause | Fix |
|---|---|---|
| Generated client breaks after spec change | Non-breaking field addition treated as breaking | Regenerate client; add `additionalProperties: true` to response schemas for forward compatibility |
| 422 instead of 400 | FastAPI returns 422 for Pydantic validation failures | Document `422` (not just `400`) in spec for all POST/PATCH operations |
| `null` vs missing field confusion | OpenAPI 3.0 `nullable: true` vs 3.1 `type: ["string","null"]` | Use 3.1 union type syntax; never use deprecated `nullable` |
| GeoJSON coordinate order wrong in spec | Spec documents [lat,lon] instead of [lon,lat] | RFC 7946 mandates [lon, lat]; add explicit note in schema description |
| Circular `$ref` breaks code generators | Schema A references B which references A | Introduce a base schema; extract the circular portion to a third schema |
| Schemathesis generates invalid project_id | Pattern regex not restrictive enough | Tighten `pattern` constraint; add `minLength`/`maxLength` |
| operationId collision | Two routes with same name | Prefix by router: `rfis_list_rfis`, `submittals_list_submittals` |
| Async job endpoint not modelled | Long-running ops return synchronous response | Use 202 Accepted + Location header + `/jobs/{job_id}` polling pattern |

---

## Dependencies

```bash
# Spec validation
pip install openapi-spec-validator pyyaml

# Server framework (auto-generates spec)
pip install fastapi uvicorn[standard]

# HTTP client for generated/handwritten clients
pip install httpx

# Contract testing
pip install schemathesis pytest

# Response validation
pip install jsonschema

# Code generation (Node.js CLI — runs from terminal)
npm install -g @openapitools/openapi-generator-cli

# Spec linting (Node.js CLI)
npm install -g @stoplight/spectral-cli
```
