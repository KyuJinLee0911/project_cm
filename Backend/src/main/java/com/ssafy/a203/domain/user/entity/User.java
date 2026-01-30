package com.ssafy.a203.domain.user.entity;

import com.ssafy.a203.domain.user.dto.request.SignUpRequest;
import com.ssafy.a203.domain.user.dto.request.UpdateUserRequest;
import com.ssafy.a203.domain.user.entity.enums.Role;
import com.ssafy.a203.global.common.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.Comment;

@Entity
@Getter
@Table(name = "users")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class User extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Comment("회원 이메일")
    @Column(nullable = false, unique = true)
    private String email;

    @Comment("회원 비밀번호")
    @Column(nullable = false)
    private String password;

    @Comment("회원 닉네임")
    @Column(nullable = false, length = 20)
    private String nickname;

    @Comment("회원 키")
    @Column(nullable = false)
    private Float height;

    @Comment("회원 몸무게")
    @Column(nullable = false)
    private Float weight;

    @Comment("회원 팔 길이")
    private Float reach;

    @Comment("역할")
    @Column(nullable = false)
    @Enumerated(EnumType.STRING)
    private Role role;

    private User(String email, String password, String nickname, Float height, Float weight, Float reach, Role role){
        this.email = email;
        this.password = password;
        this.nickname = nickname;
        this.height = height;
        this.weight = weight;
        this.reach = reach;
        this.role = role;
    }

    public static User from(SignUpRequest request, String password){

        return new User(request.email(), password, request.nickname(), request.height(),
                request.weight(), request.reach(), Role.Member);
    }

    public void update(UpdateUserRequest request){
        this.nickname = request.nickname();
        this.height = request.height();
        this.weight = request.weight();
        this.reach = request.reach();
    }

    public void withdraw(){
        this.delete();
    }
}
