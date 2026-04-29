package com.speechgym.reports;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

import com.speechgym.common.config.AppProperties;

@Configuration
public class ReportConfig {
    @Bean
    RestClient reportRestClient(RestClient.Builder builder, AppProperties properties) {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        requestFactory.setConnectTimeout((int) properties.report().connectTimeout().toMillis());
        requestFactory.setReadTimeout((int) properties.report().readTimeout().toMillis());
        return builder
            .baseUrl(properties.report().baseUrl())
            .requestFactory(requestFactory)
            .build();
    }
}
