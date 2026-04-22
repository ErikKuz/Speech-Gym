package com.speechgym.sessions.dto;

import java.time.Instant;
import java.util.UUID;

public record SessionResponse(
    UUID sessionId,
    String title,
    String goal,
    String scenario,
    String languageCode,
    String audienceType,
    int durationTargetSeconds,
    String presentationStyle,
    String notes,
    String difficultyLevel,
    String coachingMode,
    Instant createdAt,
    Instant updatedAt
) {
}
