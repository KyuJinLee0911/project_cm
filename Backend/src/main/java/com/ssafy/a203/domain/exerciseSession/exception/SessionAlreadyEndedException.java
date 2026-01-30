package com.ssafy.a203.domain.exerciseSession.exception;

import com.ssafy.a203.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class SessionAlreadyEndedException extends ApiException {

    public SessionAlreadyEndedException() {
        super(HttpStatus.BAD_REQUEST, "이미 종료된 세션입니다.", "E7002");
    }
}
