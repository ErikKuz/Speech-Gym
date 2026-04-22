package com.speechgym.jobs.dto;

import java.util.UUID;

public record JobAcceptedResponse(
    UUID jobId,
    String status,
    String statusUrl
) {
}
