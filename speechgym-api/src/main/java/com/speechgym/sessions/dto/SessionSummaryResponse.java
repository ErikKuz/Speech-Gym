package com.speechgym.sessions.dto;

import java.time.Instant;
import java.util.UUID;

public record SessionSummaryResponse(
    UUID sessionId,
    String title,
    String goal,
    Instant updatedAt
) {
}
