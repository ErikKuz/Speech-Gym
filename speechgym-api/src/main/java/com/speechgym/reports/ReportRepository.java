package com.speechgym.reports;

import java.util.Optional;
import java.util.UUID;
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

public interface ReportRepository extends JpaRepository<ReportEntity, UUID> {
    Optional<ReportEntity> findByIdAndUserId(UUID id, UUID userId);

    Optional<ReportEntity> findByJobId(UUID jobId);

    List<ReportEntity> findBySessionIdAndUserIdOrderByCreatedAtAsc(UUID sessionId, UUID userId);
}
