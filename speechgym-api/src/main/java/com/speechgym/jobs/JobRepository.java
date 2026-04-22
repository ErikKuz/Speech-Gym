package com.speechgym.jobs;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

public interface JobRepository extends JpaRepository<JobEntity, UUID> {
    Optional<JobEntity> findByIdAndUserId(UUID id, UUID userId);

    List<JobEntity> findBySessionIdAndUserIdOrderByCreatedAtDesc(UUID sessionId, UUID userId);
}
