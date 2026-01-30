package com.ssafy.a203.domain.video.exception;

import com.ssafy.a203.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class VideoNotFoundException extends ApiException {

    private static final String MESSAGE = "해당하는 영상이 없습니다.";
    public VideoNotFoundException() {
        super(HttpStatus.NOT_FOUND, MESSAGE, "E2001");
    }
}
