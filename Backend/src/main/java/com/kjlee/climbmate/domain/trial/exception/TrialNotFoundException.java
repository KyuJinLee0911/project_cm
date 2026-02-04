package com.kjlee.climbmate.domain.trial.exception;

import com.kjlee.climbmate.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class TrialNotFoundException extends ApiException {

    public TrialNotFoundException() {
        super(HttpStatus.BAD_REQUEST, "시도 정보를 찾을 수 없습니다.", "E8001");
    }
}
