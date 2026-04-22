package com.speechgym;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication(scanBasePackages = "com.speechgym")
@ConfigurationPropertiesScan
public class SpeechgymApiApplication {

	public static void main(String[] args) {
		SpringApplication.run(SpeechgymApiApplication.class, args);
	}

}
