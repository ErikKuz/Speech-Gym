package com.speechgym.sessions;

import java.util.UUID;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.speechgym.common.error.ResourceNotFoundException;
import com.speechgym.common.idempotency.IdempotencyService;
import com.speechgym.common.idempotency.StoredResponse;
import com.speechgym.sessions.dto.CreateSessionRequest;
import com.speechgym.sessions.dto.SessionListResponse;
import com.speechgym.sessions.dto.SessionResponse;
import com.speechgym.sessions.dto.SessionSummaryResponse;
import com.speechgym.sessions.dto.UpdateSessionRequest;

@Service
public class SessionService {
    private static final Logger log = LoggerFactory.getLogger(SessionService.class);

    private final SessionRepository sessionRepository;
    private final IdempotencyService idempotencyService;

    public SessionService(SessionRepository sessionRepository, IdempotencyService idempotencyService) {
        this.sessionRepository = sessionRepository;
        this.idempotencyService = idempotencyService;
    }

    @Transactional
    public StoredResponse<SessionResponse> createSession(UUID userId, String idempotencyKey, CreateSessionRequest request) {
        String requestHash = idempotencyService.hashPayload(request);
        return idempotencyService.restoreResponse(userId, idempotencyKey, requestHash, SessionResponse.class)
            .orElseGet(() -> createAndStore(userId, idempotencyKey, requestHash, request));
    }

    @Transactional(readOnly = true)
    public SessionListResponse list(UUID userId, String query, int page, int size) {
        String normalizedQuery = normalizeQuery(query);
        PageRequest pageRequest = PageRequest.of(page, size);
        Page<SessionEntity> sessions = normalizedQuery == null
            ? sessionRepository.findByUserIdOrderByUpdatedAtDesc(userId, pageRequest)
            : sessionRepository.searchByUserId(userId, normalizedQuery, pageRequest);
        return new SessionListResponse(
            sessions.getContent().stream().map(this::toSummary).toList(),
            sessions.getNumber(),
            sessions.getSize(),
            sessions.getTotalElements(),
            sessions.getTotalPages()
        );
    }

    @Transactional(readOnly = true)
    public SessionResponse get(UUID userId, UUID sessionId) {
        return toResponse(requireOwnedSession(userId, sessionId));
    }

    @Transactional
    public SessionResponse update(UUID userId, UUID sessionId, UpdateSessionRequest request) {
        SessionEntity session = requireOwnedSession(userId, sessionId);
        apply(session, request);
        return toResponse(session);
    }

    @Transactional(readOnly = true)
    public SessionEntity requireOwnedSession(UUID userId, UUID sessionId) {
        return sessionRepository.findByIdAndUserId(sessionId, userId)
            .orElseThrow(() -> new ResourceNotFoundException("Session was not found."));
    }

    private StoredResponse<SessionResponse> createAndStore(
        UUID userId,
        String idempotencyKey,
        String requestHash,
        CreateSessionRequest request
    ) {
        SessionEntity session = new SessionEntity();
        session.setUserId(userId);
        apply(session, request);
        session = sessionRepository.save(session);
        log.info("Created session sessionId={} userId={}", session.getId(), userId);

        StoredResponse<SessionResponse> response = new StoredResponse<>(
            201,
            "/api/v1/sessions/" + session.getId(),
            null,
            toResponse(session)
        );
        idempotencyService.saveResponse(userId, idempotencyKey, requestHash, response);
        return response;
    }

    private void apply(SessionEntity session, CreateSessionRequest request) {
        session.setTitle(request.title());
        session.setGoal(request.goal());
        session.setScenario(request.scenario());
        session.setLanguageCode(request.languageCode());
        session.setAudienceType(request.audienceType());
        session.setDurationTargetSeconds(request.durationTargetSeconds());
        session.setPresentationStyle(request.presentationStyle());
        session.setNotes(request.notes());
        session.setDifficultyLevel(request.difficultyLevel());
        session.setCoachingMode(request.coachingMode());
    }

    private void apply(SessionEntity session, UpdateSessionRequest request) {
        session.setTitle(request.title());
        session.setGoal(request.goal());
        session.setScenario(request.scenario());
        session.setLanguageCode(request.languageCode());
        session.setAudienceType(request.audienceType());
        session.setDurationTargetSeconds(request.durationTargetSeconds());
        session.setPresentationStyle(request.presentationStyle());
        session.setNotes(request.notes());
        session.setDifficultyLevel(request.difficultyLevel());
        session.setCoachingMode(request.coachingMode());
    }

    private SessionSummaryResponse toSummary(SessionEntity session) {
        return new SessionSummaryResponse(
            session.getId(),
            session.getTitle(),
            session.getGoal(),
            session.getUpdatedAt()
        );
    }

    private SessionResponse toResponse(SessionEntity session) {
        return new SessionResponse(
            session.getId(),
            session.getTitle(),
            session.getGoal(),
            session.getScenario(),
            session.getLanguageCode(),
            session.getAudienceType(),
            session.getDurationTargetSeconds(),
            session.getPresentationStyle(),
            session.getNotes(),
            session.getDifficultyLevel(),
            session.getCoachingMode(),
            session.getCreatedAt(),
            session.getUpdatedAt()
        );
    }

    private String normalizeQuery(String query) {
        if (query == null) {
            return null;
        }
        String normalized = query.trim();
        return normalized.isEmpty() ? null : normalized;
    }
}
