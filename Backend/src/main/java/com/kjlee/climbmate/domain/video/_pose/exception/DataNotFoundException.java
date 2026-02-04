package com.kjlee.climbmate.domain.video._pose.exception;

import com.kjlee.climbmate.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class DataNotFoundException extends ApiException {

    public DataNotFoundException() {
        super(HttpStatus.NOT_FOUND, "저장된 영상 분석 정보가 없습니다.", "E7002");
    }
}
