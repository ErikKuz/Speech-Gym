package com.speechgym.auth;

import org.springframework.http.HttpStatus;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.DeleteMapping;
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
public class AuthController { // Контроллер авторизации

    private final AuthService authService; // Сервис аторизации пользователя
    private final CurrentUserService currentUserService; // Сервис пользователя

    public AuthController(AuthService authService, CurrentUserService currentUserService) { // Конструктор
        this.authService = authService; // Инициализация
        this.currentUserService = currentUserService; // Spring автоматически создает объект класса AuthController и инициализирует эти поля
    }

    @PostMapping("/auth/register") // POST Запрос на регистрацию (создание клиента)
    @ResponseStatus(HttpStatus.CREATED) // Нужно вернуть клиенту HTTP status 201 Created // Обычно это ставят на метод контроллера, который создает новый ресурс.
    public AuthResponse register(@Valid @RequestBody RegisterRequest request) { // Взять JSON из тела запроса, десериализация этого JSON в Java-объект RegisterRequest, валидация этого объекта
        return authService.register(request);  // Вызываем соответственный сервис
    }

    @PostMapping("/auth/login") // POST Запрос на вход пользователя в уже существующий аккаунт
    public AuthResponse login(@Valid @RequestBody LoginRequest request) { // Взять JSON из тела запроса, десериализация этого JSON в Java-объект LoginRequest, валидация этого объекта
        return authService.login(request); // Вызываем соответственный сервис
    }

    @PostMapping("/auth/refresh") // POST Запрос для получения новой пары токенов refresh и access
    public AuthResponse refresh(@Valid @RequestBody RefreshTokenRequest request) { // Взять JSON из тела запроса, десериализация этого JSON в Java-объект RefreshTokenRequest, валидация этого объекта
        return authService.refresh(request.refreshToken()); // Вызываем соответственный сервис
    }

    @GetMapping("/me") // GET запрос 
    public MeResponse me() {
        return authService.me(currentUserService.requireUserId());
    }

    @DeleteMapping("/me")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteMe() {
        // Deletes exactly the currently authenticated user (from JWT subject).
        authService.deleteAccount(currentUserService.requireUserId());
    }

    @PostMapping("/auth/change-password")
    public AuthResponse changePassword(@Valid @RequestBody ChangePasswordRequest request) {
        return authService.changePassword(currentUserService.requireUserId(), request);
    }
}
