package com.speechgym.common.persistence;

import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.MappedSuperclass;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;

@MappedSuperclass
public abstract class AbstractAuditableEntity { // Класс для контроля под-классов Entity, а именно времени создания и обновления сущностей (поля createdAt и updatedAt)
    @Column(name = "created_at", nullable = false) 
    private Instant createdAt;  

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    @PrePersist
    protected void onCreate() { // Метод который выполниться как только сущность будет впервые добавлена в БД 
        Instant now = Instant.now();
        createdAt = now;
        updatedAt = now;
    }

    @PreUpdate
    protected void onUpdate() { // Метод который будет выполняться как тольео сущность будет обновлена
        updatedAt = Instant.now();
    }

    public Instant getCreatedAt() {
        return createdAt; 
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }

    public void setCreatedAt(Instant createdAt) {
        this.createdAt = createdAt;
    }

    public void setUpdatedAt(Instant updatedAt) {
        this.updatedAt = updatedAt;
    }
}
