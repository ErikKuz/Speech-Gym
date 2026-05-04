package com.speechgym.jobs;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import com.speechgym.auth.SubscriptionEntity;
import com.speechgym.auth.SubscriptionRepository;
import com.speechgym.common.error.ResourceNotFoundException;
import com.speechgym.common.error.UnprocessableEntityException;
import com.speechgym.common.idempotency.IdempotencyService;
import com.speechgym.common.idempotency.StoredResponse;
import com.speechgym.jobs.dto.CreateJobRequest;
import com.speechgym.jobs.dto.JobAcceptedResponse;
import com.speechgym.jobs.dto.JobStatusResponse;
import com.speechgym.jobs.dto.JobSummaryResponse;
import com.speechgym.reports.ReportEntity;
import com.speechgym.reports.ReportRepository;
import com.speechgym.sessions.SessionService;
import com.speechgym.uploads.UploadEntity;
import com.speechgym.uploads.UploadService;

@Service
public class JobService {
    private static final Logger log = LoggerFactory.getLogger(JobService.class);

    private final JobRepository jobRepository;
    private final JobEventRepository jobEventRepository;
    private final ReportRepository reportRepository;
    private final SessionService sessionService;
    private final UploadService uploadService;
    private final SubscriptionRepository subscriptionRepository;
    private final JobPublisher jobPublisher;
    private final IdempotencyService idempotencyService;

    public JobService(
        JobRepository jobRepository,
        JobEventRepository jobEventRepository,
        ReportRepository reportRepository,
        SessionService sessionService,
        UploadService uploadService,
        SubscriptionRepository subscriptionRepository,
        JobPublisher jobPublisher,
        IdempotencyService idempotencyService
    ) {
        this.jobRepository = jobRepository;
        this.jobEventRepository = jobEventRepository;
        this.reportRepository = reportRepository;
        this.sessionService = sessionService;
        this.uploadService = uploadService;
        this.subscriptionRepository = subscriptionRepository;
        this.jobPublisher = jobPublisher;
        this.idempotencyService = idempotencyService;
    }

    @Transactional
    public StoredResponse<JobAcceptedResponse> createJob(
        UUID userId,
        UUID sessionId,
        String idempotencyKey,
        CreateJobRequest request
    ) {
        String requestHash = idempotencyService.hashPayload(request);
        return idempotencyService.restoreResponse(userId, idempotencyKey, requestHash, JobAcceptedResponse.class)
            .orElseGet(() -> createAndStore(userId, sessionId, idempotencyKey, requestHash, request));
    }

    @Transactional(readOnly = true)
    public JobStatusResponse getStatus(UUID userId, UUID jobId) {
        JobEntity job = requireOwnedJob(userId, jobId);
        return toStatus(job);
    }

    @Transactional(readOnly = true)
    public List<JobSummaryResponse> listBySession(UUID userId, UUID sessionId) {
        sessionService.requireOwnedSession(userId, sessionId);
        return jobRepository.findBySessionIdAndUserIdOrderByCreatedAtDesc(sessionId, userId).stream()
            .map(job -> new JobSummaryResponse(
                job.getId(),
                job.getUploadId(),
                job.getStatus().name(),
                job.getProgress(),
                job.getCreatedAt(),
                job.getFinishedAt()
            ))
            .toList();
    }

    @Transactional
    public JobStatusResponse requeue(UUID userId, UUID jobId) {
        JobEntity job = requireOwnedJob(userId, jobId);
        ensureUserCanCreateJobs(userId);
        job.setStatus(JobStatus.QUEUED);
        job.setCurrentStage(JobStatus.QUEUED.name());
        job.setProgress(0);
        job.setErrorCode(null);
        job.setErrorMessage(null);
        job.setStartedAt(null);
        job.setFinishedAt(null);
        recordEvent(job, JobEventType.JOB_ENQUEUED, job.getCurrentStage(), 0, "Job requeued.", Map.of());
        publishAfterCommit(new ProcessJobMessage(job.getId(), job.getUserId(), job.getSessionId(), job.getUploadId()));
        return toStatus(job);
    }

    @Transactional
    public JobEntity markStage(UUID jobId, JobStatus status, int progress, String message) {
        JobEntity job = getJobForWorker(jobId);
        if (job.getStartedAt() == null && status != JobStatus.QUEUED) {
            job.setStartedAt(Instant.now());
        }
        job.setStatus(status);
        job.setCurrentStage(status.name());
        job.setProgress(progress);
        recordEvent(job, JobEventType.STAGE_STARTED, status.name(), progress, message, Map.of());
        log.debug("Worker stage jobId={} sessionId={} userId={} stage={}", job.getId(), job.getSessionId(), job.getUserId(), status);
        return job;
    }

    @Transactional
    public void markStageCompleted(UUID jobId, JobStatus status, int progress, String message, Map<String, Object> payload) {
        JobEntity job = getJobForWorker(jobId);
        job.setStatus(status);
        job.setCurrentStage(status.name());
        job.setProgress(progress);
        recordEvent(job, JobEventType.STAGE_COMPLETED, status.name(), progress, message, payload);
    }

