package com.speechgym.asr;

import java.io.ByteArrayInputStream;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.InputStreamResource;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.MediaTypeFactory;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestClient;

import com.speechgym.common.config.AppProperties;

@Service
public class AsrHttpClient implements AsrClient {
    private static final Logger log = LoggerFactory.getLogger(AsrHttpClient.class);

    private final RestClient restClient;
    private final AppProperties.AsrProperties properties;

    public AsrHttpClient(RestClient asrRestClient, AppProperties appProperties) {
        this.restClient = asrRestClient;
        this.properties = appProperties.asr();
    }

    @Override
    public AsrTranscription transcribe(String filename, String contentType, byte[] audioBytes) {
        HttpHeaders partHeaders = new HttpHeaders();
        partHeaders.setContentType(resolveContentType(contentType, filename));
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", new HttpEntity<>(new NamedInputStreamResource(audioBytes, filename), partHeaders));

        try {
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
        catch (Exception exception) {
            log.error("ASR request failed for file={}", filename, exception);
            throw new IllegalStateException("Unable to transcribe audio with ASR service.", exception);
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
