package com.kjlee.climbmate.domain.user.exception;

import com.kjlee.climbmate.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class DuplicatedEmailException extends ApiException {
    private static final String MESSAGE = "이미 가입 되어 있는 이메일입니다.";

    public DuplicatedEmailException() {
        super(HttpStatus.BAD_REQUEST, MESSAGE, "E1002");
    }
}
