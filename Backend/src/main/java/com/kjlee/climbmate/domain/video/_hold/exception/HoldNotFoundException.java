package com.kjlee.climbmate.domain.video._hold.exception;

import com.kjlee.climbmate.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class HoldNotFoundException extends ApiException {

    private static final String MESSAGE = "홀드 정보를 찾을 수 없습니다.";

    public HoldNotFoundException() {
        super(HttpStatus.BAD_REQUEST, MESSAGE, "E3001");
    }
}
