# API Contract

## Conventions

- Base path: `/api/v1`
- Auth: `Authorization: Bearer <access-token>` on every protected endpoint
- Current user is taken only from JWT claim `sub` via `CurrentUserService.requireUserId()`
- Ownership failures return `404 Not Found`
- Errors use `application/problem+json`
- `Idempotency-Key` is required for:
  - `POST /api/v1/sessions`
  - `POST /api/v1/sessions/{sessionId}/jobs`
- Idempotency TTL: 24 hours

## Auth

### `POST /auth/register`

Request:

```json
{
  "email": "demo@example.com",
  "password": "Password123",
  "fullName": "Demo User"
}
```

Response `201 Created`:

```json
{
  "userId": "11111111-1111-1111-1111-111111111111",
  "email": "demo@example.com",
  "fullName": "Demo User",
  "role": "USER",
  "accessToken": "eyJ...",
  "accessTokenExpiresAt": "2026-03-14T12:15:00Z",
  "refreshToken": "eyJ...",
  "refreshTokenExpiresAt": "2026-03-28T12:00:00Z"
}
```

### `POST /auth/login`

Request:

```json
{
  "email": "demo@example.com",
  "password": "Password123"
}
```

Response `200 OK`: same shape as register.

### `POST /auth/refresh`

Request:

```json
{
  "refreshToken": "eyJ..."
}
```

Response `200 OK`: same shape as register/login with rotated access token and refresh token.

### `GET /me`

Response `200 OK`:

```json
{
  "userId": "11111111-1111-1111-1111-111111111111",
  "email": "demo@example.com",
  "fullName": "Demo User",
  "role": "USER",
  "subscriptionPlan": "FREE",
  "subscriptionActive": true,
  "subscriptionValidUntil": "2026-04-13T12:00:00Z",
  "createdAt": "2026-03-14T12:00:00Z"
}
```

## Sessions

### `POST /sessions`

Headers:

- `Authorization: Bearer ...`
- `Idempotency-Key: 5d1c2ef5-d7ba-4200-9f77-1fe27e0bdac3`

Request:

```json
{
  "title": "Board meeting rehearsal",
  "goal": "Prepare a concise quarterly update",
  "scenario": "BUSINESS_UPDATE",
  "languageCode": "en",
  "audienceType": "executives",
  "durationTargetSeconds": 420,
  "presentationStyle": "confident",
  "notes": "Focus on risks and roadmap",
  "difficultyLevel": "MEDIUM",
  "coachingMode": "BALANCED"
}
```

Response `201 Created`

Headers:

- `Location: /api/v1/sessions/{sessionId}`

Body:

```json
{
  "sessionId": "22222222-2222-2222-2222-222222222222",
  "title": "Board meeting rehearsal",
  "goal": "Prepare a concise quarterly update",
  "scenario": "BUSINESS_UPDATE",
  "languageCode": "en",
  "audienceType": "executives",
  "durationTargetSeconds": 420,
  "presentationStyle": "confident",
  "notes": "Focus on risks and roadmap",
  "difficultyLevel": "MEDIUM",
  "coachingMode": "BALANCED",
  "createdAt": "2026-03-14T12:01:00Z",
  "updatedAt": "2026-03-14T12:01:00Z"
}
```

### `GET /sessions?page=0&size=20&query=board`

Response `200 OK`:

```json
{
  "items": [
    {
      "sessionId": "22222222-2222-2222-2222-222222222222",
      "title": "Board meeting rehearsal",
      "goal": "Prepare a concise quarterly update",
      "updatedAt": "2026-03-14T12:01:00Z"
    }
  ],
  "page": 0,
  "size": 20,
  "totalElements": 1,
  "totalPages": 1
}
```

### `GET /sessions/{sessionId}`

Response `200 OK`: same shape as `POST /sessions`.

### `PATCH /sessions/{sessionId}`

Request body: same shape as `CreateSessionRequest`

Response `200 OK`: same shape as session details.

## Uploads

### `POST /sessions/{sessionId}/uploads`

Consumes: `multipart/form-data`

Part:

- `file`: audio file

Response `200 OK`:

```json
{
  "uploadId": "33333333-3333-3333-3333-333333333333",
  "status": "STORED",
  "originalFilename": "rehearsal.wav",
  "contentType": "audio/wav",
  "sizeBytes": 428381,
  "createdAt": "2026-03-14T12:03:00Z"
}
```

### `GET /sessions/{sessionId}/uploads`

