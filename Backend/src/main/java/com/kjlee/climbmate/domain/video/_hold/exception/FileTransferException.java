package com.kjlee.climbmate.domain.video._hold.exception;

import com.kjlee.climbmate.global.common.exception.ApiException;
import org.springframework.http.HttpStatus;

public class FileTransferException extends ApiException {

    public FileTransferException() {
        super(HttpStatus.CONFLICT, "파일 전송 중 문제가 발생했습니다. ", "E3004");
    }
}
