package com.speechgym.jobs;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.speechgym.asr.AsrClient;
import com.speechgym.asr.AsrTranscription;
import com.speechgym.artifacts.ArtifactEntity;
import com.speechgym.artifacts.ArtifactService;
import com.speechgym.artifacts.ArtifactType;
import com.speechgym.reports.PdfReportGenerator;
import com.speechgym.reports.ReportRepository;
import com.speechgym.sessions.SessionEntity;
import com.speechgym.sessions.SessionRepository;
import com.speechgym.storage.StorageService;
import com.speechgym.storage.StoredObject;
import com.speechgym.uploads.UploadEntity;
import com.speechgym.uploads.UploadService;

@ExtendWith(MockitoExtension.class)
class JobWorkerTest {
    @Mock
    private JobService jobService;

    @Mock
    private UploadService uploadService;

    @Mock
    private StorageService storageService;

    @Mock
    private AsrClient asrClient;

    @Mock
    private ArtifactService artifactService;

    @Mock
    private ReportRepository reportRepository;

    @Mock
    private SessionRepository sessionRepository;

    @Mock
    private PdfReportGenerator pdfReportGenerator;

    @Test
    void consumeLoadsAudioFromStorageAndStoresRawAsrTranscript() {
        ObjectMapper objectMapper = new ObjectMapper();
        JobWorker worker = new JobWorker(
            jobService,
            uploadService,
            storageService,
            asrClient,
            artifactService,
            reportRepository,
            sessionRepository,
            pdfReportGenerator,
            objectMapper
        );

        UUID jobId = UUID.randomUUID();
        UUID userId = UUID.randomUUID();
        UUID sessionId = UUID.randomUUID();
        UUID uploadId = UUID.randomUUID();

        JobEntity job = new JobEntity();
        ReflectionTestUtils.setField(job, "id", jobId);
        job.setUserId(userId);
        job.setSessionId(sessionId);
        job.setUploadId(uploadId);

        UploadEntity upload = new UploadEntity();
        ReflectionTestUtils.setField(upload, "id", uploadId);
        upload.setBucketName("speechgym-uploads");
        upload.setObjectKey("user/session/uploads/demo.wav");
        upload.setContentType("audio/wav");
        upload.setOriginalFilename("demo.wav");

        SessionEntity session = new SessionEntity();
        ReflectionTestUtils.setField(session, "id", sessionId);
        session.setTitle("Demo session");

        ArtifactEntity storedArtifact = new ArtifactEntity();
        ReflectionTestUtils.setField(storedArtifact, "id", UUID.randomUUID());

        when(jobService.markStage(eq(jobId), eq(JobStatus.RUNNING_ASR), eq(15), any())).thenReturn(job);
        when(jobService.markStage(eq(jobId), eq(JobStatus.RUNNING_NLP), eq(45), any())).thenReturn(job);
        when(jobService.markStage(eq(jobId), eq(JobStatus.RUNNING_VOICE), eq(75), any())).thenReturn(job);
        when(jobService.markStage(eq(jobId), eq(JobStatus.RUNNING_REPORT), eq(92), any())).thenReturn(job);
        when(uploadService.getUploadForWorker(uploadId)).thenReturn(upload);
        when(storageService.getObject(upload.getBucketName(), upload.getObjectKey()))
            .thenReturn(new StoredObject("audio-bytes".getBytes(StandardCharsets.UTF_8), "audio/wav", 11));
        when(asrClient.transcribe(eq("demo.wav"), eq("audio/wav"), any()))
            .thenReturn(new AsrTranscription(
                1.2,
                "ru",
                0.99,
                List.of(new AsrTranscription.AsrSegment(
                    0.0,
                    1.2,
                    "privet mir",
                    List.of(new AsrTranscription.AsrWord(0.0, 0.5, "privet"))
                ))
            ));
        when(reportRepository.findByJobId(jobId)).thenReturn(Optional.empty());
        when(sessionRepository.findById(sessionId)).thenReturn(Optional.of(session));
        when(pdfReportGenerator.generate(eq("Demo session"), any())).thenReturn("pdf".getBytes(StandardCharsets.UTF_8));
        when(artifactService.storeArtifact(eq(job), any(), any(), any(), any())).thenReturn(storedArtifact);

        worker.consume(new ProcessJobMessage(jobId, userId, sessionId, uploadId));

        ArgumentCaptor<ArtifactType> typeCaptor = ArgumentCaptor.forClass(ArtifactType.class);
        ArgumentCaptor<byte[]> bytesCaptor = ArgumentCaptor.forClass(byte[].class);
        verify(artifactService, org.mockito.Mockito.atLeastOnce())
            .storeArtifact(eq(job), typeCaptor.capture(), eq("application/json"), bytesCaptor.capture(), any());

        int asrCallIndex = typeCaptor.getAllValues().indexOf(ArtifactType.ASR_TRANSCRIPT_JSON);
        assertThat(asrCallIndex).isGreaterThanOrEqualTo(0);
        String storedTranscript = new String(bytesCaptor.getAllValues().get(asrCallIndex), StandardCharsets.UTF_8);
        assertThat(storedTranscript).contains("\"language\":\"ru\"");
        assertThat(storedTranscript).contains("privet mir");
        verify(jobService).markDone(jobId);
    }
}
