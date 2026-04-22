package com.speechgym.jobs.dto;

import java.time.Instant;
import java.util.UUID;

public record JobStatusResponse(
    UUID jobId,
    UUID sessionId,
    UUID uploadId,
    String status,
    String currentStage,
    int progress,
    UUID reportId,
    String errorCode,
    String errorMessage,
    Instant createdAt,
    Instant startedAt,
    Instant finishedAt
) {
}
