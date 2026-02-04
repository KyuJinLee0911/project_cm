package com.kjlee.climbmate.domain.exerciseSession.exception;

import com.kjlee.climbmate.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class SessionAlreadyEndedException extends ApiException {

    public SessionAlreadyEndedException() {
        super(HttpStatus.BAD_REQUEST, "이미 종료된 세션입니다.", "E7002");
    }
}
