package com.ssafy.a203.domain.trial.exception;

import com.ssafy.a203.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class TrialAccessDeniedException extends ApiException {

    public TrialAccessDeniedException() {
        super(HttpStatus.BAD_REQUEST, "Trial이 해당 Session에 속하지 않았습니다.", "E8002");
    }
}
