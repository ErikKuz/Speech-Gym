# Dev Runbook

## Local Stack

Services started by [`docker-compose.yml`](/c:/Users/Наталья%20Борисовна/Documents/Проект%20по%20ОС/docker-compose.yml):

- PostgreSQL 16 on `localhost:5432`
- RabbitMQ on `localhost:5672`
- RabbitMQ Management UI on `http://localhost:15672` with `speechgym/speechgym`
- MinIO API on `http://localhost:9000`
- MinIO Console on `http://localhost:9001` with `minioadmin/minioadmin`

## Start Infrastructure

```bash
docker compose up -d
docker compose ps
```

## Create MinIO Buckets

On Docker Desktop:

```bash
docker run --rm minio/mc sh -c "mc alias set local http://host.docker.internal:9000 minioadmin minioadmin && mc mb --ignore-existing local/speechgym-uploads && mc mb --ignore-existing local/speechgym-artifacts"
```

Alternative through UI:

1. Open `http://localhost:9001`
2. Login with `minioadmin / minioadmin`
3. Create buckets `speechgym-uploads` and `speechgym-artifacts`

## Run the Application

```bash
cd speechgym-api
./mvnw spring-boot:run -Dspring-boot.run.profiles=local
```

Key local settings are defined in [`application.yml`](/c:/Users/Наталья%20Борисовна/Documents/Проект%20по%20ОС/speechgym-api/src/main/resources/application.yml) and [`application-local.yml`](/c:/Users/Наталья%20Борисовна/Documents/Проект%20по%20ОС/speechgym-api/src/main/resources/application-local.yml).

## Manual Verification

Requires `curl` and `jq`.

```bash
export API=http://localhost:8080/api/v1

REGISTER=$(curl -s -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email":"demo@example.com",
    "password":"Password123",
    "fullName":"Demo User"
  }')

ACCESS=$(echo "$REGISTER" | jq -r '.accessToken')
REFRESH=$(echo "$REGISTER" | jq -r '.refreshToken')

curl -s "$API/me" \
  -H "Authorization: Bearer $ACCESS" | jq

SESSION=$(curl -s -X POST "$API/sessions" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Idempotency-Key: 5d1c2ef5-d7ba-4200-9f77-1fe27e0bdac3" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"Board rehearsal",
    "goal":"Quarterly update",
    "scenario":"BUSINESS_UPDATE",
    "languageCode":"en",
    "audienceType":"executives",
    "durationTargetSeconds":420,
    "presentationStyle":"confident",
    "notes":"Keep it concise",
    "difficultyLevel":"MEDIUM",
    "coachingMode":"BALANCED"
  }')

SESSION_ID=$(echo "$SESSION" | jq -r '.sessionId')

printf 'RIFF....WAVEfmt ' > /tmp/speechgym-demo.wav

UPLOAD=$(curl -s -X POST "$API/sessions/$SESSION_ID/uploads" \
  -H "Authorization: Bearer $ACCESS" \
  -F "file=@/tmp/speechgym-demo.wav;type=audio/wav")

UPLOAD_ID=$(echo "$UPLOAD" | jq -r '.uploadId')

JOB_RESPONSE=$(curl -si -X POST "$API/sessions/$SESSION_ID/jobs" \
  -H "Authorization: Bearer $ACCESS" \
  -H "Idempotency-Key: 8bd2fb3c-4ab0-41d9-a97c-51818f9f03a8" \
  -H "Content-Type: application/json" \
  -d "{
    \"uploadId\":\"$UPLOAD_ID\",
    \"options\":{\"reportFormat\":\"FULL\"}
  }")

echo "$JOB_RESPONSE"
JOB_ID=$(echo "$JOB_RESPONSE" | sed -n 's/.*"jobId":"\([^"]*\)".*/\1/p')

curl -s "$API/jobs/$JOB_ID" \
  -H "Authorization: Bearer $ACCESS" | jq
```

Refresh token check:

```bash
curl -s -X POST "$API/auth/refresh" \
  -H "Content-Type: application/json" \
  -d "{\"refreshToken\":\"$REFRESH\"}" | jq
```

Requeue in local profile:

```bash
curl -s -X POST "$API/dev/jobs/$JOB_ID/requeue" \
  -H "Authorization: Bearer $ACCESS" | jq
```

## Worker Debugging

- Watch application logs for `jobId`, `sessionId`, `userId`
- Stage flow is:
  - `QUEUED`
  - `RUNNING_ASR`
  - `RUNNING_NLP`
  - `RUNNING_VOICE`
  - `RUNNING_REPORT`
  - `DONE` or `FAILED`
- RabbitMQ UI: `http://localhost:15672`
- MinIO UI: `http://localhost:9001`

Useful checks:

```bash
curl -s "$API/jobs/$JOB_ID" -H "Authorization: Bearer $ACCESS" | jq
curl -s "$API/sessions/$SESSION_ID/jobs" -H "Authorization: Bearer $ACCESS" | jq
```

## Flyway

Migrations live in:

- [`V1__init.sql`](/c:/Users/Наталья%20Борисовна/Documents/Проект%20по%20ОС/speechgym-api/src/main/resources/db/migration/V1__init.sql)
- [`V2__reports.sql`](/c:/Users/Наталья%20Борисовна/Documents/Проект%20по%20ОС/speechgym-api/src/main/resources/db/migration/V2__reports.sql)
- [`V3__idempotency_keys.sql`](/c:/Users/Наталья%20Борисовна/Documents/Проект%20по%20ОС/speechgym-api/src/main/resources/db/migration/V3__idempotency_keys.sql)

Schema validation for local runtime stays on `spring.jpa.hibernate.ddl-auto=validate`.
