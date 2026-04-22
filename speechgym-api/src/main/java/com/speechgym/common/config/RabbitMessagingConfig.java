package com.speechgym.common.config;

import org.springframework.amqp.core.Binding;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.DirectExchange;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.core.QueueBuilder;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMessagingConfig {
    @Bean
    DirectExchange speechgymJobsExchange(AppProperties properties) { 
        return new DirectExchange(properties.rabbit().exchange(), true, false);
    }

    @Bean
    Queue speechgymJobsQueue(AppProperties properties) {
        return QueueBuilder.durable(properties.rabbit().queue()).build();
    }

    @Bean
    Binding speechgymJobsBinding(
        Queue speechgymJobsQueue,
        DirectExchange speechgymJobsExchange,
        AppProperties properties
    ) {
        return BindingBuilder.bind(speechgymJobsQueue)
            .to(speechgymJobsExchange)
            .with(properties.rabbit().routingKey());
    }

    @Bean
    Jackson2JsonMessageConverter jackson2JsonMessageConverter() {
        return new Jackson2JsonMessageConverter();
    }
}
