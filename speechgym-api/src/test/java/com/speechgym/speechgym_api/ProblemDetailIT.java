package com.speechgym.speechgym_api;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;

class ProblemDetailIT extends AbstractIntegrationTest {
    @Test
    void validationErrorsUseProblemDetailShape() throws Exception {
        String token = registerAndLogin("problem@example.com");

        mockMvc.perform(post("/api/v1/sessions")
                .header("Authorization", "Bearer " + token)
                .header("Idempotency-Key", "22222222-2222-2222-2222-222222222222")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                      "title":"",
                      "goal":"Practice",
                      "scenario":"",
                      "languageCode":"en",
                      "audienceType":"team",
                      "durationTargetSeconds":5,
                      "presentationStyle":"confident",
                      "notes":"n/a",
                      "difficultyLevel":"MEDIUM",
                      "coachingMode":"BALANCED"
                    }
                    """))
            .andExpect(status().isBadRequest())
            .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_PROBLEM_JSON))
            .andExpect(jsonPath("$.status").value(400))
            .andExpect(jsonPath("$.fieldErrors").isArray())
            .andExpect(jsonPath("$.fieldErrors.length()").value(org.hamcrest.Matchers.greaterThanOrEqualTo(2)));
    }
}
