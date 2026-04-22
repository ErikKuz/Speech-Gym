package com.speechgym.artifacts;

import java.io.ByteArrayInputStream;
import java.time.Instant;
import java.util.Map;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.speechgym.common.config.AppProperties;
import com.speechgym.jobs.JobEntity;
import com.speechgym.storage.StorageService;

@Service
public class ArtifactService {
    private final ArtifactRepository artifactRepository;
    private final StorageService storageService;
    private final AppProperties properties;

    public ArtifactService(
        ArtifactRepository artifactRepository,
        StorageService storageService,
        AppProperties properties
    ) {
        this.artifactRepository = artifactRepository;
        this.storageService = storageService;
        this.properties = properties;
    }

    @Transactional
    public ArtifactEntity storeArtifact(
        JobEntity job,
        ArtifactType type,
        String contentType,
        byte[] bytes,
        Map<String, Object> metadata
    ) {
        String objectKey = job.getUserId() + "/" + job.getSessionId() + "/" + job.getId() + "/" + type.name().toLowerCase();
        storageService.putObject(
            properties.storage().artifactsBucket(),
            objectKey,
            new ByteArrayInputStream(bytes),
            bytes.length,
            contentType
        );
        ArtifactEntity artifact = artifactRepository.findByJobIdAndType(job.getId(), type)
            .orElseGet(ArtifactEntity::new);
        artifact.setJobId(job.getId());
        artifact.setUserId(job.getUserId());
        artifact.setSessionId(job.getSessionId());
        artifact.setType(type);
        artifact.setBucketName(properties.storage().artifactsBucket());
        artifact.setObjectKey(objectKey);
        artifact.setContentType(contentType);
        artifact.setSizeBytes(bytes.length);
        artifact.setMetadataJson(metadata);
        artifact.setCreatedAt(Instant.now());
        return artifactRepository.save(artifact);
    }
}
