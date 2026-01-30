package com.ssafy.a203.domain.user.service;

import com.ssafy.a203.domain.user.entity.User;
import com.ssafy.a203.domain.user.exception.DuplicatedEmailException;
import com.ssafy.a203.domain.user.exception.UserNotFoundException;
import com.ssafy.a203.domain.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class UserReader {
    private final UserRepository repository;

    public void isExistsEmail(String email){
        if(repository.existsByEmail(email)){
            throw new DuplicatedEmailException();
        }
    }

    public User getUserByEmail(String email){
        return repository.findByEmailAndDeletedAtIsNull(email)
                .orElseThrow(UserNotFoundException::new);
    }
}
