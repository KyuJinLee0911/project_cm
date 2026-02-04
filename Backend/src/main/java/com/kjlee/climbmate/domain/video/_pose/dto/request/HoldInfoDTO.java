package com.kjlee.climbmate.domain.video._pose.dto.request;

import com.kjlee.climbmate.domain.video._hold.entity.enums.HoldType;
import java.util.List;

public record HoldInfoDTO(
        HoldType type,
        List<List<Double>> polygon,
        List<Double> bbox
) {

}
