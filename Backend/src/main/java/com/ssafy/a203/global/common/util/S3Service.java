package com.ssafy.a203.global.common.util;

import com.ssafy.a203.domain.video.dto.response.PresignedUrlResponse;
import java.time.Duration;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.services.s3.presigner.S3Presigner;
import software.amazon.awssdk.services.s3.presigner.model.GetObjectPresignRequest;
import software.amazon.awssdk.services.s3.presigner.model.PresignedGetObjectRequest;
import software.amazon.awssdk.services.s3.presigner.model.PresignedPutObjectRequest;

@Service
@RequiredArgsConstructor
public class S3Service {

    private final S3Presigner s3Presigner;
    private static final int EXPIRATION_MINUTES = 5;

    @Value("${spring.cloud.aws.s3.bucket}")
    private String bucketName;

    public PresignedUrlResponse generateUploadUrl(String fileName) {
//        String contentType = "video/mp4";
        String extention = fileName.substring(fileName.lastIndexOf('.') + 1).toLowerCase();
        String contentType = switch (extention) {
            case "jpg", "jpeg" -> "image/jpeg";
            case "png" -> "image/png";
            case "mp4" -> "video/mp4";
            case "mov" -> "video/quicktime";
            default -> "application/octet-stream";
        };

        String key = UUID.randomUUID() + "_" + fileName;

        PutObjectRequest putReq = PutObjectRequest.builder()
                .bucket(bucketName)
                .key(key)
                .contentType(contentType)
                .build();

        PresignedPutObjectRequest presignedPut = s3Presigner.presignPutObject(b ->
                b.putObjectRequest(putReq)
                        .signatureDuration(Duration.ofMinutes(EXPIRATION_MINUTES))
        );

        return PresignedUrlResponse.of(key, presignedPut.url().toString());
    }

    public String generateDownloadUrl(String objectKey) {
        GetObjectRequest getReq = GetObjectRequest.builder()
                .bucket(bucketName)
                .key(objectKey)
                .build();

        PresignedGetObjectRequest presignedGet = s3Presigner.presignGetObject(
                GetObjectPresignRequest.builder()
                        .signatureDuration(Duration.ofMinutes(EXPIRATION_MINUTES))
                        .getObjectRequest(getReq).build());

        return presignedGet.url().toString();
    }
}
