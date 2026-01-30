package com.ssafy.a203.global.common.handler;

import com.ssafy.a203.global.common.dto.ApiResponse;
import com.ssafy.a203.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;

@ControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Object>> handleValidationExceptions(
            MethodArgumentNotValidException exeption
    ) {
        FieldError error = exeption.getBindingResult().getFieldErrors().get(0);
        String errorMessage = error.getField() + ": " + error.getDefaultMessage();

        return ApiResponse.failedOf(HttpStatus.BAD_REQUEST, errorMessage, "E5001");
    }

    @ExceptionHandler(ApiException.class)
    public ResponseEntity<ApiResponse<Object>> handleAllExceptions(ApiException e) {
        return ApiResponse.failedOf(e);
    }
}
