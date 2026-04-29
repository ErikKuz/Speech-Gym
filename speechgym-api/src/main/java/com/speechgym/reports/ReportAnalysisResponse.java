package com.speechgym.reports;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public record ReportAnalysisResponse(
    ReportPayload report,
    Meta meta
) {
    public ReportAnalysisResponse {
        report = report == null ? new ReportPayload(null, null, null) : report;
        meta = meta == null ? new Meta(null, null, null, null, null, null) : meta;
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record ReportPayload(
        @JsonProperty("passport_pitch") PassportPitch passportPitch,
        @JsonProperty("next_pitch") NextPitch nextPitch,
        Recommendations recommendations
    ) {
        public ReportPayload {
            passportPitch = passportPitch == null ? new PassportPitch(null, null, null) : passportPitch;
            nextPitch = nextPitch == null ? new NextPitch(null, null, null) : nextPitch;
            recommendations = recommendations == null ? new Recommendations(null, null) : recommendations;
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record PassportPitch(
        List<String> strengths,
        @JsonProperty("blockers") List<String> blockers,
        @JsonProperty("next_version_changes") List<String> nextVersionChanges
    ) {
        public PassportPitch {
            strengths = strengths == null ? List.of() : List.copyOf(strengths);
            blockers = blockers == null ? List.of() : List.copyOf(blockers);
            nextVersionChanges = nextVersionChanges == null ? List.of() : List.copyOf(nextVersionChanges);
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record NextPitch(
        String title,
        List<NextPitchBlock> blocks,
        @JsonProperty("full_text") String fullText
    ) {
        public NextPitch {
            blocks = blocks == null ? List.of() : List.copyOf(blocks);
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record NextPitchBlock(
        String label,
        String text
    ) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record Recommendations(
        List<String> summary,
        List<RecommendationChange> changes
    ) {
        public Recommendations {
            summary = summary == null ? List.of() : List.copyOf(summary);
            changes = changes == null ? List.of() : List.copyOf(changes);
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record RecommendationChange(
        String title,
        String before,
        String after,
        @JsonProperty("why_before_weaker") String whyBeforeWeaker,
        @JsonProperty("why_after_better") String whyAfterBetter,
        @JsonProperty("audience_effect") AudienceEffect audienceEffect
    ) {
        public RecommendationChange {
            audienceEffect = audienceEffect == null ? new AudienceEffect(null, null) : audienceEffect;
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record AudienceEffect(
        @JsonProperty("understands_better") String understandsBetter,
        @JsonProperty("feels_more") String feelsMore
    ) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record Meta(
        @JsonProperty("pitch_type") String pitchType,
        String language,
        @JsonProperty("target_duration_sec") Integer targetDurationSec,
        @JsonProperty("actual_duration_sec") Double actualDurationSec,
        @JsonProperty("actual_duration") String actualDuration,
        String model
    ) {
    }
}
