package com.speechgym.storage;

public record StoredObject(
    byte[] content,
    String contentType,
    long sizeBytes
) {
}
