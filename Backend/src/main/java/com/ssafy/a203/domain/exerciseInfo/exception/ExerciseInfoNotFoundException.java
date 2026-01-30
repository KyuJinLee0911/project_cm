package com.ssafy.a203.domain.exerciseInfo.exception;

import com.ssafy.a203.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class ExerciseInfoNotFoundException extends ApiException {

    private static final String MESSAGE = "운동 정보를 찾을 수 없습니다.";

    public ExerciseInfoNotFoundException() {
        super(HttpStatus.NOT_FOUND, MESSAGE, "E6001");
    }
}
