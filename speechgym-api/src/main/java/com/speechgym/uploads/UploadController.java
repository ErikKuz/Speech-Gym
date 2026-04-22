package com.speechgym.uploads;

import java.util.List;
import java.util.UUID;

import org.springframework.http.MediaType;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.speechgym.common.security.CurrentUserService;
import com.speechgym.uploads.dto.UploadResponse;

import jakarta.validation.constraints.NotNull;

@RestController
@Validated
@RequestMapping("/api/v1/sessions/{sessionId}/uploads")
public class UploadController {
    private final UploadService uploadService;
    private final CurrentUserService currentUserService;

    public UploadController(UploadService uploadService, CurrentUserService currentUserService) {
        this.uploadService = uploadService;
        this.currentUserService = currentUserService;
    }

    @PostMapping(consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public UploadResponse upload(@PathVariable UUID sessionId, @RequestParam("file") @NotNull MultipartFile file) {
        return uploadService.upload(currentUserService.requireUserId(), sessionId, file);
    }

    @GetMapping
    public List<UploadResponse> list(@PathVariable UUID sessionId) {
        return uploadService.list(currentUserService.requireUserId(), sessionId);
    }
}
