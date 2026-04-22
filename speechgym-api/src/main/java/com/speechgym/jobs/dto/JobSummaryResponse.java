package com.speechgym.jobs.dto;

import java.time.Instant;
import java.util.UUID;

public record JobSummaryResponse(
    UUID jobId,
    UUID uploadId,
    String status,
    int progress,
    Instant createdAt,
    Instant finishedAt
) {
}
