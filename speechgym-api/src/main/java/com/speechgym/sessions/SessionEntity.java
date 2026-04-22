package com.speechgym.sessions;

import java.util.UUID;

import org.hibernate.annotations.UuidGenerator;

import com.speechgym.common.persistence.AbstractAuditableEntity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "sessions")
public class SessionEntity extends AbstractAuditableEntity {
    @Id
    @GeneratedValue
    @UuidGenerator
    private UUID id;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(nullable = false, length = 200)
    private String title;

    @Column(length = 400)
    private String goal;

    @Column(nullable = false, length = 100)
    private String scenario;

    @Column(name = "language_code", nullable = false, length = 16)
    private String languageCode;

    @Column(name = "audience_type", nullable = false, length = 100)
    private String audienceType;

    @Column(name = "duration_target_seconds", nullable = false)
    private int durationTargetSeconds;

    @Column(name = "presentation_style", nullable = false, length = 100)
    private String presentationStyle;

    @Column(length = 2000)
    private String notes;

    @Column(name = "difficulty_level", nullable = false, length = 32)
    private String difficultyLevel;

    @Column(name = "coaching_mode", nullable = false, length = 32)
    private String coachingMode;

    public UUID getId() {
        return id;
    }

    public UUID getUserId() {
        return userId;
    }

    public void setUserId(UUID userId) {
        this.userId = userId;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getGoal() {
        return goal;
    }

    public void setGoal(String goal) {
        this.goal = goal;
    }

    public String getScenario() {
        return scenario;
    }

    public void setScenario(String scenario) {
        this.scenario = scenario;
    }

    public String getLanguageCode() {
        return languageCode;
    }

    public void setLanguageCode(String languageCode) {
        this.languageCode = languageCode;
    }

    public String getAudienceType() {
        return audienceType;
    }

    public void setAudienceType(String audienceType) {
        this.audienceType = audienceType;
    }

    public int getDurationTargetSeconds() {
        return durationTargetSeconds;
    }

    public void setDurationTargetSeconds(int durationTargetSeconds) {
        this.durationTargetSeconds = durationTargetSeconds;
    }

    public String getPresentationStyle() {
        return presentationStyle;
    }

    public void setPresentationStyle(String presentationStyle) {
        this.presentationStyle = presentationStyle;
    }

    public String getNotes() {
        return notes;
    }

    public void setNotes(String notes) {
        this.notes = notes;
    }

    public String getDifficultyLevel() {
        return difficultyLevel;
    }

    public void setDifficultyLevel(String difficultyLevel) {
        this.difficultyLevel = difficultyLevel;
    }

    public String getCoachingMode() {
        return coachingMode;
    }

    public void setCoachingMode(String coachingMode) {
        this.coachingMode = coachingMode;
    }
}