package com.ssafy.a203.domain.video._hold.exception;

import com.ssafy.a203.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class HoldNotBelongsException extends ApiException {

    public HoldNotBelongsException() {
        super(HttpStatus.BAD_REQUEST, "홀드가 영상에 속해있지 않습니다.", "E3005");
    }
}
