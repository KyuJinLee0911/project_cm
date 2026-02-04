package com.kjlee.climbmate.global.security.dto;

import com.kjlee.climbmate.domain.user.entity.User;
import com.kjlee.climbmate.domain.user.entity.enums.Role;
import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.stream.Collectors;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

public record CustomUserDetails(
        Long id,
        String nickname,
        String email,
        String password,
        Role role
) implements UserDetails {
    public static CustomUserDetails from(User user){
        return new CustomUserDetails(user.getId(), user.getNickname(), user.getNickname(), user.getPassword(), user.getRole());
    }

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities(){
        List<String> roles = new ArrayList<>();
        roles.add("ROLE_" + role.toString());

        return roles.stream().map(SimpleGrantedAuthority::new).collect(Collectors.toList());
    }

    @Override
    public String getPassword() {
        return password;
    }

    @Override
    public String getUsername() {
        return nickname;
    }
}
