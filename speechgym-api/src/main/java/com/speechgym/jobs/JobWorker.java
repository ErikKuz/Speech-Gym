package com.speechgym.jobs;

import java.util.ArrayList;
import java.util.List;
import java.util.LinkedHashSet;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.regex.Pattern;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.speechgym.asr.AsrClient;
import com.speechgym.asr.AsrTranscription;
import com.speechgym.artifacts.ArtifactEntity;
import com.speechgym.artifacts.ArtifactService;
import com.speechgym.artifacts.ArtifactType;
import com.speechgym.reports.PdfReportGenerator;
import com.speechgym.reports.ReportAnalysisResponse;
import com.speechgym.reports.ReportEntity;
import com.speechgym.reports.ReportGenerationResult;
import com.speechgym.reports.ReportRepository;
import com.speechgym.reports.SpeechReportClient;
import com.speechgym.sessions.SessionEntity;
import com.speechgym.sessions.SessionRepository;
import com.speechgym.storage.StorageService;
import com.speechgym.storage.StoredObject;
import com.speechgym.uploads.UploadEntity;
import com.speechgym.uploads.UploadService;

@Component
public class JobWorker {
    private static final Logger log = LoggerFactory.getLogger(JobWorker.class);
    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {
    };
    private static final Pattern WORD_PATTERN = Pattern.compile("[\\p{L}\\p{N}]+(?:[-'][\\p{L}\\p{N}]+)?");
    private static final String DEFAULT_PITCH_TYPE = "investor_pitch";
    private static final Set<String> SINGLE_WORD_FILLERS = Set.of(
        "э",
        "ээ",
        "эээ",
        "эм",
        "ну",
        "типа",
        "значит",
        "короче",
        "собственно"
    );
    private static final List<List<String>> MULTI_WORD_FILLERS = List.of(
        List.of("как", "бы"),
        List.of("в", "общем"),
        List.of("так", "сказать"),
        List.of("на", "самом", "деле"),
        List.of("это", "самое")
    );

    private final JobService jobService;
    private final UploadService uploadService;
    private final StorageService storageService;
    private final AsrClient asrClient;
    private final SpeechReportClient speechReportClient;
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
        SpeechReportClient speechReportClient,
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
        this.speechReportClient = speechReportClient;
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

        SessionEntity session = sessionRepository.findById(job.getSessionId())
            .orElseThrow(() -> new IllegalStateException("Session missing for job."));
        Map<String, Object> whisperJson = objectMapper.convertValue(transcription, MAP_TYPE);
        String pitchType = resolvePitchType(job);
        int targetDurationSec = resolveTargetDurationSec(job, session, transcription);
        String notes = resolveAnalysisNotes(job, session);

        job = jobService.markStage(message.jobId(), JobStatus.RUNNING_NLP, 45, "NLP stage started.");
        log.info(
            "Submitting jobId={} to report service with pitchType={} targetDurationSec={}",
            job.getId(),
            pitchType,
            targetDurationSec
        );
        ReportAnalysisResponse analysis = speechReportClient.generateReport(whisperJson, pitchType, targetDurationSec, notes);
        byte[] nlp = jsonBytes(analysis);
        artifactService.storeArtifact(job, ArtifactType.NLP_ANALYSIS_JSON, "application/json", nlp, Map.of(
            "stage", "NLP",
            "source", "speechgym-report-service",
            "pitchType", pitchType,
            "targetDurationSec", targetDurationSec
        ));
        jobService.markStageCompleted(
            job.getId(),
            JobStatus.RUNNING_NLP,
            60,
            "NLP stage completed.",
            buildNlpStageMetadata(analysis)
        );

        job = jobService.markStage(message.jobId(), JobStatus.RUNNING_VOICE, 75, "Voice stage started.");
        VoiceMetrics voiceMetrics = buildVoiceMetrics(transcription, analysis);
        byte[] voice = jsonBytes(Map.of(
            "paceWpm", voiceMetrics.paceWpm(),
            "confidence", voiceMetrics.confidence(),
            "clarity", voiceMetrics.clarity(),
            "fillerWordsCount", voiceMetrics.fillerWordsCount()
        ));
        artifactService.storeArtifact(job, ArtifactType.VOICE_METRICS_JSON, "application/json", voice, Map.of(
            "stage", "VOICE"
        ));
        jobService.markStageCompleted(job.getId(), JobStatus.RUNNING_VOICE, 85, "Voice stage completed.", Map.of(
            "paceWpm", voiceMetrics.paceWpm(),
            "fillerWordsCount", voiceMetrics.fillerWordsCount()
        ));

