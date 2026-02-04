package com.kjlee.climbmate.domain.video._hold.entity.enums;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

public enum HoldType {
    START, COMMON, TOP;

    @JsonCreator
    public static HoldType from(String value) {
        return HoldType.valueOf(value.toUpperCase());
    }

    @JsonValue
    public String toValue() {
        return this.name().toLowerCase();
    }
}
