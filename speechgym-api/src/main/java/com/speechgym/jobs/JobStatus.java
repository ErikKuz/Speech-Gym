package com.speechgym.jobs;

public enum JobStatus {
    QUEUED,
    RUNNING_ASR,
    RUNNING_NLP,
    RUNNING_VOICE,
    RUNNING_REPORT,
    DONE,
    FAILED
}
