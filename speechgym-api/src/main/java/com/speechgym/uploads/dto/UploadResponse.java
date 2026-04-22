package com.speechgym.uploads.dto;

import java.time.Instant;
import java.util.UUID;

public record UploadResponse(
    UUID uploadId,
    String status,
    String originalFilename,
    String contentType,
    long sizeBytes,
    Instant createdAt
) {
}
