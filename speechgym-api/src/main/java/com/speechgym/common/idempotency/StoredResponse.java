package com.speechgym.common.idempotency;

public record StoredResponse<T>(
    int statusCode,
    String location,
    String retryAfter,
    T body
) {
}
