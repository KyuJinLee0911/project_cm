package com.ssafy.a203.domain.exerciseSession.exception;

import com.ssafy.a203.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class SessionNotFoundException extends ApiException {

    public SessionNotFoundException() {
        super(HttpStatus.NOT_FOUND, "세션을 찾을 수 없습니다.", "7001");
    }
}
