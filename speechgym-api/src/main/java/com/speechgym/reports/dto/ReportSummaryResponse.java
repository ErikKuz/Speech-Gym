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
    List<String> nextVersionChanges,
    NextVersionResponse nextVersion,
    List<String> recommendationsSummary,
    List<RecommendationDetailResponse> recommendationDetails,
    AnalysisMetaResponse analysisMeta,
    Instant createdAt
) {
    public ReportSummaryResponse {
        strengths = strengths == null ? List.of() : List.copyOf(strengths);
        improvements = improvements == null ? List.of() : List.copyOf(improvements);
        recommendations = recommendations == null ? List.of() : List.copyOf(recommendations);
        nextVersionChanges = nextVersionChanges == null ? List.of() : List.copyOf(nextVersionChanges);
        nextVersion = nextVersion == null ? new NextVersionResponse(null, null, null) : nextVersion;
        recommendationsSummary = recommendationsSummary == null ? List.of() : List.copyOf(recommendationsSummary);
        recommendationDetails = recommendationDetails == null ? List.of() : List.copyOf(recommendationDetails);
        analysisMeta = analysisMeta == null ? new AnalysisMetaResponse(null, null, null, null, null, null) : analysisMeta;
    }

    public record NextVersionResponse(
        String title,
        List<NextVersionBlockResponse> blocks,
        String fullText
    ) {
        public NextVersionResponse {
            blocks = blocks == null ? List.of() : List.copyOf(blocks);
        }
    }

    public record NextVersionBlockResponse(
        String label,
        String text
    ) {
    }

    public record RecommendationDetailResponse(
        String title,
        String before,
        String after,
        String whyBeforeWeaker,
        String whyAfterBetter,
        AudienceEffectResponse audienceEffect
    ) {
        public RecommendationDetailResponse {
            audienceEffect = audienceEffect == null ? new AudienceEffectResponse(null, null) : audienceEffect;
        }
    }

    public record AudienceEffectResponse(
        String understandsBetter,
        String feelsMore
    ) {
    }

    public record AnalysisMetaResponse(
        String pitchType,
        String language,
        Integer targetDurationSec,
        Double actualDurationSec,
        String actualDuration,
        String model
    ) {
    }
}
