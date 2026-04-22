package com.speechgym.uploads;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

public interface UploadRepository extends JpaRepository<UploadEntity, UUID> {
    List<UploadEntity> findBySessionIdAndUserIdOrderByCreatedAtDesc(UUID sessionId, UUID userId);

    Optional<UploadEntity> findByIdAndUserId(UUID id, UUID userId);

    Optional<UploadEntity> findByIdAndSessionIdAndUserId(UUID id, UUID sessionId, UUID userId);
}
