package com.ssafy.a203.domain.trial.exception;

import com.ssafy.a203.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class TrialNotFoundException extends ApiException {

    public TrialNotFoundException() {
        super(HttpStatus.BAD_REQUEST, "시도 정보를 찾을 수 없습니다.", "E8001");
    }
}
