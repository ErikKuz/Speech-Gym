package com.speechgym.asr;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AsrTranscription(
    double duration,
    String language,
    @JsonProperty("language_probability") double languageProbability,
    List<AsrSegment> segments
) {
    public AsrTranscription {
        segments = segments == null ? List.of() : List.copyOf(segments);
    }

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

    public record AsrWord(
        double start,
        double end,
        String word
    ) {
    }
}
