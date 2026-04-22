package com.speechgym.storage;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.URI;
import java.time.Duration;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import com.speechgym.common.error.UnprocessableEntityException;

import io.minio.GetObjectArgs;
import io.minio.GetPresignedObjectUrlArgs;
import io.minio.MinioClient;
import io.minio.PutObjectArgs;
import io.minio.http.Method;

@Service
public class MinioStorageService implements StorageService {
    private static final Logger log = LoggerFactory.getLogger(MinioStorageService.class);

    private final MinioClient minioClient;

    public MinioStorageService(MinioClient minioClient) {
        this.minioClient = minioClient;
    }

    @Override
    public void putObject(String bucketName, String objectKey, InputStream inputStream, long sizeBytes, String contentType) {
        try {
            minioClient.putObject(
                PutObjectArgs.builder()
                    .bucket(bucketName)
                    .object(objectKey)
                    .stream(inputStream, sizeBytes, -1)
                    .contentType(contentType)
                    .build()
            );
            log.debug("Stored object bucket={} key={}", bucketName, objectKey);
        }
        catch (Exception exception) {
            throw new UnprocessableEntityException("Unable to store object in MinIO.");
        }
    }

    @Override
    public StoredObject getObject(String bucketName, String objectKey) {
        try (InputStream inputStream = minioClient.getObject(
            GetObjectArgs.builder().bucket(bucketName).object(objectKey).build()
        )) {
            ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
            inputStream.transferTo(outputStream);
            return new StoredObject(outputStream.toByteArray(), "application/octet-stream", outputStream.size());
        }
        catch (Exception exception) {
            throw new UnprocessableEntityException("Unable to read object from MinIO.");
        }
    }

    @Override
    public URI createPresignedGetUrl(String bucketName, String objectKey, Duration ttl) {
        try {
            return URI.create(minioClient.getPresignedObjectUrl(
                GetPresignedObjectUrlArgs.builder()
                    .method(Method.GET)
                    .bucket(bucketName)
                    .object(objectKey)
                    .expiry((int) ttl.getSeconds())
                    .build()
            ));
        }
        catch (Exception exception) {
            throw new UnprocessableEntityException("Unable to generate a presigned URL.");
        }
    }
}
