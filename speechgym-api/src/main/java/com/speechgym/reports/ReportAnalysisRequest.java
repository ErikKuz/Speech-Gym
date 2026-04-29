package com.speechgym.reports;

import java.util.Map;

import com.fasterxml.jackson.annotation.JsonProperty;

public record ReportAnalysisRequest(
    @JsonProperty("whisper_json") Map<String, Object> whisperJson,
    @JsonProperty("pitch_type") String pitchType,
    @JsonProperty("target_duration_sec") int targetDurationSec
) {
    public ReportAnalysisRequest {
        whisperJson = whisperJson == null ? Map.of() : Map.copyOf(whisperJson);
    }
}
