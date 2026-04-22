package com.speechgym.sessions.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record CreateSessionRequest(
    @NotBlank @Size(max = 200) String title,
    @Size(max = 400) String goal,
    @NotBlank @Size(max = 100) String scenario,
    @NotBlank @Size(max = 16) String languageCode,
    @NotBlank @Size(max = 100) String audienceType,
    @Min(30) @Max(7200) int durationTargetSeconds,
    @NotBlank @Size(max = 100) String presentationStyle,
    @Size(max = 2000) String notes,
    @NotBlank @Size(max = 32) String difficultyLevel,
    @NotBlank @Size(max = 32) String coachingMode
) {
}
