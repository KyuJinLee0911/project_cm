package com.kjlee.climbmate.domain.video._hold.dto.request;

import com.kjlee.climbmate.domain.video._hold.entity.enums.HoldType;
import jakarta.validation.constraints.NotNull;

public record HoldDetectionRequest(
        @NotNull Double x,
        @NotNull Double y,
        @NotNull HoldType holdType
) {

}
