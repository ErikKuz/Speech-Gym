package com.speechgym.asr;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

import com.speechgym.common.config.AppProperties;

@Configuration
public class AsrConfig {
    @Bean
    RestClient asrRestClient(RestClient.Builder builder, AppProperties properties) {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout((int) properties.asr().connectTimeout().toMillis());
        requestFactory.setReadTimeout((int) properties.asr().readTimeout().toMillis());
        return builder
            .baseUrl(properties.asr().baseUrl())
            .requestFactory(requestFactory)
            .build();
    }
}
