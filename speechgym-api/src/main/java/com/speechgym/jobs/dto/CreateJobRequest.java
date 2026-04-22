package com.speechgym.jobs.dto;

import java.util.Map;
import java.util.UUID;

import jakarta.validation.constraints.NotNull;

public record CreateJobRequest(
    @NotNull UUID uploadId,
    Map<String, Object> options
) {
}
