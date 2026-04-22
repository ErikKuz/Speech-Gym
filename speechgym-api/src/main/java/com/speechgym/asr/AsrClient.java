package com.speechgym.asr;

public interface AsrClient {
    AsrTranscription transcribe(String filename, String contentType, byte[] audioBytes);
}
