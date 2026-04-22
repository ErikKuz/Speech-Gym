package com.speechgym.artifacts;

import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

public interface ArtifactRepository extends JpaRepository<ArtifactEntity, UUID> {
    Optional<ArtifactEntity> findByIdAndUserId(UUID id, UUID userId);

    Optional<ArtifactEntity> findByJobIdAndTypeAndUserId(UUID jobId, ArtifactType type, UUID userId);

    Optional<ArtifactEntity> findByJobIdAndType(UUID jobId, ArtifactType type);
}
