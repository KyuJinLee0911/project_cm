package com.kjlee.climbmate.domain.user.service;

import com.kjlee.climbmate.domain.user.entity.User;
import com.kjlee.climbmate.domain.user.repository.UserRepository;
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
