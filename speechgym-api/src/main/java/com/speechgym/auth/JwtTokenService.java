package com.speechgym.auth;

import java.time.Clock;
import java.time.Instant;
import java.util.Map;
import java.util.UUID;

import org.springframework.security.oauth2.jose.jws.MacAlgorithm;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.jwt.JwtClaimsSet;
import org.springframework.security.oauth2.jwt.JwtDecoder;
import org.springframework.security.oauth2.jwt.JwtEncoder;
import org.springframework.security.oauth2.jwt.JwtEncoderParameters;
import org.springframework.security.oauth2.jwt.JwsHeader;
import org.springframework.stereotype.Service;

import com.speechgym.common.config.AppProperties;
import com.speechgym.common.error.UnprocessableEntityException;

@Service
public class JwtTokenService {
    private final JwtEncoder jwtEncoder;
    private final JwtDecoder jwtDecoder;
    private final AppProperties properties;
    private final Clock clock;

    public JwtTokenService(JwtEncoder jwtEncoder, JwtDecoder jwtDecoder, AppProperties properties, Clock clock) {
        this.jwtEncoder = jwtEncoder;
        this.jwtDecoder = jwtDecoder;
        this.properties = properties;
        this.clock = clock;
    }

    public TokenBundle issueTokens(UserEntity user) {
        Instant now = Instant.now(clock);
        Instant accessExpiresAt = now.plus(properties.jwt().accessTokenTtl());
        Instant refreshExpiresAt = now.plus(properties.jwt().refreshTokenTtl());
        return new TokenBundle(
            createToken(user, "access", accessExpiresAt),
            accessExpiresAt,
            createToken(user, "refresh", refreshExpiresAt),
            refreshExpiresAt
        );
    }

    public Jwt parseRefreshToken(String token) {
        Jwt jwt = jwtDecoder.decode(token);
        if (!"refresh".equals(jwt.getClaimAsString("token_type"))) {
            throw new UnprocessableEntityException("Refresh token is invalid.");
        }
        return jwt;
    }

    private String createToken(UserEntity user, String tokenType, Instant expiresAt) {
        JwtClaimsSet claimsSet = JwtClaimsSet.builder()
            .issuer(properties.jwt().issuer())
            .subject(user.getId().toString())
            .issuedAt(Instant.now(clock))
            .expiresAt(expiresAt)
            .claims(claims -> claims.putAll(Map.of(
                "role", user.getRole(),
                "email", user.getEmail(),
                "full_name", user.getFullName(),
                "token_type", tokenType
            )))
            .build();
        return jwtEncoder.encode(
            JwtEncoderParameters.from(JwsHeader.with(MacAlgorithm.HS256).build(), claimsSet)
        ).getTokenValue();
    }
}
