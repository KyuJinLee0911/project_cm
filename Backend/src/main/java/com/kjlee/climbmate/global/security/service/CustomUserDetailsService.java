package com.kjlee.climbmate.global.security.service;

import com.kjlee.climbmate.domain.user.entity.User;
import com.kjlee.climbmate.domain.user.service.UserReader;
import com.kjlee.climbmate.global.security.dto.CustomUserDetails;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class CustomUserDetailsService implements UserDetailsService {

    private final UserReader userReader;
    @Override
    public UserDetails loadUserByUsername(String email) throws UsernameNotFoundException {
        log.info("로그인된 유저 : " + email);
        User user = userReader.getUserByEmail(email);
        return new CustomUserDetails(user.getId(), user.getNickname(), user.getEmail(), user.getPassword(), user.getRole());
    }
}
