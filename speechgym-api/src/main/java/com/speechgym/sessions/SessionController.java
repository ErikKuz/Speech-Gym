package com.speechgym.sessions;

import java.net.URI;
import java.util.UUID;

import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.speechgym.common.idempotency.StoredResponse;
import com.speechgym.common.security.CurrentUserService;
import com.speechgym.sessions.dto.CreateSessionRequest;
import com.speechgym.sessions.dto.SessionListResponse;
import com.speechgym.sessions.dto.SessionResponse;
import com.speechgym.sessions.dto.UpdateSessionRequest;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Pattern;

@RestController
@Validated
@RequestMapping("/api/v1/sessions")
public class SessionController {
    private final SessionService sessionService; // Бизнес-логика 
    private final CurrentUserService currentUserService;

    public SessionController(SessionService sessionService, CurrentUserService currentUserService) {
        this.sessionService = sessionService;
        this.currentUserService = currentUserService;
    }

    @PostMapping
    public ResponseEntity<SessionResponse> create(
        @RequestHeader("Idempotency-Key")
        @Pattern(regexp = "^[0-9a-fA-F-]{36}$", message = "Idempotency-Key must be a UUID string.")
        String idempotencyKey,
        @Valid @RequestBody CreateSessionRequest request
    ) {
        StoredResponse<SessionResponse> response = sessionService.createSession(
            currentUserService.requireUserId(),
            idempotencyKey,
            request
        );
        return ResponseEntity.status(response.statusCode())
            .header(HttpHeaders.LOCATION, URI.create(response.location()).toString())
            .body(response.body());
    }

    @GetMapping
    public SessionListResponse list(
        @RequestParam(defaultValue = "0") @Min(0) int page,
        @RequestParam(defaultValue = "20") @Min(1) @Max(100) int size,
        @RequestParam(required = false) String query
    ) {
        return sessionService.list(currentUserService.requireUserId(), query, page, size);
    }

    @GetMapping("/{sessionId}")
    public SessionResponse get(@PathVariable UUID sessionId) {
        return sessionService.get(currentUserService.requireUserId(), sessionId);
    }

    @PatchMapping("/{sessionId}")
    public SessionResponse update(@PathVariable UUID sessionId, @Valid @RequestBody UpdateSessionRequest request) {
        return sessionService.update(currentUserService.requireUserId(), sessionId, request);
    }
}
