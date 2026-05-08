package com.speechgym.jobs;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Service;

import com.speechgym.common.config.AppProperties;

@Service
public class JobPublisher {
    private static final Logger log = LoggerFactory.getLogger(JobPublisher.class);

    private final RabbitTemplate rabbitTemplate;
    private final AppProperties properties;

    public JobPublisher(RabbitTemplate rabbitTemplate, AppProperties properties) {
        this.rabbitTemplate = rabbitTemplate;
        this.properties = properties;
    }

    public void publish(ProcessJobMessage message) {
        log.debug("Publishing job payload={}", message);
        rabbitTemplate.convertAndSend(properties.rabbit().exchange(), properties.rabbit().routingKey(), message);
    }

    public void publishPostAsr(PostAsrJobMessage message) {
        log.debug("Publishing post-ASR job payload={}", message);
        rabbitTemplate.convertAndSend(properties.rabbit().exchange(), properties.rabbit().postAsrRoutingKey(), message);
    }
}
