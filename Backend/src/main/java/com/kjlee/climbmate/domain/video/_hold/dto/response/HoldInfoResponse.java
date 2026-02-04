package com.kjlee.climbmate.domain.video._hold.dto.response;

import com.kjlee.climbmate.domain.video._hold.entity.Hold;
import java.util.List;

public record HoldInfoResponse(
        Long holdId,
        Double x,
        Double y,
        List<List<Double>> polygon,
        List<Double> bbox
) {

    public static HoldInfoResponse from(Hold hold) {
        return new HoldInfoResponse(hold.getId(), hold.getX(), hold.getY(), hold.getPolygon(),
                hold.getBbox());
    }

}