Response `200 OK`:

```json
[
  {
    "uploadId": "33333333-3333-3333-3333-333333333333",
    "status": "STORED",
    "originalFilename": "rehearsal.wav",
    "contentType": "audio/wav",
    "sizeBytes": 428381,
    "createdAt": "2026-03-14T12:03:00Z"
  }
]
```

## Jobs

### `POST /sessions/{sessionId}/jobs`

Headers:

- `Authorization: Bearer ...`
- `Idempotency-Key: 8bd2fb3c-4ab0-41d9-a97c-51818f9f03a8`

Request:

```json
{
  "uploadId": "33333333-3333-3333-3333-333333333333",
  "options": {
    "reportFormat": "FULL",
    "languageHint": "en"
  }
}
```

Response `202 Accepted`

Headers:

- `Location: /api/v1/jobs/{jobId}`
- `Retry-After: 2`

Body:

```json
{
  "jobId": "44444444-4444-4444-4444-444444444444",
  "status": "QUEUED",
  "statusUrl": "/api/v1/jobs/44444444-4444-4444-4444-444444444444"
}
```

### `GET /jobs/{jobId}`

Response `200 OK`:

```json
{
  "jobId": "44444444-4444-4444-4444-444444444444",
  "sessionId": "22222222-2222-2222-2222-222222222222",
  "uploadId": "33333333-3333-3333-3333-333333333333",
  "status": "RUNNING_NLP",
  "currentStage": "RUNNING_NLP",
  "progress": 60,
  "reportId": null,
  "errorCode": null,
  "errorMessage": null,
  "createdAt": "2026-03-14T12:04:00Z",
  "startedAt": "2026-03-14T12:04:01Z",
  "finishedAt": null
}
```

Job status values:

- `QUEUED`
- `RUNNING_ASR`
- `RUNNING_NLP`
- `RUNNING_VOICE`
- `RUNNING_REPORT`
- `DONE`
- `FAILED`

### `GET /sessions/{sessionId}/jobs`

Response `200 OK`:

```json
[
  {
    "jobId": "44444444-4444-4444-4444-444444444444",
    "uploadId": "33333333-3333-3333-3333-333333333333",
    "status": "DONE",
    "progress": 100,
    "createdAt": "2026-03-14T12:04:00Z",
    "finishedAt": "2026-03-14T12:04:07Z"
  }
]
```

### `POST /dev/jobs/{jobId}/requeue`

- Available only with profile `local`
- Requires authenticated owner of the job

Response `200 OK`: same shape as `GET /jobs/{jobId}`.

## Reports

### `GET /reports/{reportId}`

Response `200 OK`:

```json
{
  "reportId": "55555555-5555-5555-5555-555555555555",
  "jobId": "44444444-4444-4444-4444-444444444444",
  "sessionId": "22222222-2222-2222-2222-222222222222",
  "overallScore": 82,
  "clarity": 84,
  "paceWpm": 136,
  "fillerWordsCount": 6,
  "confidence": 81,
  "structure": 79,
  "emotionalTone": "confident",
  "strengths": ["Clear call to action", "Good pacing"],
  "improvements": ["Reduce filler words", "Shorten the middle section"],
  "recommendations": [
    "Practice transitions between key points",
    "Use a deliberate pause after the opening"
  ],
  "createdAt": "2026-03-14T12:04:07Z"
}
```

### `GET /reports/{reportId}/pdf`

Response `200 OK`

- `Content-Type: application/pdf`
- `Content-Disposition: attachment; filename="speechgym-report-{reportId}.pdf"`

## Problem Details

Example validation response `400 Bad Request`:

```json
{
  "type": "https://speechgym.dev/problems/validation-error",
  "title": "Bad Request",
  "status": 400,
  "detail": "Request validation failed.",
  "instance": "/api/v1/sessions",
  "fieldErrors": [
    {
      "field": "title",
      "message": "must not be blank"
    },
    {
      "field": "durationTargetSeconds",
      "message": "must be greater than or equal to 30"
    }
  ]
}
```

Typical problem types:

- `https://speechgym.dev/problems/validation-error`
- `https://speechgym.dev/problems/missing-header`
- `https://speechgym.dev/problems/constraint-violation`
- `https://speechgym.dev/problems/resource-not-found`
- `https://speechgym.dev/problems/conflict`
- `https://speechgym.dev/problems/unprocessable-entity`
- `https://speechgym.dev/problems/bad-request`
