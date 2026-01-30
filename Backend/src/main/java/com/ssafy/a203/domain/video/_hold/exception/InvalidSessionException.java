package com.ssafy.a203.domain.video._hold.exception;

import com.ssafy.a203.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class InvalidSessionException extends ApiException {

    private static final String MESSAGE = "유효하지 않은 세션 정보입니다.";

    public InvalidSessionException() {
        super(HttpStatus.BAD_REQUEST, MESSAGE, "E3002");
    }
}
