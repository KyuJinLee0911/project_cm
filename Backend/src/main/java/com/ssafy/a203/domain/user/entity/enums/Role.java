package com.ssafy.a203.domain.user.entity.enums;

public enum Role {
    Admin(100), Member(2);

    private final int value;

    Role(int value){
        this.value = value;
    }

    public static Role fromValue(int value){
        for(Role role : values()){
            if(role.value == value){
                return role;
            }
        }

        throw new IllegalArgumentException("해당 값에 맞는 role이 없습니다. " + value);
    }
}
