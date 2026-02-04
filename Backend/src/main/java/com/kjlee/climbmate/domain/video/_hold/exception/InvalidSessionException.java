package com.kjlee.climbmate.domain.video._hold.exception;

import com.kjlee.climbmate.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class InvalidSessionException extends ApiException {

    private static final String MESSAGE = "유효하지 않은 세션 정보입니다.";

    public InvalidSessionException() {
        super(HttpStatus.BAD_REQUEST, MESSAGE, "E3002");
    }
}
