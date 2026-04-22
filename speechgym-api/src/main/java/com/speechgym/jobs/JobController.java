package com.speechgym.jobs;

import java.net.URI;
import java.util.List;
import java.util.UUID;

import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.speechgym.common.idempotency.StoredResponse;
import com.speechgym.common.security.CurrentUserService;
import com.speechgym.jobs.dto.CreateJobRequest;
import com.speechgym.jobs.dto.JobAcceptedResponse;
import com.speechgym.jobs.dto.JobStatusResponse;
import com.speechgym.jobs.dto.JobSummaryResponse;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Pattern;

@RestController
@Validated
@RequestMapping("/api/v1")
public class JobController {
    private final JobService jobService;
    private final CurrentUserService currentUserService;

    public JobController(JobService jobService, CurrentUserService currentUserService) {
        this.jobService = jobService;
        this.currentUserService = currentUserService;
    }

    @PostMapping("/sessions/{sessionId}/jobs")
    public ResponseEntity<JobAcceptedResponse> create(
        @PathVariable UUID sessionId,
        @RequestHeader("Idempotency-Key")
        @Pattern(regexp = "^[0-9a-fA-F-]{36}$", message = "Idempotency-Key must be a UUID string.")
        String idempotencyKey,
        @Valid @RequestBody CreateJobRequest request
    ) {
        StoredResponse<JobAcceptedResponse> response = jobService.createJob(
            currentUserService.requireUserId(),
            sessionId,
            idempotencyKey,
            request
        );
        return ResponseEntity.status(response.statusCode())
            .header(HttpHeaders.LOCATION, URI.create(response.location()).toString())
            .header(HttpHeaders.RETRY_AFTER, response.retryAfter())
            .body(response.body());
    }

    @GetMapping("/jobs/{jobId}")
    public JobStatusResponse get(@PathVariable UUID jobId) {
        return jobService.getStatus(currentUserService.requireUserId(), jobId);
    }

    @GetMapping("/sessions/{sessionId}/jobs")
    public List<JobSummaryResponse> list(@PathVariable UUID sessionId) {
        return jobService.listBySession(currentUserService.requireUserId(), sessionId);
    }
}
