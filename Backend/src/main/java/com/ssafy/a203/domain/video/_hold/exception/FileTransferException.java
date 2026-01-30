package com.ssafy.a203.domain.video._hold.exception;

import com.ssafy.a203.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class FileTransferException extends ApiException {

    public FileTransferException() {
        super(HttpStatus.CONFLICT, "파일 전송 중 문제가 발생했습니다. ", "E3004");
    }
}
