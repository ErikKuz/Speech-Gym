package com.speechgym.reports.dto;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

public record ReportSummaryResponse(
    UUID reportId,
    UUID jobId,
    UUID sessionId,
    int overallScore,
    int clarity,
    int paceWpm,
    int fillerWordsCount,
    int confidence,
    int structure,
    String emotionalTone,
    List<String> strengths,
    List<String> improvements,
    List<String> recommendations,
    Instant createdAt
) {
}
