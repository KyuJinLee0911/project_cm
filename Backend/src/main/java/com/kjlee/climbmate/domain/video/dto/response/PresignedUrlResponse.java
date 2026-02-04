package com.kjlee.climbmate.domain.video.dto.response;

public record PresignedUrlResponse(
        String fileKey,
        String presignedUrl
) {
    public static PresignedUrlResponse of(String fileKey, String presignedUrl){
        return new PresignedUrlResponse(fileKey, presignedUrl);
    }
}
