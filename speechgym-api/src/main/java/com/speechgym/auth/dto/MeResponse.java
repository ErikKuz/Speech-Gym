package com.speechgym.auth.dto;

import java.time.Instant;
import java.util.UUID;

public record MeResponse(
    UUID userId,
    String email,
    String fullName,
    String role,
    String subscriptionPlan,
    boolean subscriptionActive,
    Instant subscriptionValidUntil,
    Instant createdAt
) {
}
