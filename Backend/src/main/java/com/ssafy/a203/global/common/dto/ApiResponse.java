package com.ssafy.a203.global.common.dto;

import com.ssafy.a203.global.common.exception.ApiException;
import org.apache.coyote.Response;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

public record ApiResponse<T>(
        String code,
        String message,
        T data
) {
    public static <T> ResponseEntity<ApiResponse<T>> of(HttpStatus status, String code){
        return ResponseEntity.status(status).body(new ApiResponse<>(code, null, null));
    }

    public static <T> ResponseEntity<ApiResponse<T>> of(HttpStatus status, String code, String message){
        return ResponseEntity.status(status).body(new ApiResponse<>(code, message, null));
    }

    public static <T> ResponseEntity<ApiResponse<T>> of(HttpStatus status, String code, T data){
        return ResponseEntity.status(status).body(new ApiResponse<>(code, null, data));
    }

    public static <T> ResponseEntity<ApiResponse<T>> of(HttpStatus status, String code,
            String message, T data) {
        return ResponseEntity.status(status).body(new ApiResponse<>(code, message, data));
    }

    public static <T> ApiResponse<T> of(String code, String message, T data){
        return new ApiResponse<>(code, message, data);
    }

    public static <T> ResponseEntity<ApiResponse<T>> failedOf(HttpStatus status, String code, String message){
        return ResponseEntity.status(status).body(new ApiResponse<>(code, message, null));
    }

    public static <T> ResponseEntity<ApiResponse<T>> failedOf(ApiException e){
        return ResponseEntity.status(e.status).body(new ApiResponse<>(e.code, e.getMessage(), null));
    }

    public static <T> ResponseEntity<ApiResponse<T>> created(){
        return ApiResponse.of(HttpStatus.CREATED, "SUCCESS");
    }

    public static <T> ResponseEntity<ApiResponse<T>> created(T data){
        return ApiResponse.of(HttpStatus.CREATED, "SUCCESS", data);
    }

    public static <T> ResponseEntity<ApiResponse<T>> ok(){
        return ApiResponse.of(HttpStatus.OK, "SUCCESS");
    }

    public static <T> ResponseEntity<ApiResponse<T>> ok(T data){
        return ApiResponse.of(HttpStatus.OK, "SUCCESS", data);
    }
}
