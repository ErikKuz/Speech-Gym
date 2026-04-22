package com.speechgym.common.idempotency;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Clock;
import java.time.Instant;
import java.util.HexFormat;
import java.util.Optional;
import java.util.UUID;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.speechgym.common.config.AppProperties;
import com.speechgym.common.error.ConflictException;

@Service
public class IdempotencyService {
    private final IdempotencyKeyRepository repository;
    private final ObjectMapper objectMapper;
    private final Clock clock;
    private final AppProperties properties;

    public IdempotencyService(
        IdempotencyKeyRepository repository,
        ObjectMapper objectMapper,
        Clock clock,
        AppProperties properties
    ) {
        this.repository = repository;
        this.objectMapper = objectMapper;
        this.clock = clock;
        this.properties = properties;
    }

    public String hashPayload(Object payload) {
        try {
            byte[] json = objectMapper.writeValueAsBytes(payload);
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(digest.digest(json));
        }
        catch (JsonProcessingException | NoSuchAlgorithmException exception) {
            throw new IllegalStateException("Unable to hash idempotent payload.", exception);
        }
    }

    @Transactional
    public <T> Optional<StoredResponse<T>> restoreResponse(
        UUID userId,
        String idempotencyKey,
        String requestHash,
        Class<T> responseType
    ) {
        purgeExpiredKeys();
        return repository.findByUserIdAndIdempotencyKey(userId, idempotencyKey)
            .map(existing -> toStoredResponse(existing, requestHash, responseType));
    }

    @Transactional
    public void saveResponse(UUID userId, String idempotencyKey, String requestHash, StoredResponse<?> storedResponse) {
        IdempotencyKeyEntity entity = new IdempotencyKeyEntity();
        entity.setUserId(userId);
        entity.setIdempotencyKey(idempotencyKey);
        entity.setRequestHash(requestHash);
        entity.setResponseStatus(storedResponse.statusCode());
        entity.setLocation(storedResponse.location());
        entity.setRetryAfter(storedResponse.retryAfter());
        entity.setResponseBody(objectMapper.valueToTree(storedResponse.body()));
        entity.setCreatedAt(Instant.now(clock));
        entity.setExpiresAt(Instant.now(clock).plus(properties.idempotency().ttl()));
        repository.save(entity);
    }

    private <T> StoredResponse<T> toStoredResponse(
        IdempotencyKeyEntity entity,
        String requestHash,
        Class<T> responseType
    ) {
        if (!entity.getRequestHash().equals(requestHash)) {
            throw new ConflictException("Idempotency-Key reuse with a different request body is not allowed.");
        }
        T body = objectMapper.convertValue(entity.getResponseBody(), responseType);
        return new StoredResponse<>(entity.getResponseStatus(), entity.getLocation(), entity.getRetryAfter(), body);
    }

    private void purgeExpiredKeys() {
        repository.deleteByExpiresAtBefore(Instant.now(clock));
    }
}
