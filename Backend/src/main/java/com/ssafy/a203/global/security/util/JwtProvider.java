package com.ssafy.a203.global.security.util;

import com.ssafy.a203.domain.user.entity.enums.Role;
import com.ssafy.a203.global.security.dto.CustomUserDetails;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import java.security.Key;
import java.util.Date;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class JwtProvider {
    private Key key;
    @Value("${jwt.secret}")
    private String secretKey;
    @Value("${jwt.access.expiration}")
    private long accessTokenValidity; // 1시간
    @Value("${jwt.refresh.expiration}")
    private long refreshTokenValidity; // 일주일

    @PostConstruct
    protected void init(){
        byte[] secretKeyBytes = Decoders.BASE64.decode(secretKey);
        key = Keys.hmacShaKeyFor(secretKeyBytes);
    }

    public String generateAccessToken(CustomUserDetails user){
        return createToken(user, true);
    }

    public String generateRefreshToken(CustomUserDetails user){
        return createToken(user, false);
    }

    private String createToken(CustomUserDetails user, boolean isAccessToken){
        Claims claims = Jwts.claims().setSubject(user.nickname());
        claims.put("uid", user.id());
        claims.put("email", user.email());
        claims.put("role", user.role().name());

        Date now = new Date();
        long validity = isAccessToken ? accessTokenValidity : refreshTokenValidity;
        Date expiry = new Date(now.getTime() + validity);

        return Jwts.builder()
                .setClaims(claims)
                .setIssuedAt(now)
                .setExpiration(expiry)
                .signWith(key, SignatureAlgorithm.HS256)
                .compact();
    }

    public boolean validateToken(String token){
        try{
            Jwts.parserBuilder().setSigningKey(key).build().parseClaimsJws(token);
            return true;
        } catch(JwtException | IllegalArgumentException e){
            return false;
        }
    }

    public Long getId(String token){
        return parseClaims(token).get("uid", Number.class).longValue();
    }

    public String getNickname(String token){
        return parseClaims(token).getSubject();
    }

    public String getEmail(String token){
        return parseClaims(token).get("email", String.class);
    }

    public long getRemainTime(String token){
        Date now = new Date();
        return parseClaims(token).getExpiration().getTime() - now.getTime();
    }

    public long getExpirationTime(String token){
        return parseClaims(token).getExpiration().getTime();
    }

    public Role getRole(String token){
        String role = parseClaims(token).get("role", String.class);
        return Role.valueOf(role);
    }

    private Claims parseClaims(String token){
        return Jwts.parserBuilder()
                .setSigningKey(key)
                .build()
                .parseClaimsJws(token)
                .getBody();
    }
}