        job = jobService.markStage(message.jobId(), JobStatus.RUNNING_REPORT, 92, "Report stage started.");
        ReportGenerationResult result = buildReportResult(analysis, voiceMetrics);
        byte[] pdf = pdfReportGenerator.generate(session.getTitle(), result, analysis);
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

    private Map<String, Object> buildNlpStageMetadata(ReportAnalysisResponse analysis) {
        ReportAnalysisResponse.PassportPitch passportPitch = analysis.report().passportPitch();
        ReportAnalysisResponse.NextPitch nextPitch = analysis.report().nextPitch();
        return Map.of(
            "strengths", passportPitch.strengths().size(),
            "blockers", passportPitch.blockers().size(),
            "nextPitchBlocks", nextPitch.blocks().size()
        );
    }

    private VoiceMetrics buildVoiceMetrics(AsrTranscription transcription, ReportAnalysisResponse analysis) {
        List<String> tokens = tokenizeWords(transcription.text());
        int wordCount = tokens.size();
        int fillerWordsCount = countFillerWords(tokens);
        int paceWpm = calculatePaceWpm(wordCount, estimateDurationSec(transcription));
        int strengthBoost = Math.min(12, analysis.report().passportPitch().strengths().size() * 4);
        int blockerPenalty = Math.min(18, analysis.report().passportPitch().blockers().size() * 5);
        int fillerPenalty = Math.min(16, fillerWordsCount * 2);
        int pacePenalty = pacePenalty(paceWpm);

        int clarity = clamp(86 + strengthBoost - blockerPenalty - fillerPenalty - pacePenalty, 45, 98);
        int confidence = clamp(82 + strengthBoost - blockerPenalty - Math.min(12, fillerWordsCount) - (pacePenalty / 2), 45, 96);
        return new VoiceMetrics(paceWpm, fillerWordsCount, clarity, confidence);
    }

    private ReportGenerationResult buildReportResult(ReportAnalysisResponse analysis, VoiceMetrics voiceMetrics) {
        ReportAnalysisResponse.PassportPitch passportPitch = analysis.report().passportPitch();
        ReportAnalysisResponse.NextPitch nextPitch = analysis.report().nextPitch();
        ReportAnalysisResponse.Recommendations recommendations = analysis.report().recommendations();

        List<String> strengths = mergeOrderedUnique(passportPitch.strengths());
        List<String> improvements = mergeOrderedUnique(passportPitch.blockers());
        List<String> recommendationTitles = recommendations.changes().stream()
            .map(ReportAnalysisResponse.RecommendationChange::title)
            .toList();
        List<String> mergedRecommendations = mergeOrderedUnique(
            passportPitch.nextVersionChanges(),
            recommendations.summary(),
            recommendationTitles
        );

        int structureScore = clamp(
            70
                + Math.min(16, nextPitch.blocks().size() * 2)
                + Math.min(8, recommendations.changes().size())
                + Math.min(6, strengths.size() * 2)
                - Math.min(12, improvements.size() * 4),
            45,
            97
        );
        int overallScore = clamp(
            (int) Math.round(
                (voiceMetrics.clarity() * 0.35)
                    + (voiceMetrics.confidence() * 0.25)
                    + (structureScore * 0.40)
            ),
            45,
            97
        );
        String emotionalTone = resolveEmotionalTone(voiceMetrics.confidence());

        return new ReportGenerationResult(
            overallScore,
            voiceMetrics.clarity(),
            voiceMetrics.paceWpm(),
            voiceMetrics.fillerWordsCount(),
            voiceMetrics.confidence(),
            structureScore,
            emotionalTone,
            strengths,
            improvements,
            mergedRecommendations
        );
    }

    private String resolvePitchType(JobEntity job) {
        String optionValue = readStringOption(job, "pitchType", "pitch_type");
        if (optionValue == null || optionValue.isBlank()) {
            return DEFAULT_PITCH_TYPE;
        }
        String normalized = optionValue.trim()
            .toLowerCase(Locale.ROOT)
            .replace('-', '_')
            .replace(' ', '_')
            .replaceAll("[^a-z0-9_]+", "");
        return normalized.isBlank() ? DEFAULT_PITCH_TYPE : normalized;
    }

    private int resolveTargetDurationSec(JobEntity job, SessionEntity session, AsrTranscription transcription) {
        Integer optionValue = readIntOption(job, "targetDurationSec", "target_duration_sec");
        if (optionValue != null) {
            return clamp(optionValue, 30, 1800);
        }
        if (session != null && session.getDurationTargetSeconds() > 0) {
            return clamp(session.getDurationTargetSeconds(), 30, 1800);
        }
        int derivedDuration = (int) Math.round(Math.max(estimateDurationSec(transcription), 30.0d));
        return clamp(derivedDuration, 30, 1800);
    }