    @Transactional
    public void markDone(UUID jobId) {
        JobEntity job = getJobForWorker(jobId);
        job.setStatus(JobStatus.DONE);
        job.setCurrentStage(JobStatus.DONE.name());
        job.setProgress(100);
        job.setFinishedAt(Instant.now());
        recordEvent(job, JobEventType.JOB_DONE, JobStatus.DONE.name(), 100, "Job completed.", Map.of());
        log.info("Job done jobId={} sessionId={} userId={}", job.getId(), job.getSessionId(), job.getUserId());
    }

    @Transactional
    public void markFailed(UUID jobId, String errorCode, String errorMessage) {
        JobEntity job = getJobForWorker(jobId);
        job.setStatus(JobStatus.FAILED);
        job.setCurrentStage(JobStatus.FAILED.name());
        job.setErrorCode(errorCode);
        job.setErrorMessage(errorMessage);
        job.setFinishedAt(Instant.now());
        recordEvent(job, JobEventType.JOB_FAILED, JobStatus.FAILED.name(), job.getProgress(), errorMessage, Map.of(
            "errorCode", errorCode
        ));
        log.error("Job failed jobId={} sessionId={} userId={} errorCode={} message={}",
            job.getId(), job.getSessionId(), job.getUserId(), errorCode, errorMessage);
    }

    @Transactional(readOnly = true)
    public JobEntity getJobForWorker(UUID jobId) {
        return jobRepository.findById(jobId)
            .orElseThrow(() -> new ResourceNotFoundException("Job was not found."));
    }

    JobEntity requireOwnedJob(UUID userId, UUID jobId) {
        return jobRepository.findByIdAndUserId(jobId, userId)
            .orElseThrow(() -> new ResourceNotFoundException("Job was not found."));
    }

    private StoredResponse<JobAcceptedResponse> createAndStore(
        UUID userId,
        UUID sessionId,
        String idempotencyKey,
        String requestHash,
        CreateJobRequest request
    ) {
        sessionService.requireOwnedSession(userId, sessionId);
        ensureUserCanCreateJobs(userId);
        UploadEntity upload = uploadService.requireOwnedUpload(userId, sessionId, request.uploadId());

        JobEntity job = new JobEntity();
        job.setUserId(userId);
        job.setSessionId(sessionId);
        job.setUploadId(upload.getId());
        job.setStatus(JobStatus.QUEUED);
        job.setCurrentStage(JobStatus.QUEUED.name());
        job.setProgress(0);
        job.setOptionsJson(request.options() == null ? Map.of() : request.options());
        job = jobRepository.save(job);

        recordEvent(job, JobEventType.JOB_CREATED, JobStatus.QUEUED.name(), 0, "Job created.", Map.of());
        recordEvent(job, JobEventType.JOB_ENQUEUED, JobStatus.QUEUED.name(), 0, "Job enqueued.", Map.of());
        publishAfterCommit(new ProcessJobMessage(job.getId(), userId, sessionId, upload.getId()));
        log.info("Created job jobId={} sessionId={} userId={}", job.getId(), sessionId, userId);

        StoredResponse<JobAcceptedResponse> response = new StoredResponse<>(
            202,
            "/api/v1/jobs/" + job.getId(),
            "2",
            new JobAcceptedResponse(job.getId(), job.getStatus().name(), "/api/v1/jobs/" + job.getId())
        );
        idempotencyService.saveResponse(userId, idempotencyKey, requestHash, response);
        return response;
    }

    private void publishAfterCommit(ProcessJobMessage message) {
        if (!TransactionSynchronizationManager.isSynchronizationActive()) {
            jobPublisher.publish(message);
            return;
        }

        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            @Override
            public void afterCommit() {
                jobPublisher.publish(message);
            }
        });
    }

    private void ensureUserCanCreateJobs(UUID userId) {
        SubscriptionEntity subscription = subscriptionRepository.findByUserId(userId)
            .orElseThrow(() -> new UnprocessableEntityException("Active subscription is required to create jobs."));
        boolean valid = subscription.isActive() && (subscription.getValidUntil() == null || subscription.getValidUntil().isAfter(Instant.now()));
        if (!valid) {
            throw new UnprocessableEntityException("Active subscription is required to create jobs.");
        }
    }

    private void recordEvent(
        JobEntity job,
        JobEventType eventType,
        String stage,
        int progress,
        String message,
        Map<String, Object> payload
    ) {
        JobEventEntity event = new JobEventEntity();
        event.setJobId(job.getId());
        event.setEventType(eventType);
        event.setStage(stage);
        event.setProgress(progress);
        event.setMessage(message);
        event.setPayloadJson(payload);
        jobEventRepository.save(event);
    }

    private JobStatusResponse toStatus(JobEntity job) {
        UUID reportId = reportRepository.findByJobId(job.getId()).map(ReportEntity::getId).orElse(null);
        return new JobStatusResponse(
            job.getId(),
            job.getSessionId(),
            job.getUploadId(),
            job.getStatus().name(),
            job.getCurrentStage(),
            job.getProgress(),
            reportId,
            job.getErrorCode(),
            job.getErrorMessage(),
            job.getCreatedAt(),
            job.getStartedAt(),
            job.getFinishedAt()
        );
    }
}
