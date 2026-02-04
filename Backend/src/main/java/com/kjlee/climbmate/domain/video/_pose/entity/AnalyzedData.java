package com.kjlee.climbmate.domain.video._pose.entity;

import com.kjlee.climbmate.domain.video.entity.Video;
import com.kjlee.climbmate.global.common.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.Comment;

@Entity
@Getter
@Table(name = "analyzed_datas")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class AnalyzedData extends BaseEntity {

    @Id
    @Column(name = "id", nullable = false)
    private String id;

    @Comment("상태")
    @Column(name = "status")
    String status;

    @Column(name = "message")
    String message;

    @Comment("분석 결과")
    @Column(name = "result_json", columnDefinition = "text")
    private String resultJson;

    @Comment("영상 id")
    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "video_id")
    Video video;

    private AnalyzedData(String id, String status, String message, String resultJson, Video video) {
        this.id = id;
        this.status = status;
        this.message = message;
        this.resultJson = resultJson;
        this.video = video;
    }

    public static AnalyzedData of(String id, String status, String message, String resultJson,
            Video video) {
        return new AnalyzedData(id, status, message, resultJson, video);
    }

    public void updateStatus(String status, String message) {
        this.status = status;
        this.message = message;
    }

    public void updateResult(String resultJson) {
        this.resultJson = resultJson;
    }
}

