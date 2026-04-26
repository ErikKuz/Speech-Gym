package com.speechgym.reports;

import java.util.Map;
import java.util.UUID;
import java.util.List;

import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.speechgym.artifacts.ArtifactEntity;
import com.speechgym.artifacts.ArtifactRepository;
import com.speechgym.common.error.ResourceNotFoundException;
import com.speechgym.reports.dto.ReportSummaryResponse;
import com.speechgym.sessions.SessionService;
import com.speechgym.storage.StoredObject;
import com.speechgym.storage.StorageService;

@Service
public class ReportService {
    private final ReportRepository reportRepository;
    private final ArtifactRepository artifactRepository;
    private final StorageService storageService;
    private final SessionService sessionService;

    public ReportService(
        ReportRepository reportRepository,
        ArtifactRepository artifactRepository,
        StorageService storageService,
        SessionService sessionService
    ) {
        this.reportRepository = reportRepository;
        this.artifactRepository = artifactRepository;
        this.storageService = storageService;
        this.sessionService = sessionService;
    }

    @Transactional(readOnly = true)
    public ReportSummaryResponse get(UUID userId, UUID reportId) {
        ReportEntity report = requireOwnedReport(userId, reportId);
        return toResponse(report);
    }

    @Transactional(readOnly = true)
    public List<ReportSummaryResponse> listBySession(UUID userId, UUID sessionId) {
        sessionService.requireOwnedSession(userId, sessionId);
        return reportRepository.findBySessionIdAndUserIdOrderByCreatedAtAsc(sessionId, userId).stream()
            .map(this::toResponse)
            .toList();
    }

    @Transactional(readOnly = true)
    public ResponseEntity<byte[]> downloadPdf(UUID userId, UUID reportId) {
        ReportEntity report = requireOwnedReport(userId, reportId);
        ArtifactEntity artifact = artifactRepository.findByIdAndUserId(report.getPdfArtifactId(), userId)
            .orElseThrow(() -> new ResourceNotFoundException("Report PDF was not found."));
        StoredObject storedObject = storageService.getObject(artifact.getBucketName(), artifact.getObjectKey());
        return ResponseEntity.ok()
            .contentType(MediaType.APPLICATION_PDF)
            .header(
                HttpHeaders.CONTENT_DISPOSITION,
                ContentDisposition.attachment().filename("speechgym-report-" + reportId + ".pdf").build().toString()
            )
            .body(storedObject.content());
    }

    ReportSummaryResponse toResponse(ReportEntity report) {
        return new ReportSummaryResponse(
            report.getId(),
            report.getJobId(),
            report.getSessionId(),
            report.getOverallScore(),
            report.getClarity(),
            report.getPaceWpm(),
            report.getFillerWordsCount(),
            report.getConfidence(),
            report.getStructureScore(),
            report.getEmotionalTone(),
            report.getStrengths(),
            report.getImprovements(),
            report.getRecommendations(),
            report.getCreatedAt()
        );
    }

    ReportEntity requireOwnedReport(UUID userId, UUID reportId) {
        return reportRepository.findByIdAndUserId(reportId, userId)
            .orElseThrow(() -> new ResourceNotFoundException("Report was not found."));
    }
}
