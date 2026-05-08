package com.speechgym.auth.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record RegisterRequest( // Тело запроса на регистрацию
    @Email @NotBlank String email, // email, @NotBlank используется в связке с аннотацией @Valid // В контроллере поле данного запроса проверяется на "не пустое"
    @NotBlank @Size(min = 8, max = 72) String password, // Size указвыет максимальное и минмальное количесвто символов для пароля
    @NotBlank @Size(max = 120) String fullName //  Полное имя - также задано с ограничениями
) {
}
