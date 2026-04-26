package com.speechgym.asr;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.http.HttpMethod.POST;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.method;
import static org.springframework.test.web.client.match.MockRestRequestMatchers.requestTo;
import static org.springframework.test.web.client.response.MockRestResponseCreators.withSuccess;

import java.net.ConnectException;
import java.time.Duration;
import java.util.List;

import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;
import org.springframework.test.web.client.MockRestServiceServer;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.ResourceAccessException;

import com.speechgym.common.config.AppProperties;

class AsrHttpClientTest {
    @Test
    void transcribeMapsAsrResponse() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        server.expect(requestTo("http://localhost:8000/transcribe"))
            .andExpect(method(POST))
            .andRespond(withSuccess("""
                {
                  "duration": 12.5,
                  "language": "ru",
                  "language_probability": 0.98,
                  "segments": [
                    {
                      "start": 0.0,
                      "end": 1.1,
                      "text": "privet",
                      "words": [
                        {
                          "start": 0.0,
                          "end": 1.1,
                          "word": "privet"
                        }
                      ]
                    }
                  ]
                }
                """, MediaType.APPLICATION_JSON));

        AppProperties properties = new AppProperties(
            "/api/v1",
            new AppProperties.IdempotencyProperties(Duration.ofHours(24)),
            new AppProperties.JwtProperties("issuer", "secret", Duration.ofMinutes(15), Duration.ofDays(14)),
            new AppProperties.RabbitProperties("exchange", "queue", "routing"),
            new AppProperties.StorageProperties(
                "uploads",
                "artifacts",
                Duration.ofMinutes(15),
                new AppProperties.MinioProperties("http://localhost:9000", "key", "secret", false)
            ),
            new AppProperties.AsrProperties(
                "http://localhost:8000",
                "/transcribe",
                "/health",
                Duration.ofSeconds(5),
                Duration.ofMinutes(10),
                5,
                Duration.ofSeconds(2),
                Duration.ofSeconds(15)
            )
        );
        AsrHttpClient client = new AsrHttpClient(builder.baseUrl("http://localhost:8000").build(), properties);

        AsrTranscription transcription = client.transcribe("demo.wav", "audio/wav", "audio".getBytes());

        assertThat(transcription.language()).isEqualTo("ru");
        assertThat(transcription.languageProbability()).isEqualTo(0.98);
        assertThat(transcription.segments()).hasSize(1);
        assertThat(transcription.segments().getFirst().text()).isEqualTo("privet");
        assertThat(transcription.segments().getFirst().words())
            .extracting(AsrTranscription.AsrWord::word)
            .isEqualTo(List.of("privet"));
        server.verify();
    }

    @Test
    void transcribeRetriesTransientConnectionFailures() {
        RestClient.Builder builder = RestClient.builder();
        MockRestServiceServer server = MockRestServiceServer.bindTo(builder).build();
        server.expect(requestTo("http://localhost:8000/transcribe"))
            .andExpect(method(POST))
            .andRespond(request -> {
                throw new ResourceAccessException("I/O error", new ConnectException("Connection refused"));
            });
        server.expect(requestTo("http://localhost:8000/transcribe"))
            .andExpect(method(POST))
            .andRespond(withSuccess("""
                {
                  "duration": 5.0,
                  "language": "ru",
                  "language_probability": 0.97,
                  "segments": []
                }
                """, MediaType.APPLICATION_JSON));

        AppProperties properties = new AppProperties(
            "/api/v1",
            new AppProperties.IdempotencyProperties(Duration.ofHours(24)),
            new AppProperties.JwtProperties("issuer", "secret", Duration.ofMinutes(15), Duration.ofDays(14)),
            new AppProperties.RabbitProperties("exchange", "queue", "routing"),
            new AppProperties.StorageProperties(
                "uploads",
                "artifacts",
                Duration.ofMinutes(15),
                new AppProperties.MinioProperties("http://localhost:9000", "key", "secret", false)
            ),
            new AppProperties.AsrProperties(
                "http://localhost:8000",
                "/transcribe",
                "/health",
                Duration.ofSeconds(5),
                Duration.ofMinutes(10),
                2,
                Duration.ZERO,
                Duration.ZERO
            )
        );
        AsrHttpClient client = new AsrHttpClient(builder.baseUrl("http://localhost:8000").build(), properties);

        AsrTranscription transcription = client.transcribe("demo.wav", "audio/wav", "audio".getBytes());

        assertThat(transcription.language()).isEqualTo("ru");
        server.verify();
    }
}
