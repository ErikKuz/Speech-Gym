package com.speechgym.sessions.dto;

import java.util.List;

public record SessionListResponse(
    List<SessionSummaryResponse> items,
    int page,
    int size,
    long totalElements,
    int totalPages
) {
}