    private String resolveAnalysisNotes(JobEntity job, SessionEntity session) {
        String optionValue = readStringOption(job, "notes", "userNotes", "user_notes", "sessionNotes", "session_notes");
        if (optionValue != null && !optionValue.isBlank()) {
            return optionValue.trim();
        }
        if (session != null && session.getNotes() != null) {
            return session.getNotes().trim();
        }
        return "";
    }

    private String readStringOption(JobEntity job, String... keys) {
        Map<String, Object> options = job.getOptionsJson();
        if (options == null || options.isEmpty()) {
            return null;
        }
        for (String key : keys) {
            Object value = options.get(key);
            if (value instanceof String stringValue && !stringValue.isBlank()) {
                return stringValue;
            }
        }
        return null;
    }

    private Integer readIntOption(JobEntity job, String... keys) {
        Map<String, Object> options = job.getOptionsJson();
        if (options == null || options.isEmpty()) {
            return null;
        }
        for (String key : keys) {
            Object value = options.get(key);
            if (value instanceof Number numberValue) {
                return numberValue.intValue();
            }
            if (value instanceof String stringValue) {
                try {
                    return Integer.parseInt(stringValue.trim());
                }
                catch (NumberFormatException ignored) {
                    // Ignore malformed option values and fall back to derived duration.
                }
            }
        }
        return null;
    }

    private List<String> tokenizeWords(String text) {
        String source = text == null ? "" : text.toLowerCase(Locale.ROOT);
        java.util.regex.Matcher matcher = WORD_PATTERN.matcher(source);
        List<String> tokens = new ArrayList<>();
        while (matcher.find()) {
            tokens.add(matcher.group());
        }
        return tokens;
    }

    private int countFillerWords(List<String> tokens) {
        int count = 0;
        for (int index = 0; index < tokens.size(); index++) {
            if (SINGLE_WORD_FILLERS.contains(tokens.get(index))) {
                count++;
            }
            for (List<String> phrase : MULTI_WORD_FILLERS) {
                if (matchesPhrase(tokens, index, phrase)) {
                    count++;
                }
            }
        }
        return count;
    }

    private boolean matchesPhrase(List<String> tokens, int startIndex, List<String> phrase) {
        if (startIndex + phrase.size() > tokens.size()) {
            return false;
        }
        for (int offset = 0; offset < phrase.size(); offset++) {
            if (!phrase.get(offset).equals(tokens.get(startIndex + offset))) {
                return false;
            }
        }
        return true;
    }

    private int calculatePaceWpm(int wordCount, double durationSec) {
        if (wordCount <= 0 || durationSec <= 0.0d) {
            return 0;
        }
        return (int) Math.round((wordCount * 60.0d) / durationSec);
    }

    private double estimateDurationSec(AsrTranscription transcription) {
        if (transcription.duration() > 0.0d) {
            return transcription.duration();
        }
        double minStart = Double.MAX_VALUE;
        double maxEnd = 0.0d;
        for (AsrTranscription.AsrSegment segment : transcription.segments()) {
            minStart = Math.min(minStart, segment.start());
            maxEnd = Math.max(maxEnd, segment.end());
        }
        if (minStart == Double.MAX_VALUE || maxEnd <= minStart) {
            return 0.0d;
        }
        return maxEnd - minStart;
    }

    private int pacePenalty(int paceWpm) {
        if (paceWpm <= 0) {
            return 12;
        }
        return Math.min(14, Math.abs(paceWpm - 145) / 4);
    }

    private List<String> mergeOrderedUnique(List<String>... lists) {
        LinkedHashSet<String> values = new LinkedHashSet<>();
        for (List<String> list : lists) {
            if (list == null) {
                continue;
            }
            for (String value : list) {
                if (value == null) {
                    continue;
                }
                String cleaned = value.trim();
                if (!cleaned.isBlank()) {
                    values.add(cleaned);
                }
            }
        }
        return List.copyOf(values);
    }

    private String resolveEmotionalTone(int confidence) {
        if (confidence >= 85) {
            return "confident";
        }
        if (confidence >= 72) {
            return "steady";
        }
        if (confidence >= 58) {
            return "neutral";
        }
        return "uncertain";
    }

    private int clamp(int value, int min, int max) {
        return Math.max(min, Math.min(max, value));
    }

    private record VoiceMetrics(
        int paceWpm,
        int fillerWordsCount,
        int clarity,
        int confidence
    ) {
    }
}
