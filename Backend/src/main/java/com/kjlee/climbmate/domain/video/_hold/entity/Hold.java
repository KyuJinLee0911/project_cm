package com.kjlee.climbmate.domain.video._hold.entity;

import com.kjlee.climbmate.domain.video._hold.dto.request.HoldDetectionRequest;
import com.kjlee.climbmate.domain.video._hold.entity.enums.HoldType;
import com.kjlee.climbmate.domain.video.entity.Video;
import com.kjlee.climbmate.global.common.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.util.List;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.Comment;
import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

@Entity
@Getter
@Table(name = "holds")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Hold extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Comment("x 좌표")
    @Column(nullable = false)
    private Double x;

    @Comment("y 좌표")
    @Column(nullable = false)
    private Double y;

    @Comment("홀드 인식 결과")
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "polygon", columnDefinition = "jsonb")
    private List<List<Double>> polygon;

    @Comment("홀드 인식 박스")
    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "bbox", columnDefinition = "jsonb")
    private List<Double> bbox;

    @Comment("홀드 타입")
    @Column(nullable = false)
    @Enumerated(EnumType.STRING)
    private HoldType holdType;

    @Comment("연관 영상")
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "video_id", nullable = false)
    private Video video;

    private Hold(Double x, Double y, HoldType type, Video video) {
        this.x = x;
        this.y = y;
        this.video = video;
        this.holdType = type;
    }

    public static Hold from(HoldDetectionRequest request, Video video) {
        return new Hold(request.x(), request.y(), request.holdType(), video);
    }

    public void updatePolygonAndBox(List<List<Double>> polygon, List<Double> bbox) {
        this.polygon = polygon;
        this.bbox = bbox;
    }

    public void deleteHold() {
        this.delete();
    }

}
