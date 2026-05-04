package com.speechgym.reports;

import java.time.Duration;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;

import com.speechgym.common.config.AppProperties;

@Service
public class SpeechReportHttpClient implements SpeechReportClient {
    private static final Logger log = LoggerFactory.getLogger(SpeechReportHttpClient.class);

    private final RestClient restClient;
    private final AppProperties.ReportProperties properties;

    public SpeechReportHttpClient(
        @Qualifier("reportRestClient") RestClient reportRestClient,
        AppProperties appProperties
    ) {
        this.restClient = reportRestClient;
        this.properties = appProperties.report();
    }

    @Override
<<<<<<< Updated upstream
    public ReportAnalysisResponse generateReport(Map<String, Object> whisperJson, String pitchType, int targetDurationSec, String notes) {
=======
    public ReportAnalysisResponse generateReport(
        Map<String, Object> whisperJson,
        String pitchType,
        int targetDurationSec,
        String notes
    ) {
>>>>>>> Stashed changes
        int maxAttempts = Math.max(1, properties.maxAttempts());
        Duration backoff = normalizeDuration(properties.initialBackoff());
        Duration maxBackoff = normalizeDuration(properties.maxBackoff());

        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return executeReport(whisperJson, pitchType, targetDurationSec, notes);
            }
            catch (Exception exception) {
                if (!isRetriable(exception) || attempt == maxAttempts) {
                    log.error(
                        "Report request failed for pitchType={} targetDurationSec={} attempt={}/{}",
                        pitchType,
                        targetDurationSec,
                        attempt,
                        maxAttempts,
                        exception
                    );
                    throw new IllegalStateException("Unable to generate speech report.", exception);
                }

                long delayMs = backoff.toMillis();
                log.warn(
                    "Report request transient failure for pitchType={} targetDurationSec={} attempt={}/{}. Retrying in {} ms.",
                    pitchType,
                    targetDurationSec,
                    attempt,
                    maxAttempts,
                    delayMs,
                    exception
                );
                pauseBeforeRetry(backoff);
                backoff = nextBackoff(backoff, maxBackoff);
            }
        }

        throw new IllegalStateException("Unable to generate speech report.");
    }

<<<<<<< Updated upstream
    private ReportAnalysisResponse executeReport(Map<String, Object> whisperJson, String pitchType, int targetDurationSec, String notes) {
=======
    private ReportAnalysisResponse executeReport(
        Map<String, Object> whisperJson,
        String pitchType,
        int targetDurationSec,
        String notes
    ) {
>>>>>>> Stashed changes
        ReportAnalysisResponse response = restClient.post()
            .uri(properties.reportPath())
            .contentType(MediaType.APPLICATION_JSON)
            .body(new ReportAnalysisRequest(whisperJson, pitchType, targetDurationSec, notes))
            .retrieve()
            .body(ReportAnalysisResponse.class);
        if (response == null) {
            throw new IllegalStateException("Report service returned an empty body.");
        }
        return response;
    }

    private boolean isRetriable(Exception exception) {
        if (exception instanceof ResourceAccessException) {
            return true;
        }
        if (exception instanceof RestClientResponseException responseException) {
            return responseException.getStatusCode().is5xxServerError();
        }
        return false;
    }

    private Duration normalizeDuration(Duration duration) {
        if (duration == null || duration.isNegative()) {
            return Duration.ZERO;
        }
        return duration;
    }

    private Duration nextBackoff(Duration currentBackoff, Duration maxBackoff) {
        long currentMs = currentBackoff.toMillis();
        if (currentMs <= 0L) {
            return Duration.ZERO;
        }
        long nextMs = currentMs * 2L;
        long maxMs = maxBackoff.toMillis();
        if (maxMs > 0L) {
            nextMs = Math.min(nextMs, maxMs);
        }
        return Duration.ofMillis(nextMs);
    }

    private void pauseBeforeRetry(Duration backoff) {
        long delayMs = backoff.toMillis();
        if (delayMs <= 0L) {
            return;
        }
        try {
            Thread.sleep(delayMs);
        }
        catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Report retry interrupted.", exception);
        }
    }
}
