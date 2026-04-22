package com.speechgym.jobs;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.speechgym.asr.AsrClient;
import com.speechgym.asr.AsrTranscription;
import com.speechgym.artifacts.ArtifactEntity;
import com.speechgym.artifacts.ArtifactService;
import com.speechgym.artifacts.ArtifactType;
import com.speechgym.reports.PdfReportGenerator;
import com.speechgym.reports.ReportEntity;
import com.speechgym.reports.ReportGenerationResult;
import com.speechgym.reports.ReportRepository;
import com.speechgym.sessions.SessionEntity;
import com.speechgym.sessions.SessionRepository;
import com.speechgym.storage.StorageService;
import com.speechgym.storage.StoredObject;
import com.speechgym.uploads.UploadEntity;
import com.speechgym.uploads.UploadService;

@Component
public class JobWorker {
    private static final Logger log = LoggerFactory.getLogger(JobWorker.class);

    private final JobService jobService;
    private final UploadService uploadService;
    private final StorageService storageService;
    private final AsrClient asrClient;
    private final ArtifactService artifactService;
    private final ReportRepository reportRepository;
    private final SessionRepository sessionRepository;
    private final PdfReportGenerator pdfReportGenerator;
    private final ObjectMapper objectMapper;

    public JobWorker(
        JobService jobService,
        UploadService uploadService,
        StorageService storageService,
        AsrClient asrClient,
        ArtifactService artifactService,
        ReportRepository reportRepository,
        SessionRepository sessionRepository,
        PdfReportGenerator pdfReportGenerator,
        ObjectMapper objectMapper
    ) {
        this.jobService = jobService;
        this.uploadService = uploadService;
        this.storageService = storageService;
        this.asrClient = asrClient;
        this.artifactService = artifactService;
        this.reportRepository = reportRepository;
        this.sessionRepository = sessionRepository;
        this.pdfReportGenerator = pdfReportGenerator;
        this.objectMapper = objectMapper;
    }

    @RabbitListener(queues = "${app.rabbit.queue}")
    public void consume(ProcessJobMessage message) {
        try {
            runPipeline(message);
        }
        catch (Exception exception) {
            jobService.markFailed(message.jobId(), "WORKER_ERROR", exception.getMessage());
        }
    }

    private void runPipeline(ProcessJobMessage message) {
        JobEntity job = jobService.markStage(message.jobId(), JobStatus.RUNNING_ASR, 15, "ASR stage started.");
        UploadEntity upload = uploadService.getUploadForWorker(message.uploadId());
        StoredObject storedAudio = storageService.getObject(upload.getBucketName(), upload.getObjectKey());
        if (storedAudio == null || storedAudio.content() == null || storedAudio.content().length == 0) {
            throw new IllegalStateException("Audio upload is missing in object storage.");
        }
        log.info("Submitting uploadId={} jobId={} to ASR service", upload.getId(), job.getId());
        AsrTranscription transcription = asrClient.transcribe(
            upload.getOriginalFilename(),
            upload.getContentType(),
            storedAudio.content()
        );
        byte[] transcript = jsonBytes(transcription);
        artifactService.storeArtifact(job, ArtifactType.ASR_TRANSCRIPT_JSON, "application/json", transcript, Map.of(
            "stage", "ASR",
            "uploadId", upload.getId(),
            "language", transcription.language()
        ));
        jobService.markStageCompleted(job.getId(), JobStatus.RUNNING_ASR, 30, "ASR stage completed.", Map.of(
            "language", transcription.language(),
            "segments", transcription.segments().size()
        ));

        job = jobService.markStage(message.jobId(), JobStatus.RUNNING_NLP, 45, "NLP stage started.");
        pause();
        byte[] nlp = jsonBytes(Map.of(
            "fillerWordsCount", 6,
            "structure", "Clear intro/body/outro",
            "strengths", List.of("Strong opening", "Clear thesis")
        ));
        artifactService.storeArtifact(job, ArtifactType.NLP_ANALYSIS_JSON, "application/json", nlp, Map.of(
            "stage", "NLP"
        ));
        jobService.markStageCompleted(job.getId(), JobStatus.RUNNING_NLP, 60, "NLP stage completed.", Map.of());

        job = jobService.markStage(message.jobId(), JobStatus.RUNNING_VOICE, 75, "Voice stage started.");
        pause();
        byte[] voice = jsonBytes(Map.of(
            "paceWpm", 136,
            "confidence", 81,
            "clarity", 84
        ));
        artifactService.storeArtifact(job, ArtifactType.VOICE_METRICS_JSON, "application/json", voice, Map.of(
            "stage", "VOICE"
        ));
        jobService.markStageCompleted(job.getId(), JobStatus.RUNNING_VOICE, 85, "Voice stage completed.", Map.of());

        job = jobService.markStage(message.jobId(), JobStatus.RUNNING_REPORT, 92, "Report stage started.");
        pause();
        SessionEntity session = sessionRepository.findById(job.getSessionId())
            .orElseThrow(() -> new IllegalStateException("Session missing for job."));
        ReportGenerationResult result = new ReportGenerationResult(
            82,
            84,
            136,
            6,
            81,
            79,
            "confident",
            List.of("Clear call to action", "Good pacing"),
            List.of("Reduce filler words", "Shorten the middle section"),
            List.of("Practice transitions between key points", "Use a deliberate pause after the opening")
        );
        byte[] pdf = pdfReportGenerator.generate(session.getTitle(), result);
        ArtifactEntity pdfArtifact = artifactService.storeArtifact(
            job,
            ArtifactType.REPORT_PDF,
            "application/pdf",
            pdf,
            Map.of("stage", "REPORT")
        );
        upsertReport(job, pdfArtifact.getId(), result);
        jobService.markStageCompleted(job.getId(), JobStatus.RUNNING_REPORT, 98, "Report generated.", Map.of());
        jobService.markDone(job.getId());
    }

    @Transactional
    protected void upsertReport(JobEntity job, UUID pdfArtifactId, ReportGenerationResult result) {
        ReportEntity report = reportRepository.findByJobId(job.getId()).orElseGet(ReportEntity::new);
        report.setJobId(job.getId());
        report.setUserId(job.getUserId());
        report.setSessionId(job.getSessionId());
        report.setPdfArtifactId(pdfArtifactId);
        report.setOverallScore(result.overallScore());
        report.setClarity(result.clarity());
        report.setPaceWpm(result.paceWpm());
        report.setFillerWordsCount(result.fillerWordsCount());
        report.setConfidence(result.confidence());
        report.setStructureScore(result.structureScore());
        report.setEmotionalTone(result.emotionalTone());
        report.setStrengths(result.strengths());
        report.setImprovements(result.improvements());
        report.setRecommendations(result.recommendations());
        reportRepository.save(report);
    }

    private byte[] jsonBytes(Object payload) {
        try {
            return objectMapper.writeValueAsBytes(payload);
        }
        catch (JsonProcessingException exception) {
            throw new IllegalStateException("Unable to serialize worker artifact payload.", exception);
        }
    }

    private void pause() {
        try {
            Thread.sleep(50L);
        }
        catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Worker interrupted.", exception);
        }
    }
}
