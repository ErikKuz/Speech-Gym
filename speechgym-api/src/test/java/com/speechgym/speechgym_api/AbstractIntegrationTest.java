package com.speechgym.speechgym_api;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.net.URI;
import java.time.Duration;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

import org.junit.jupiter.api.BeforeEach;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Primary;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import com.jayway.jsonpath.JsonPath;
import com.speechgym.artifacts.ArtifactRepository;
import com.speechgym.auth.SubscriptionRepository;
import com.speechgym.auth.UserRepository;
import com.speechgym.common.config.AppProperties;
import com.speechgym.common.idempotency.IdempotencyKeyRepository;
import com.speechgym.jobs.JobEventRepository;
import com.speechgym.jobs.JobPublisher;
import com.speechgym.jobs.JobRepository;
import com.speechgym.jobs.PostAsrJobMessage;
import com.speechgym.jobs.ProcessJobMessage;
import com.speechgym.reports.ReportRepository;
import com.speechgym.sessions.SessionRepository;
import com.speechgym.storage.StorageService;
import com.speechgym.storage.StoredObject;
import com.speechgym.uploads.UploadRepository;

@SpringBootTest
@AutoConfigureMockMvc
@Import(AbstractIntegrationTest.TestStorageConfiguration.class)
abstract class AbstractIntegrationTest {
    @Autowired
    protected MockMvc mockMvc;

    @Autowired
    protected SessionRepository sessionRepository;

    @Autowired
    protected UploadRepository uploadRepository;

    @Autowired
    protected JobRepository jobRepository;

    @Autowired
    protected JobEventRepository jobEventRepository;

    @Autowired
    protected ArtifactRepository artifactRepository;

    @Autowired
    protected ReportRepository reportRepository;

    @Autowired
    protected StorageService storageService;

    @Autowired
    protected IdempotencyKeyRepository idempotencyKeyRepository;

    @Autowired
    protected SubscriptionRepository subscriptionRepository;

    @Autowired
    protected UserRepository userRepository;

    @BeforeEach
    void cleanDatabase() {
        reportRepository.deleteAll();
        artifactRepository.deleteAll();
        jobEventRepository.deleteAll();
        jobRepository.deleteAll();
        uploadRepository.deleteAll();
        sessionRepository.deleteAll();
        idempotencyKeyRepository.deleteAll();
        subscriptionRepository.deleteAll();
        userRepository.deleteAll();
    }

    protected String registerAndLogin(String email) throws Exception {
        mockMvc.perform(post("/api/v1/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                      "email":"%s",
                      "password":"Password123",
                      "fullName":"Test User"
                    }
                    """.formatted(email)))
            .andExpect(status().isCreated());
        return login(email, "Password123");
    }

    protected String login(String email, String password) throws Exception {
        MvcResult result = mockMvc.perform(post("/api/v1/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                      "email":"%s",
                      "password":"%s"
                    }
                    """.formatted(email, password)))
            .andExpect(status().isOk())
            .andReturn();
        return JsonPath.read(result.getResponse().getContentAsString(), "$.accessToken");
    }

    protected String createSession(String token, String title) throws Exception {
        MvcResult result = mockMvc.perform(post("/api/v1/sessions")
                .header("Authorization", "Bearer " + token)
                .header("Idempotency-Key", UUID.randomUUID().toString())
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                      "title":"%s",
                      "goal":"Practice keynote",
                      "scenario":"KEYNOTE",
                      "languageCode":"en",
                      "audienceType":"team",
                      "durationTargetSeconds":300,
                      "presentationStyle":"confident",
                      "notes":"Keep it sharp",
                      "difficultyLevel":"MEDIUM",
                      "coachingMode":"BALANCED"
                    }
                    """.formatted(title)))
            .andExpect(status().isCreated())
            .andReturn();
        return JsonPath.read(result.getResponse().getContentAsString(), "$.sessionId").toString();
    }

    protected String createUpload(String token, String sessionId) throws Exception {
        MvcResult result = mockMvc.perform(
                org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart("/api/v1/sessions/{sessionId}/uploads", sessionId)
                    .file("file", "fake-audio".getBytes())
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .header("Authorization", "Bearer " + token)
            )
            .andExpect(status().isOk())
            .andReturn();
        return JsonPath.read(result.getResponse().getContentAsString(), "$.uploadId").toString();
    }

    @TestConfiguration
    static class TestStorageConfiguration {
        @Bean
        @Primary
        StorageService storageService() {
            return new StorageService() {
                private final Map<String, StoredObject> objects = new ConcurrentHashMap<>();

                @Override
                public void putObject(
                    String bucketName,
                    String objectKey,
                    java.io.InputStream inputStream,
                    long sizeBytes,
                    String contentType
                ) {
                    try {
                        objects.put(bucketName + ":" + objectKey, new StoredObject(inputStream.readAllBytes(), contentType, sizeBytes));
                    }
                    catch (java.io.IOException exception) {
                        throw new IllegalStateException(exception);
                    }
                }

                @Override
                public StoredObject getObject(String bucketName, String objectKey) {
                    return objects.get(bucketName + ":" + objectKey);
                }

                @Override
                public URI createPresignedGetUrl(String bucketName, String objectKey, Duration ttl) {
                    return URI.create("http://example.test/" + bucketName + "/" + objectKey);
                }
            };
        }

        @Bean
        @Primary
        JobPublisher jobPublisher(AppProperties properties) {
            return new JobPublisher(null, properties) {
                @Override
                public void publish(ProcessJobMessage message) {
                    // Intentionally no-op for integration tests.
                }

                @Override
                public void publishPostAsr(PostAsrJobMessage message) {
                    // Intentionally no-op for integration tests.
                }
            };
        }
    }
}
