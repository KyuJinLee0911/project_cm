package com.ssafy.a203.domain.user.exception;

import com.ssafy.a203.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class UserNotFoundException extends ApiException {

    private static final String MESSAGE = "회원 정보를 찾을 수 없습니다.";
    public UserNotFoundException() {
        super(HttpStatus.BAD_REQUEST, MESSAGE, "E1001");
    }
}
