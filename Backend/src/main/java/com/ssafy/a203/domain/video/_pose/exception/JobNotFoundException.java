package com.ssafy.a203.domain.video._pose.exception;

import com.ssafy.a203.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class JobNotFoundException extends ApiException {

    private static final String MESSAGE = "분석 Job을 찾을 수 없습니다.";

    public JobNotFoundException() {
        super(HttpStatus.NOT_FOUND, MESSAGE, "E7001");
    }
}
