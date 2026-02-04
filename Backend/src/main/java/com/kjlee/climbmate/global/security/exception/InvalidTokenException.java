package com.kjlee.climbmate.global.security.exception;

import com.kjlee.climbmate.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class InvalidTokenException extends ApiException {
    private static final String MESSAGE = "만료된 토큰입니다.";
    public InvalidTokenException() {
        super(HttpStatus.FORBIDDEN, MESSAGE, "E1005");
    }
}
