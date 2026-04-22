package com.speechgym.common.error;

import java.net.URI;
import java.util.List;
import java.util.Map;

import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingRequestHeaderException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.ServletWebRequest;
import org.springframework.web.context.request.WebRequest;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;

import jakarta.validation.ConstraintViolationException;

@RestControllerAdvice
public class GlobalExceptionHandler extends ResponseEntityExceptionHandler {
    @Override
    protected ResponseEntity<Object> handleMethodArgumentNotValid(
        MethodArgumentNotValidException ex,
        HttpHeaders headers,
        HttpStatusCode status,
        WebRequest request
    ) {
        ProblemDetail problemDetail = createProblemDetail(
            ex,
            HttpStatus.BAD_REQUEST,
            "Request validation failed.",
            "validation-error",
            null,
            request
        );
        problemDetail.setProperty(
            "fieldErrors",
            ex.getBindingResult().getFieldErrors().stream()
                .map(this::toFieldError)
                .toList()
        );
        return handleExceptionInternal(ex, problemDetail, headers, HttpStatus.BAD_REQUEST, request);
    }

    @ExceptionHandler(MissingRequestHeaderException.class)
    ResponseEntity<ProblemDetail> handleMissingRequestHeader(
        MissingRequestHeaderException ex,
        ServletWebRequest request
    ) {
        return ResponseEntity.badRequest()
            .body(baseProblem(HttpStatus.BAD_REQUEST, ex.getHeaderName() + " header is required.", "missing-header", request));
    }

    @ExceptionHandler(ConstraintViolationException.class)
    ResponseEntity<ProblemDetail> handleConstraintViolation(
        ConstraintViolationException exception,
        ServletWebRequest request
    ) {
        ProblemDetail problemDetail = baseProblem(
            HttpStatus.BAD_REQUEST,
            "Constraint violation.",
            "constraint-violation",
            request
        );
        problemDetail.setProperty(
            "fieldErrors",
            exception.getConstraintViolations().stream()
                .map(violation -> Map.of(
                    "field", violation.getPropertyPath().toString(),
                    "message", violation.getMessage()
                ))
                .toList()
        );
        return ResponseEntity.badRequest().body(problemDetail);
    }

    @ExceptionHandler(ResourceNotFoundException.class)
    ResponseEntity<ProblemDetail> handleNotFound(ResourceNotFoundException exception, ServletWebRequest request) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND)
            .body(baseProblem(HttpStatus.NOT_FOUND, exception.getMessage(), "resource-not-found", request));
    }

    @ExceptionHandler(ConflictException.class)
    ResponseEntity<ProblemDetail> handleConflict(ConflictException exception, ServletWebRequest request) {
        return ResponseEntity.status(HttpStatus.CONFLICT)
            .body(baseProblem(HttpStatus.CONFLICT, exception.getMessage(), "conflict", request));
    }

    @ExceptionHandler(UnprocessableEntityException.class)
    ResponseEntity<ProblemDetail> handleUnprocessable(
        UnprocessableEntityException exception,
        ServletWebRequest request
    ) {
        return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY)
            .body(baseProblem(
                HttpStatus.UNPROCESSABLE_ENTITY,
                exception.getMessage(),
                "unprocessable-entity",
                request
            ));
    }

    @ExceptionHandler(IllegalArgumentException.class)
    ResponseEntity<ProblemDetail> handleIllegalArgument(
        IllegalArgumentException exception,
        ServletWebRequest request
    ) {
        return ResponseEntity.badRequest()
            .body(baseProblem(HttpStatus.BAD_REQUEST, exception.getMessage(), "bad-request", request));
    }

    private ProblemDetail baseProblem(
        HttpStatus status,
        String detail,
        String type,
        ServletWebRequest request
    ) {
        ProblemDetail problemDetail = ProblemDetail.forStatusAndDetail(status, detail);
        problemDetail.setTitle(status.getReasonPhrase());
        problemDetail.setType(URI.create("https://speechgym.dev/problems/" + type));
        problemDetail.setInstance(URI.create(request.getRequest().getRequestURI()));
        return problemDetail;
    }

    private Map<String, String> toFieldError(FieldError fieldError) {
        return Map.of(
            "field", fieldError.getField(),
            "message", fieldError.getDefaultMessage() == null ? "Invalid value." : fieldError.getDefaultMessage()
        );
    }
}
