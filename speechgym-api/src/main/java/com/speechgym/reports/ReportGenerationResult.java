package com.speechgym.reports;

import java.util.List;

public record ReportGenerationResult(
    int overallScore,
    int clarity,
    int paceWpm,
    int fillerWordsCount,
    int confidence,
    int structureScore,
    String emotionalTone,
    List<String> strengths,
    List<String> improvements,
    List<String> recommendations
) {
}
