package com.speechgym.jobs;

import java.util.UUID;

public record PostAsrJobMessage(
    UUID jobId,
    UUID userId,
    UUID sessionId,
    UUID uploadId,
    UUID asrArtifactId
) {
}
