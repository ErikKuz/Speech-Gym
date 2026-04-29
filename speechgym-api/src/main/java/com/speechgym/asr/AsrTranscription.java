package com.speechgym.asr;

import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;

@JsonIgnoreProperties(ignoreUnknown = true)
public record AsrTranscription(
    String text,
    double duration,
    String language,
    @JsonProperty("language_probability") double languageProbability,
    List<AsrSegment> segments
) {
    public AsrTranscription {
        segments = segments == null ? List.of() : List.copyOf(segments);
        text = text == null || text.isBlank() ? joinSegmentText(segments) : text;
    }

    public AsrTranscription(
        double duration,
        String language,
        double languageProbability,
        List<AsrSegment> segments
    ) {
        this(null, duration, language, languageProbability, segments);
    }

    private static String joinSegmentText(List<AsrSegment> segments) {
        return segments.stream()
            .map(AsrSegment::text)
            .filter(Objects::nonNull)
            .map(String::trim)
            .filter(value -> !value.isBlank())
            .collect(Collectors.joining(" "));
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record AsrSegment(
        double start,
        double end,
        String text,
        List<AsrWord> words
    ) {
        public AsrSegment {
            words = words == null ? List.of() : List.copyOf(words);
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record AsrWord(
        double start,
        double end,
        String word
    ) {
    }
}
