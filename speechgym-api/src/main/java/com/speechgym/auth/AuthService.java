package com.speechgym.auth;

import java.util.UUID;

import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.speechgym.auth.dto.AuthResponse;
import com.speechgym.auth.dto.ChangePasswordRequest;
import com.speechgym.auth.dto.LoginRequest;
import com.speechgym.auth.dto.MeResponse;
import com.speechgym.auth.dto.RegisterRequest;
import com.speechgym.common.error.ConflictException;
import com.speechgym.common.error.ResourceNotFoundException;
import com.speechgym.common.error.UnprocessableEntityException;

@Service
public class AuthService {

    private final UserRepository userRepository; // Сущность нашей БД // репозиторий для работы с пользователями
    private final SubscriptionRepository subscriptionRepository; // Сущность нашей БД // репозиторий для работы с подпиской (Мы удалим, данный механизм у нас не реализован)

    private final PasswordEncoder passwordEncoder; // Класс из Spring Security // Безопасная работа с паролями // хэши
    private final JwtTokenService jwtTokenService; // Вся логика работы с JWT токенами

    public AuthService( // Конструктор
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

    @Transactional // выполни этот метод внутри транзакции БД (То есть все функции изменения в БД выполняются в рамках одной транзакции, если хотя бы одна функция взаимодействия с БД не срабатывает)
    public AuthResponse register(RegisterRequest request) {

        userRepository.findByEmailIgnoreCase(request.email()).ifPresent(existing -> { // Если найдем пользователя с таким же email, выбросим исключение
            throw new ConflictException("User with this email already exists.");
        });
        UserEntity user = new UserEntity(); // Создаем новую сущность пользователя для добавления в БД
        user.setEmail(request.email().trim().toLowerCase()); // Инициллизируем сеттером email у пользователя
        user.setFullName(request.fullName().trim()); // Инициллизируем сеттером полное имя пользователя
        user.setPasswordHash(passwordEncoder.encode(request.password())); // Инициализируем поле где хранится hash пароля пользователя //
        user = userRepository.save(user); // Обращаемя к интерфейсу репозитория и сохраняем пользователя //

        SubscriptionEntity subscription = new SubscriptionEntity(); // Это мы удалим, механизма подписки не будет
        subscription.setUserId(user.getId()); 
        subscriptionRepository.save(subscription);

        return toAuthResponse(user, jwtTokenService.issueTokens(user)); // С помощью метода  toAuthResponse() Приводим в нужный формат ответа
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

    @Transactional
    public AuthResponse changePassword(UUID userId, ChangePasswordRequest request) {
        UserEntity user = userRepository.findById(userId)
            .orElseThrow(() -> new ResourceNotFoundException("User was not found."));
        if (!passwordEncoder.matches(request.currentPassword(), user.getPasswordHash())) {
            throw new UnprocessableEntityException("Current password is incorrect.");
        }
        if (passwordEncoder.matches(request.newPassword(), user.getPasswordHash())) {
            throw new UnprocessableEntityException("New password must be different from current password.");
        }
        user.setPasswordHash(passwordEncoder.encode(request.newPassword()));
        return toAuthResponse(user, jwtTokenService.issueTokens(user));
    }

    @Transactional
    public void deleteAccount(UUID userId) {
        // Explicit "find then delete" gives a clear 404-style business error when user is already missing.
        UserEntity user = userRepository.findById(userId)
            .orElseThrow(() -> new ResourceNotFoundException("User was not found."));
        // Entity relationships/cascades defined in JPA mappings clean up owned rows on user deletion.
        userRepository.delete(user);
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
