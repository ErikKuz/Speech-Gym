package com.speechgym.speechgym_api;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.http.MediaType;

class AuthIT extends AbstractIntegrationTest {
    @Test
    void registerLoginRefreshAndMeFlowWorks() throws Exception {
        String registerResponse = mockMvc.perform(post("/api/v1/auth/register")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                      "email":"auth@example.com",
                      "password":"Password123",
                      "fullName":"Auth User"
                    }
                    """))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.accessToken").exists())
            .andExpect(jsonPath("$.refreshToken").exists())
            .andReturn()
            .getResponse()
            .getContentAsString();

        String accessToken = com.jayway.jsonpath.JsonPath.read(registerResponse, "$.accessToken");
        String refreshToken = com.jayway.jsonpath.JsonPath.read(registerResponse, "$.refreshToken");

        mockMvc.perform(post("/api/v1/auth/login")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                      "email":"auth@example.com",
                      "password":"Password123"
                    }
                    """))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.email").value("auth@example.com"));

        mockMvc.perform(post("/api/v1/auth/refresh")
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {
                      "refreshToken":"%s"
                    }
                    """.formatted(refreshToken)))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.accessToken").exists());

        mockMvc.perform(get("/api/v1/me").header("Authorization", "Bearer " + accessToken))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.email").value("auth@example.com"))
            .andExpect(jsonPath("$.subscriptionPlan").value("FREE"))
            .andExpect(jsonPath("$.subscriptionActive").value(true));
    }
}
