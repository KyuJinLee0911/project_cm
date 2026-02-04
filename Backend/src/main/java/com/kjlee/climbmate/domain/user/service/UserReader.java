package com.kjlee.climbmate.domain.user.service;

import com.kjlee.climbmate.domain.user.entity.User;
import com.kjlee.climbmate.domain.user.exception.DuplicatedEmailException;
import com.kjlee.climbmate.domain.user.exception.UserNotFoundException;
import com.kjlee.climbmate.domain.user.repository.UserRepository;
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
