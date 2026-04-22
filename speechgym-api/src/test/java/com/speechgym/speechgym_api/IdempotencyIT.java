package com.speechgym.speechgym_api;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;

class IdempotencyIT extends AbstractIntegrationTest {
    @Test
    void sameKeySameBodyReturnsStoredResponseAndDifferentBodyReturnsConflict() throws Exception {
        String token = registerAndLogin("idempotency@example.com");
        String key = "11111111-1111-1111-1111-111111111111";

        String response = mockMvc.perform(post("/api/v1/sessions")
                .header("Authorization", "Bearer " + token)
                .header("Idempotency-Key", key)
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                      "title":"Session One",
                      "goal":"Practice",
                      "scenario":"KEYNOTE",
                      "languageCode":"en",
                      "audienceType":"team",
                      "durationTargetSeconds":300,
                      "presentationStyle":"confident",
                      "notes":"n/a",
                      "difficultyLevel":"MEDIUM",
                      "coachingMode":"BALANCED"
                    }
                    """))
            .andExpect(status().isCreated())
            .andReturn()
            .getResponse()
            .getContentAsString();

        String sessionId = com.jayway.jsonpath.JsonPath.read(response, "$.sessionId");

        mockMvc.perform(post("/api/v1/sessions")
                .header("Authorization", "Bearer " + token)
                .header("Idempotency-Key", key)
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                      "title":"Session One",
                      "goal":"Practice",
                      "scenario":"KEYNOTE",
                      "languageCode":"en",
                      "audienceType":"team",
                      "durationTargetSeconds":300,
                      "presentationStyle":"confident",
                      "notes":"n/a",
                      "difficultyLevel":"MEDIUM",
                      "coachingMode":"BALANCED"
                    }
                    """))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.sessionId").value(sessionId));

        mockMvc.perform(post("/api/v1/sessions")
                .header("Authorization", "Bearer " + token)
                .header("Idempotency-Key", key)
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                      "title":"Session Two",
                      "goal":"Different",
                      "scenario":"KEYNOTE",
                      "languageCode":"en",
                      "audienceType":"team",
                      "durationTargetSeconds":300,
                      "presentationStyle":"confident",
                      "notes":"n/a",
                      "difficultyLevel":"MEDIUM",
                      "coachingMode":"BALANCED"
                    }
                    """))
            .andExpect(status().isConflict());
    }
}
