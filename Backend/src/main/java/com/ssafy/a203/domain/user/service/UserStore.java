package com.ssafy.a203.domain.user.service;

import com.ssafy.a203.domain.user.entity.User;
import com.ssafy.a203.domain.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class UserStore {
    private final UserRepository repository;

    void save(User user){
        repository.save(user);
    }
}
