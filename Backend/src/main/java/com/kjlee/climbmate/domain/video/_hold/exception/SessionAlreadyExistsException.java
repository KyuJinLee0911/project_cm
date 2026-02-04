package com.kjlee.climbmate.domain.video._hold.exception;

import com.kjlee.climbmate.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class SessionAlreadyExistsException extends ApiException {

    private static final String MESSAGE = "이미 세션이 있습니다.";

    public SessionAlreadyExistsException() {
        super(HttpStatus.BAD_REQUEST, MESSAGE, "E3001");
    }
}
