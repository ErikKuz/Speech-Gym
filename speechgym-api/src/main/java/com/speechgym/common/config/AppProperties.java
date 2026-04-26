package com.speechgym.common.config;

import java.time.Duration;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "app")
public record AppProperties(
    String apiPrefix,
    IdempotencyProperties idempotency,
    JwtProperties jwt,
    RabbitProperties rabbit,
    StorageProperties storage,
    AsrProperties asr
) {
    public record IdempotencyProperties(Duration ttl) {
    }

    public record JwtProperties(
        String issuer,
        String secret,
        Duration accessTokenTtl,
        Duration refreshTokenTtl
    ) {
    }

    public record RabbitProperties(
        String exchange,
        String queue,
        String routingKey
    ) {
    }

    public record StorageProperties(
        String uploadsBucket,
        String artifactsBucket,
        Duration presignedUrlTtl,
        MinioProperties minio
    ) {
    }

    public record MinioProperties(
        String endpoint,
        String accessKey,
        String secretKey,
        boolean secure
    ) {
    }

    public record AsrProperties(
        String baseUrl,
        String transcribePath,
        String healthPath,
        Duration connectTimeout,
        Duration readTimeout,
        int maxAttempts,
        Duration initialBackoff,
        Duration maxBackoff
    ) {
    }
}
