package com.kjlee.climbmate.domain.user.repository;

import com.kjlee.climbmate.domain.user.entity.User;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;


public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);

    boolean existsByEmail(String email);

    Optional<User> findByEmailAndDeletedAtIsNull(String email);
}
