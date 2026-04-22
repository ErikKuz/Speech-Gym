package com.speechgym.uploads;

import java.io.IOException;
import java.util.List;
import java.util.UUID;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import com.speechgym.common.config.AppProperties;
import com.speechgym.common.error.ResourceNotFoundException;
import com.speechgym.sessions.SessionService;
import com.speechgym.storage.StorageService;
import com.speechgym.uploads.dto.UploadResponse;

@Service
public class UploadService {
    private static final Logger log = LoggerFactory.getLogger(UploadService.class);

    private final UploadRepository uploadRepository;
    private final SessionService sessionService;
    private final StorageService storageService;
    private final AppProperties properties;

    public UploadService(
        UploadRepository uploadRepository,
        SessionService sessionService,
        StorageService storageService,
        AppProperties properties
    ) {
        this.uploadRepository = uploadRepository;
        this.sessionService = sessionService;
        this.storageService = storageService;
        this.properties = properties;
    }

    @Transactional
    public UploadResponse upload(UUID userId, UUID sessionId, MultipartFile file) {
        sessionService.requireOwnedSession(userId, sessionId);
        UploadEntity upload = new UploadEntity();
        upload.setUserId(userId);
        upload.setSessionId(sessionId);
        upload.setStatus(UploadStatus.STORED);
        upload.setOriginalFilename(file.getOriginalFilename() == null ? "audio.bin" : file.getOriginalFilename());
        upload.setContentType(file.getContentType() == null ? "application/octet-stream" : file.getContentType());
        upload.setSizeBytes(file.getSize());
        upload.setBucketName(properties.storage().uploadsBucket());
        upload.setObjectKey(userId + "/" + sessionId + "/uploads/" + UUID.randomUUID() + "-" + upload.getOriginalFilename());
        try {
            storageService.putObject(
                upload.getBucketName(),
                upload.getObjectKey(),
                file.getInputStream(),
                file.getSize(),
                upload.getContentType()
            );
        }
        catch (IOException exception) {
            throw new IllegalStateException("Unable to read uploaded file.", exception);
        }
        upload = uploadRepository.save(upload);
        log.info("Stored upload uploadId={} sessionId={} userId={}", upload.getId(), sessionId, userId);
        return toResponse(upload);
    }

    @Transactional(readOnly = true)
    public List<UploadResponse> list(UUID userId, UUID sessionId) {
        sessionService.requireOwnedSession(userId, sessionId);
        return uploadRepository.findBySessionIdAndUserIdOrderByCreatedAtDesc(sessionId, userId).stream()
            .map(this::toResponse)
            .toList();
    }

    @Transactional(readOnly = true)
    public UploadEntity requireOwnedUpload(UUID userId, UUID sessionId, UUID uploadId) {
        return uploadRepository.findByIdAndSessionIdAndUserId(uploadId, sessionId, userId)
            .orElseThrow(() -> new ResourceNotFoundException("Upload was not found."));
    }

    @Transactional(readOnly = true)
    public UploadEntity getUploadForWorker(UUID uploadId) {
        return uploadRepository.findById(uploadId)
            .orElseThrow(() -> new ResourceNotFoundException("Upload was not found."));
    }

    private UploadResponse toResponse(UploadEntity upload) {
        return new UploadResponse(
            upload.getId(),
            upload.getStatus().name(),
            upload.getOriginalFilename(),
            upload.getContentType(),
            upload.getSizeBytes(),
            upload.getCreatedAt()
        );
    }
}
