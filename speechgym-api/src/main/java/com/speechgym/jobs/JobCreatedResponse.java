package com.speechgym.jobs;

import java.time.Instant;
import java.util.UUID;

public record JobCreatedResponse(
    UUID jobId, // id нашего job-а
    String status, // Статус готовности job-а
    String statusUrl, // Адрес для проверки статуса job-а
    Instant receivedAt // Время создания job-а
) {}
