package com.speechgym.storage;

import java.io.InputStream;
import java.net.URI;
import java.time.Duration;

public interface StorageService {
    void putObject(String bucketName, String objectKey, InputStream inputStream, long sizeBytes, String contentType);

    StoredObject getObject(String bucketName, String objectKey);

    URI createPresignedGetUrl(String bucketName, String objectKey, Duration ttl);
}
