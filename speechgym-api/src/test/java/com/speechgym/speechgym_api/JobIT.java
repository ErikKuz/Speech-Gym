package com.speechgym.speechgym_api;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.UUID;

import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;

class JobIT extends AbstractIntegrationTest {
    @Test
    void createJobReturns202PollsAndHidesForeignObjects() throws Exception {
        String ownerToken = registerAndLogin("job-owner@example.com");
        String otherToken = registerAndLogin("job-other@example.com");
        String sessionId = createSession(ownerToken, "Job Session");
        String uploadId = createUpload(ownerToken, sessionId);

        String jobResponse = mockMvc.perform(post("/api/v1/sessions/{sessionId}/jobs", sessionId)
                .header("Authorization", "Bearer " + ownerToken)
                .header("Idempotency-Key", UUID.randomUUID().toString())
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                      "uploadId":"%s",
                      "options":{"generatePdf":true}
                    }
                    """.formatted(uploadId)))
            .andExpect(status().isAccepted())
            .andExpect(header().string("Location", org.hamcrest.Matchers.containsString("/api/v1/jobs/")))
            .andExpect(header().string("Retry-After", "2"))
            .andExpect(jsonPath("$.status").value("QUEUED"))
            .andReturn()
            .getResponse()
            .getContentAsString();

        String jobId = com.jayway.jsonpath.JsonPath.read(jobResponse, "$.jobId");

        mockMvc.perform(get("/api/v1/jobs/{jobId}", jobId)
                .header("Authorization", "Bearer " + ownerToken))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("QUEUED"))
            .andExpect(jsonPath("$.progress").value(0));

        mockMvc.perform(get("/api/v1/jobs/{jobId}", jobId)
                .header("Authorization", "Bearer " + otherToken))
            .andExpect(status().isNotFound());
    }
}
