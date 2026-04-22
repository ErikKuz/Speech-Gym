package com.speechgym.auth;

import java.util.UUID;

import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.speechgym.auth.dto.AuthResponse;
import com.speechgym.auth.dto.LoginRequest;
import com.speechgym.auth.dto.MeResponse;
import com.speechgym.auth.dto.RegisterRequest;
import com.speechgym.common.error.ConflictException;
import com.speechgym.common.error.ResourceNotFoundException;
import com.speechgym.common.error.UnprocessableEntityException;

@Service
public class AuthService {
    private final UserRepository userRepository;
    private final SubscriptionRepository subscriptionRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenService jwtTokenService;

    public AuthService(
        UserRepository userRepository,
        SubscriptionRepository subscriptionRepository,
        PasswordEncoder passwordEncoder,
        JwtTokenService jwtTokenService
    ) {
        this.userRepository = userRepository;
        this.subscriptionRepository = subscriptionRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtTokenService = jwtTokenService;
    }

    @Transactional
    public AuthResponse register(RegisterRequest request) {
        userRepository.findByEmailIgnoreCase(request.email()).ifPresent(existing -> {
            throw new ConflictException("User with this email already exists.");
        });
        UserEntity user = new UserEntity();
        user.setEmail(request.email().trim().toLowerCase());
        user.setFullName(request.fullName().trim());
        user.setPasswordHash(passwordEncoder.encode(request.password()));
        user = userRepository.save(user);

        SubscriptionEntity subscription = new SubscriptionEntity();
        subscription.setUserId(user.getId());
        subscriptionRepository.save(subscription);

        return toAuthResponse(user, jwtTokenService.issueTokens(user));
    }

    @Transactional(readOnly = true)
    public AuthResponse login(LoginRequest request) {
        UserEntity user = userRepository.findByEmailIgnoreCase(request.email().trim().toLowerCase())
            .orElseThrow(() -> new UnprocessableEntityException("Invalid email or password."));
        if (!passwordEncoder.matches(request.password(), user.getPasswordHash())) {
            throw new UnprocessableEntityException("Invalid email or password.");
        }
        return toAuthResponse(user, jwtTokenService.issueTokens(user));
    }

    @Transactional(readOnly = true)
    public AuthResponse refresh(String refreshToken) {
        Jwt jwt = jwtTokenService.parseRefreshToken(refreshToken);
        UserEntity user = userRepository.findById(UUID.fromString(jwt.getSubject()))
            .orElseThrow(() -> new UnprocessableEntityException("Refresh token user no longer exists."));
        return toAuthResponse(user, jwtTokenService.issueTokens(user));
    }

    @Transactional(readOnly = true)
    public MeResponse me(UUID userId) {
        UserEntity user = userRepository.findById(userId)
            .orElseThrow(() -> new ResourceNotFoundException("User was not found."));
        SubscriptionEntity subscription = subscriptionRepository.findByUserId(userId)
            .orElseThrow(() -> new ResourceNotFoundException("Subscription was not found."));
        return new MeResponse(
            user.getId(),
            user.getEmail(),
            user.getFullName(),
            user.getRole(),
            subscription.getPlanCode(),
            subscription.isActive(),
            subscription.getValidUntil(),
            user.getCreatedAt()
        );
    }

    private AuthResponse toAuthResponse(UserEntity user, TokenBundle tokens) {
        return new AuthResponse(
            user.getId(),
            user.getEmail(),
            user.getFullName(),
            user.getRole(),
            tokens.accessToken(),
            tokens.accessTokenExpiresAt(),
            tokens.refreshToken(),
            tokens.refreshTokenExpiresAt()
        );
    }
}
