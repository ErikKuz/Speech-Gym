package com.speechgym.common.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import io.minio.MinioClient;

@Configuration
public class MinioConfig {
    @Bean
    MinioClient minioClient(AppProperties properties) {
        return MinioClient.builder()
            .endpoint(properties.storage().minio().endpoint())
            .credentials(
                properties.storage().minio().accessKey(),
                properties.storage().minio().secretKey()
            )
            .build();
    }
}
