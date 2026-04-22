package com.speechgym.jobs;

import java.util.List;
import java.util.UUID;

import org.springframework.data.jpa.repository.JpaRepository;

public interface JobEventRepository extends JpaRepository<JobEventEntity, UUID> {
    List<JobEventEntity> findByJobIdOrderByCreatedAtAsc(UUID jobId);
}
