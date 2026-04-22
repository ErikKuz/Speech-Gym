package com.speechgym.reports;

import java.time.Instant;
import java.util.List;
import java.util.UUID;

import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.annotations.UuidGenerator;
import org.hibernate.type.SqlTypes;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "reports")
public class ReportEntity {
    @Id
    @GeneratedValue
    @UuidGenerator
    private UUID id;

    @Column(name = "job_id", nullable = false, unique = true)
    private UUID jobId;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(name = "session_id", nullable = false)
    private UUID sessionId;

    @Column(name = "pdf_artifact_id", nullable = false, unique = true)
    private UUID pdfArtifactId;

    @Column(name = "overall_score", nullable = false)
    private int overallScore;

    @Column(nullable = false)
    private int clarity;

    @Column(name = "pace_wpm", nullable = false)
    private int paceWpm;

    @Column(name = "filler_words_count", nullable = false)
    private int fillerWordsCount;

    @Column(nullable = false)
    private int confidence;

    @Column(name = "structure_score", nullable = false)
    private int structureScore;

    @Column(name = "emotional_tone", nullable = false, length = 64)
    private String emotionalTone;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(nullable = false)
    private List<String> strengths;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(nullable = false)
    private List<String> improvements;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(nullable = false)
    private List<String> recommendations;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt = Instant.now();

    public UUID getId() {
        return id;
    }

    public UUID getJobId() {
        return jobId;
    }

    public void setJobId(UUID jobId) {
        this.jobId = jobId;
    }

    public UUID getUserId() {
        return userId;
    }

    public void setUserId(UUID userId) {
        this.userId = userId;
    }

    public UUID getSessionId() {
        return sessionId;
    }

    public void setSessionId(UUID sessionId) {
        this.sessionId = sessionId;
    }

    public UUID getPdfArtifactId() {
        return pdfArtifactId;
    }

    public void setPdfArtifactId(UUID pdfArtifactId) {
        this.pdfArtifactId = pdfArtifactId;
    }

    public int getOverallScore() {
        return overallScore;
    }

    public void setOverallScore(int overallScore) {
        this.overallScore = overallScore;
    }

    public int getClarity() {
        return clarity;
    }

    public void setClarity(int clarity) {
        this.clarity = clarity;
    }

    public int getPaceWpm() {
        return paceWpm;
    }

    public void setPaceWpm(int paceWpm) {
        this.paceWpm = paceWpm;
    }

    public int getFillerWordsCount() {
        return fillerWordsCount;
    }

    public void setFillerWordsCount(int fillerWordsCount) {
        this.fillerWordsCount = fillerWordsCount;
    }

    public int getConfidence() {
        return confidence;
    }

    public void setConfidence(int confidence) {
        this.confidence = confidence;
    }

    public int getStructureScore() {
        return structureScore;
    }

    public void setStructureScore(int structureScore) {
        this.structureScore = structureScore;
    }

    public String getEmotionalTone() {
        return emotionalTone;
    }

    public void setEmotionalTone(String emotionalTone) {
        this.emotionalTone = emotionalTone;
    }

    public List<String> getStrengths() {
        return strengths;
    }

    public void setStrengths(List<String> strengths) {
        this.strengths = strengths;
    }

    public List<String> getImprovements() {
        return improvements;
    }

    public void setImprovements(List<String> improvements) {
        this.improvements = improvements;
    }

    public List<String> getRecommendations() {
        return recommendations;
    }

    public void setRecommendations(List<String> recommendations) {
        this.recommendations = recommendations;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(Instant createdAt) {
        this.createdAt = createdAt;
    }
}
