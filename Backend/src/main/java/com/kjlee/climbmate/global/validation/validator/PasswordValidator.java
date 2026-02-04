package com.kjlee.climbmate.global.validation.validator;

import com.kjlee.climbmate.global.validation.annotation.ValidPassword;
import jakarta.validation.ConstraintValidator;
import jakarta.validation.ConstraintValidatorContext;
import java.util.Objects;

public class PasswordValidator implements ConstraintValidator<ValidPassword, String> {


    @Override
    public boolean isValid(String password, ConstraintValidatorContext constraintValidatorContext) {
        if(Objects.isNull(password))
            return false;

        if(password.length() < 8 || password.length() > 16){
            return false;
        }

        boolean hasLetter = password.chars().anyMatch(Character::isLetter);
        boolean hasDigit = password.chars().anyMatch(Character::isDigit);

        return hasLetter && hasDigit;
    }
}
