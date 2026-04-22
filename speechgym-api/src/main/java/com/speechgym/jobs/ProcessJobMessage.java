package com.speechgym.jobs;

import java.util.UUID;

public record ProcessJobMessage(
    UUID jobId,
    UUID userId,
    UUID sessionId,
    UUID uploadId
) {
}
