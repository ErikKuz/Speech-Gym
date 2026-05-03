package com.speechgym.auth;

import org.springframework.http.HttpStatus;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.speechgym.auth.dto.AuthResponse;
import com.speechgym.auth.dto.ChangePasswordRequest;
import com.speechgym.auth.dto.LoginRequest;
import com.speechgym.auth.dto.MeResponse;
import com.speechgym.auth.dto.RefreshTokenRequest;
import com.speechgym.auth.dto.RegisterRequest;
import com.speechgym.common.security.CurrentUserService;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/v1")
@Validated
public class AuthController {
    private final AuthService authService;
    private final CurrentUserService currentUserService;

    public AuthController(AuthService authService, CurrentUserService currentUserService) {
        this.authService = authService;
        this.currentUserService = currentUserService;
    }

    @PostMapping("/auth/register")
    @ResponseStatus(HttpStatus.CREATED)
    public AuthResponse register(@Valid @RequestBody RegisterRequest request) {
        return authService.register(request);
    }

    @PostMapping("/auth/login")
    public AuthResponse login(@Valid @RequestBody LoginRequest request) {
        return authService.login(request);
    }

    @PostMapping("/auth/refresh")
    public AuthResponse refresh(@Valid @RequestBody RefreshTokenRequest request) {
        return authService.refresh(request.refreshToken());
    }

    @GetMapping("/me")
    public MeResponse me() {
        return authService.me(currentUserService.requireUserId());
    }

    @PostMapping("/auth/change-password")
    public AuthResponse changePassword(@Valid @RequestBody ChangePasswordRequest request) {
        return authService.changePassword(currentUserService.requireUserId(), request);
    }
}
