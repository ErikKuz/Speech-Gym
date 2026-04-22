package com.speechgym.jobs;

import java.util.UUID;

import org.springframework.context.annotation.Profile;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.speechgym.common.security.CurrentUserService;
import com.speechgym.jobs.dto.JobStatusResponse;

@Profile("local")
@RestController
@RequestMapping("/api/v1/dev/jobs")
public class DevJobController {
    private final JobService jobService;
    private final CurrentUserService currentUserService;

    public DevJobController(JobService jobService, CurrentUserService currentUserService) {
        this.jobService = jobService;
        this.currentUserService = currentUserService;
    }

    @PostMapping("/{jobId}/requeue")
    public JobStatusResponse requeue(@PathVariable UUID jobId) {
        return jobService.requeue(currentUserService.requireUserId(), jobId);
    }
}
