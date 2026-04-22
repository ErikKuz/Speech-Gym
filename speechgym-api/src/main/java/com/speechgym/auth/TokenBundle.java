package com.speechgym.auth;

import java.time.Instant;

public record TokenBundle(
    String accessToken,
    Instant accessTokenExpiresAt,
    String refreshToken,
    Instant refreshTokenExpiresAt
) {
}
