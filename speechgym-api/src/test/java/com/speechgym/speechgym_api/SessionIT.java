package com.speechgym.speechgym_api;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;

class SessionIT extends AbstractIntegrationTest {
    @Test
    void createListAndOwnershipRulesWork() throws Exception {
        String userOneToken = registerAndLogin("one@example.com");
        String userTwoToken = registerAndLogin("two@example.com");

        String userOneSessionId = createSession(userOneToken, "Investor Pitch");
        createSession(userTwoToken, "Other Session");

        mockMvc.perform(get("/api/v1/sessions")
                .header("Authorization", "Bearer " + userOneToken))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.items.length()").value(1))
            .andExpect(jsonPath("$.items[0].sessionId").value(userOneSessionId));

        mockMvc.perform(get("/api/v1/sessions/{sessionId}", userOneSessionId)
                .header("Authorization", "Bearer " + userTwoToken))
            .andExpect(status().isNotFound());
    }
}
