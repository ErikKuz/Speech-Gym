package com.speechgym.speechgym_api;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;

class UploadIT extends AbstractIntegrationTest {
    @Test
    void uploadsAreListedPerSessionAndOwnershipRulesWork() throws Exception {
        String userOneToken = registerAndLogin("upload-one@example.com");
        String userTwoToken = registerAndLogin("upload-two@example.com");
        String sessionId = createSession(userOneToken, "Upload Session");

        String firstUploadId = createUpload(userOneToken, sessionId);
        String secondUploadId = createUpload(userOneToken, sessionId);

        mockMvc.perform(get("/api/v1/sessions/{sessionId}/uploads", sessionId)
                .header("Authorization", "Bearer " + userOneToken))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.length()").value(2))
            .andExpect(jsonPath("$[0].uploadId").value(secondUploadId))
            .andExpect(jsonPath("$[1].uploadId").value(firstUploadId));

        mockMvc.perform(get("/api/v1/sessions/{sessionId}/uploads", sessionId)
                .header("Authorization", "Bearer " + userTwoToken))
            .andExpect(status().isNotFound());
    }
}
