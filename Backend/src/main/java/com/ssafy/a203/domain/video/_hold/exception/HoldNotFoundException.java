package com.ssafy.a203.domain.video._hold.exception;

import com.ssafy.a203.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class HoldNotFoundException extends ApiException {

    private static final String MESSAGE = "홀드 정보를 찾을 수 없습니다.";

    public HoldNotFoundException() {
        super(HttpStatus.BAD_REQUEST, MESSAGE, "E3001");
    }
}
