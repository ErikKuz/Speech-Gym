# Architecture Decisions

## ADR-001: JWT Strategy

- Status: Accepted for MVP
- Decision: use self-issued JWT access and refresh tokens inside the Spring Boot app
- Why:
  - keeps the MVP self-contained
  - satisfies Bearer JWT requirement from the specification
  - works well with `spring-boot-starter-oauth2-resource-server`
- Consequences:
  - the app owns token signing, refresh validation and secret rotation
  - production-grade key rotation and centralized identity are deferred

### REQUIRE AGREEMENT: move to Keycloak or another OIDC provider

- Not implemented
- Would replace local token issuance with external identity and resource-server validation through issuer metadata or JWKS

## ADR-002: Upload Path

- Status: Accepted for MVP
- Decision: use backend multipart upload for `POST /api/v1/sessions/{sessionId}/uploads`
- Why:
  - smallest end-to-end path for desktop MVP
  - simpler validation and ownership checks
  - no client-side S3 signing logic is needed
- Consequences:
  - API node handles file transfer directly
  - large-file scalability is lower than direct-to-object-storage uploads

Presigned URLs are prepared at the abstraction level through `StorageService#createPresignedGetUrl(...)`, but presigned upload endpoints are intentionally not implemented yet.

### REQUIRE AGREEMENT: add presigned upload flow

- Not implemented
- Expected future shape:
  - `POST /api/v1/sessions/{sessionId}/uploads/init`
  - `POST /api/v1/uploads/{uploadId}/complete`

## ADR-003: Worker Topology

- Status: Accepted for MVP
- Decision: keep API and worker in the same Spring Boot application, connected through RabbitMQ
- Why:
  - keeps deployment and debugging simple
  - preserves asynchronous boundaries and message contracts
  - easy to split later because publisher, queue payload and listener are already explicit

### REQUIRE AGREEMENT: split worker into a separate service

- Not implemented
- Would require separate deployment, shared config and potentially dedicated scaling rules

## ADR-004: Queue Publish Reliability

- Status: Accepted for MVP
- Decision: publish directly to RabbitMQ after persisting `jobs` and `job_events`
- Why:
  - smaller implementation surface for MVP
  - enough for local development and demo flows
- Consequences:
  - no durable outbox replay if DB commit succeeds and publish fails afterwards
  - rare edge cases can leave a `QUEUED` job without a delivered message

### REQUIRE AGREEMENT: transactional outbox + relay

- Not implemented
- Recommended production path for higher reliability and replayability

## ADR-005: Idempotency

- Status: Accepted
- Decision: store idempotent responses in `idempotency_keys` for 24 hours
- Why:
  - protects session and job creation from client retries
  - aligns with network retry behavior of desktop clients
- Consequences:
  - same key + same body returns the stored response
  - same key + different body returns `409 Conflict`

## ADR-006: Object-Level Security

- Status: Accepted
- Decision: every resource lookup is constrained by `user_id`
- Why:
  - prevents cross-user enumeration
  - matches the original requirement for object-level access control
- Consequences:
  - foreign resource access returns `404`, not `403`
  - no `X-User-Id` or similar client-supplied ownership headers are trusted
