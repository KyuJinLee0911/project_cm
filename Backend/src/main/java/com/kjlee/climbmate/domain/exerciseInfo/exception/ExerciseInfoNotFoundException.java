package com.kjlee.climbmate.domain.exerciseInfo.exception;

import com.kjlee.climbmate.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class ExerciseInfoNotFoundException extends ApiException {

    private static final String MESSAGE = "운동 정보를 찾을 수 없습니다.";

    public ExerciseInfoNotFoundException() {
        super(HttpStatus.NOT_FOUND, MESSAGE, "E6001");
    }
}
