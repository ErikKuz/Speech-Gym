package com.speechgym.asr;

import java.io.ByteArrayInputStream;
import java.time.Duration;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.core.io.InputStreamResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.MediaTypeFactory;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;

import com.speechgym.common.config.AppProperties;

@Service
public class AsrHttpClient implements AsrClient {
    private static final Logger log = LoggerFactory.getLogger(AsrHttpClient.class);

    private final RestClient restClient;
    private final AppProperties.AsrProperties properties;

    public AsrHttpClient(@Qualifier("asrRestClient") RestClient asrRestClient, AppProperties appProperties) {
        this.restClient = asrRestClient;
        this.properties = appProperties.asr();
    }

    @Override
    public AsrTranscription transcribe(String filename, String contentType, byte[] audioBytes) {
        int maxAttempts = Math.max(1, properties.maxAttempts());
        Duration backoff = normalizeDuration(properties.initialBackoff());
        Duration maxBackoff = normalizeDuration(properties.maxBackoff());

        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return executeTranscribe(filename, contentType, audioBytes);
            }
            catch (Exception exception) {
                if (!isRetriable(exception) || attempt == maxAttempts) {
                    log.error("ASR request failed for file={} attempt={}/{}", filename, attempt, maxAttempts, exception);
                    throw new IllegalStateException("Unable to transcribe audio with ASR service.", exception);
                }

                long delayMs = backoff.toMillis();
                log.warn(
                    "ASR request transient failure for file={} attempt={}/{}. Retrying in {} ms.",
                    filename,
                    attempt,
                    maxAttempts,
                    delayMs,
                    exception
                );
                pauseBeforeRetry(backoff);
                backoff = nextBackoff(backoff, maxBackoff);
            }
        }

        throw new IllegalStateException("Unable to transcribe audio with ASR service.");
    }

    private AsrTranscription executeTranscribe(String filename, String contentType, byte[] audioBytes) {
        HttpHeaders partHeaders = new HttpHeaders();
        partHeaders.setContentType(resolveContentType(contentType, filename));
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", new HttpEntity<>(new NamedInputStreamResource(audioBytes, filename), partHeaders));

        AsrTranscription response = restClient.post()
            .uri(properties.transcribePath())
            .contentType(MediaType.MULTIPART_FORM_DATA)
            .body(body)
            .retrieve()
            .body(AsrTranscription.class);
        if (response == null) {
            throw new IllegalStateException("ASR service returned an empty body.");
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
            throw new IllegalStateException("ASR retry interrupted.", exception);
        }
    }

    private MediaType resolveContentType(String contentType, String filename) {
        if (contentType != null && !contentType.isBlank()) {
            try {
                return MediaType.parseMediaType(contentType);
            }
            catch (Exception ignored) {
                // Fall back to extension-based detection below.
            }
        }
        return MediaTypeFactory.getMediaType(filename).orElse(MediaType.APPLICATION_OCTET_STREAM);
    }

    private static final class NamedInputStreamResource extends InputStreamResource {
        private final String filename;

        private NamedInputStreamResource(byte[] bytes, String filename) {
            super(new ByteArrayInputStream(bytes));
            this.filename = filename == null || filename.isBlank() ? "audio.bin" : filename;
        }

        @Override
        public String getFilename() {
            return filename;
        }

        @Override
        public long contentLength() {
            return -1;
        }
    }
}
