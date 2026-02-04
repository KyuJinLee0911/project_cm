package com.kjlee.climbmate.global.common.exception;

import org.springframework.http.HttpStatus;

public class ApiException extends RuntimeException{
    public final String code;
    public final HttpStatus status;

    public ApiException(HttpStatus status, String message, String code){
        super(message);
        this.code = code;
        this.status = status;
    }
}
