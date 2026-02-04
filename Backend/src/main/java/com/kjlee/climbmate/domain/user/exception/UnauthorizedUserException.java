package com.kjlee.climbmate.domain.user.exception;

import com.kjlee.climbmate.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class UnauthorizedUserException extends ApiException {

    private static final String MESSAGE = "접근 권한이 없습니다.";
    public UnauthorizedUserException() {
        super(HttpStatus.UNAUTHORIZED, MESSAGE, "E1003");
    }
}
