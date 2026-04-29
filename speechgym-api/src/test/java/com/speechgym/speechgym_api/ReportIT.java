package com.speechgym.speechgym_api;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.UUID;

import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;

import com.jayway.jsonpath.JsonPath;
import com.speechgym.artifacts.ArtifactEntity;
import com.speechgym.artifacts.ArtifactType;
import com.speechgym.reports.ReportEntity;
import com.speechgym.sessions.SessionEntity;

class ReportIT extends AbstractIntegrationTest {
    @Test
    void reportsAreListedPerSessionAndRespectOwnership() throws Exception {
        String ownerToken = registerAndLogin("report-owner@example.com");
        String otherToken = registerAndLogin("report-other@example.com");
        String sessionId = createSession(ownerToken, "Report Session");
        String uploadId = createUpload(ownerToken, sessionId);

        String jobResponse = mockMvc.perform(post("/api/v1/sessions/{sessionId}/jobs", sessionId)
                .header("Authorization", "Bearer " + ownerToken)
                .header("Idempotency-Key", UUID.randomUUID().toString())
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                      "uploadId":"%s",
                      "options":{"reportFormat":"FULL"}
                    }
                    """.formatted(uploadId)))
            .andExpect(status().isAccepted())
            .andReturn()
            .getResponse()
            .getContentAsString();

        String jobId = JsonPath.read(jobResponse, "$.jobId");
        SessionEntity session = sessionRepository.findById(UUID.fromString(sessionId)).orElseThrow();

        ArtifactEntity artifact = new ArtifactEntity();
        artifact.setJobId(UUID.fromString(jobId));
        artifact.setUserId(session.getUserId());
        artifact.setSessionId(session.getId());
        artifact.setType(ArtifactType.REPORT_PDF);
        artifact.setBucketName("speechgym-artifacts");
        artifact.setObjectKey("reports/" + jobId + ".pdf");
        artifact.setContentType("application/pdf");
        artifact.setSizeBytes(128);
        artifact.setMetadataJson(Map.of("source", "test"));
        artifact = artifactRepository.save(artifact);

        String analysisObjectKey = "analysis/" + jobId + ".json";
        String analysisJson = """
            {
              "report": {
                "passport_pitch": {
                  "strengths": ["Clear opening"],
                  "blockers": ["Tighter close"],
                  "next_version_changes": ["Lead with traction"]
                },
                "next_pitch": {
                  "title": "Следующая версия pitch",
                  "blocks": [
                    {
                      "label": "Вступление",
                      "text": "Новый заход"
                    }
                  ],
                  "full_text": "Новый полный текст"
                },
                "recommendations": {
                  "summary": ["Собрать более сильное начало"],
                  "changes": [
                    {
                      "title": "Начало",
                      "before": "Старый текст",
                      "after": "Новый текст",
                      "why_before_weaker": "Слабый старт",
                      "why_after_better": "Более четко",
                      "audience_effect": {
                        "understands_better": "Понятнее",
                        "feels_more": "Больше доверия"
                      }
                    }
                  ]
                }
              },
              "meta": {
                "pitch_type": "investor_pitch",
                "language": "ru",
                "target_duration_sec": 300,
                "actual_duration_sec": 288.24,
                "actual_duration": "4:48",
                "model": "GigaChat-Max"
              }
            }
            """;
        ArtifactEntity nlpArtifact = new ArtifactEntity();
        nlpArtifact.setJobId(UUID.fromString(jobId));
        nlpArtifact.setUserId(session.getUserId());
        nlpArtifact.setSessionId(session.getId());
        nlpArtifact.setType(ArtifactType.NLP_ANALYSIS_JSON);
        nlpArtifact.setBucketName("speechgym-artifacts");
        nlpArtifact.setObjectKey(analysisObjectKey);
        nlpArtifact.setContentType("application/json");
        nlpArtifact.setSizeBytes(analysisJson.getBytes(StandardCharsets.UTF_8).length);
        nlpArtifact.setMetadataJson(Map.of("source", "test"));
        artifactRepository.save(nlpArtifact);
        storageService.putObject(
            "speechgym-artifacts",
            analysisObjectKey,
            new ByteArrayInputStream(analysisJson.getBytes(StandardCharsets.UTF_8)),
            analysisJson.getBytes(StandardCharsets.UTF_8).length,
            "application/json"
        );

        ReportEntity report = new ReportEntity();
        report.setJobId(UUID.fromString(jobId));
        report.setUserId(session.getUserId());
        report.setSessionId(session.getId());
        report.setPdfArtifactId(artifact.getId());
        report.setOverallScore(88);
        report.setClarity(84);
        report.setPaceWpm(136);
        report.setFillerWordsCount(4);
        report.setConfidence(86);
        report.setStructureScore(82);
        report.setEmotionalTone("confident");
        report.setStrengths(List.of("Clear opening"));
        report.setImprovements(List.of("Tighter close"));
        report.setRecommendations(List.of("Pause before key points"));
        report = reportRepository.save(report);

        mockMvc.perform(get("/api/v1/sessions/{sessionId}/reports", sessionId)
                .header("Authorization", "Bearer " + ownerToken))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.length()").value(1))
            .andExpect(jsonPath("$[0].reportId").value(report.getId().toString()))
            .andExpect(jsonPath("$[0].jobId").value(jobId))
            .andExpect(jsonPath("$[0].sessionId").value(sessionId));

        mockMvc.perform(get("/api/v1/sessions/{sessionId}/reports", sessionId)
                .header("Authorization", "Bearer " + otherToken))
            .andExpect(status().isNotFound());

        mockMvc.perform(get("/api/v1/reports/{reportId}", report.getId())
                .header("Authorization", "Bearer " + ownerToken))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.nextVersionChanges[0]").value("Lead with traction"))
            .andExpect(jsonPath("$.nextVersion.title").value("Следующая версия pitch"))
            .andExpect(jsonPath("$.nextVersion.blocks[0].label").value("Вступление"))
            .andExpect(jsonPath("$.recommendationsSummary[0]").value("Собрать более сильное начало"))
            .andExpect(jsonPath("$.recommendationDetails[0].title").value("Начало"))
            .andExpect(jsonPath("$.recommendationDetails[0].whyBeforeWeaker").value("Слабый старт"))
            .andExpect(jsonPath("$.recommendationDetails[0].audienceEffect.understandsBetter").value("Понятнее"))
            .andExpect(jsonPath("$.analysisMeta.actualDuration").value("4:48"));
    }
}
