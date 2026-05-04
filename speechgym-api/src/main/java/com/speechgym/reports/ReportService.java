package com.speechgym.reports;

import java.io.IOException;
import java.util.Map;
import java.util.UUID;
import java.util.List;
import java.util.Optional;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.speechgym.artifacts.ArtifactEntity;
import com.speechgym.artifacts.ArtifactRepository;
import com.speechgym.artifacts.ArtifactType;
import com.speechgym.common.error.ResourceNotFoundException;
import com.speechgym.reports.dto.ReportSummaryResponse;
import com.speechgym.sessions.SessionService;
import com.speechgym.storage.StoredObject;
import com.speechgym.storage.StorageService;
import com.fasterxml.jackson.databind.ObjectMapper;

@Service
public class ReportService {
    private static final Logger log = LoggerFactory.getLogger(ReportService.class);

    private final ReportRepository reportRepository;
    private final ArtifactRepository artifactRepository;
    private final StorageService storageService;
    private final SessionService sessionService;
    private final ObjectMapper objectMapper;

    public ReportService(
        ReportRepository reportRepository,
        ArtifactRepository artifactRepository,
        StorageService storageService,
        SessionService sessionService,
        ObjectMapper objectMapper
    ) {
        this.reportRepository = reportRepository;
        this.artifactRepository = artifactRepository;
        this.storageService = storageService;
        this.sessionService = sessionService;
        this.objectMapper = objectMapper;
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
        ReportAnalysisResponse analysis = loadDetailedAnalysis(report.getUserId(), report.getJobId())
            .orElseGet(() -> new ReportAnalysisResponse(null, null));
        ReportAnalysisResponse.PassportPitch passportPitch = analysis.report().passportPitch();
        ReportAnalysisResponse.NextPitch nextPitch = analysis.report().nextPitch();
        ReportAnalysisResponse.Recommendations detailedRecommendations = analysis.report().recommendations();
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
            passportPitch.nextVersionChanges(),
            mapNextVersion(nextPitch),
            detailedRecommendations.summary(),
            mapRecommendationDetails(detailedRecommendations.changes()),
            mapAnalysisMeta(analysis.meta()),
            report.getCreatedAt()
        );
    }

    private Optional<ReportAnalysisResponse> loadDetailedAnalysis(UUID userId, UUID jobId) {
        return artifactRepository.findByJobIdAndTypeAndUserId(jobId, ArtifactType.NLP_ANALYSIS_JSON, userId)
            .flatMap(this::readAnalysisArtifact);
    }

    private Optional<ReportAnalysisResponse> readAnalysisArtifact(ArtifactEntity artifact) {
        StoredObject storedObject = storageService.getObject(artifact.getBucketName(), artifact.getObjectKey());
        if (storedObject == null || storedObject.content() == null || storedObject.content().length == 0) {
            return Optional.empty();
        }
        try {
            return Optional.of(objectMapper.readValue(storedObject.content(), ReportAnalysisResponse.class));
        }
        catch (IOException exception) {
            log.warn(
                "Unable to parse NLP analysis artifact artifactId={} jobId={}",
                artifact.getId(),
                artifact.getJobId(),
                exception
            );
            return Optional.empty();
        }
    }

    private ReportSummaryResponse.NextVersionResponse mapNextVersion(ReportAnalysisResponse.NextPitch nextPitch) {
        return new ReportSummaryResponse.NextVersionResponse(
            nextPitch.title(),
            nextPitch.blocks().stream()
                .map(block -> new ReportSummaryResponse.NextVersionBlockResponse(block.label(), block.text()))
                .toList(),
            nextPitch.fullText()
        );
    }

    private List<ReportSummaryResponse.RecommendationDetailResponse> mapRecommendationDetails(
        List<ReportAnalysisResponse.RecommendationChange> changes
    ) {
        return changes.stream()
            .map(change -> new ReportSummaryResponse.RecommendationDetailResponse(
                change.title(),
                change.before(),
                change.after(),
                change.whyBeforeWeaker(),
                change.whyAfterBetter(),
                new ReportSummaryResponse.AudienceEffectResponse(
                    change.audienceEffect().understandsBetter(),
                    change.audienceEffect().feelsMore()
                )
            ))
            .toList();
    }

    private ReportSummaryResponse.AnalysisMetaResponse mapAnalysisMeta(ReportAnalysisResponse.Meta meta) {
        return new ReportSummaryResponse.AnalysisMetaResponse(
            meta.pitchType(),
            meta.language(),
            meta.targetDurationSec(),
            meta.actualDurationSec(),
            meta.actualDuration(),
            meta.actualSpeakingRateWpm(),
            meta.notesUsed(),
            meta.model()
        );
    }

    ReportEntity requireOwnedReport(UUID userId, UUID reportId) {
        return reportRepository.findByIdAndUserId(reportId, userId)
            .orElseThrow(() -> new ResourceNotFoundException("Report was not found."));
    }
}
