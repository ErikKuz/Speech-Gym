package com.speechgym.sessions;

import java.util.Optional;
import java.util.UUID;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

public interface SessionRepository extends JpaRepository<SessionEntity, UUID> {
    Optional<SessionEntity> findByIdAndUserId(UUID id, UUID userId);

    Page<SessionEntity> findByUserIdOrderByUpdatedAtDesc(UUID userId, Pageable pageable);

    @Query("""
        select s
        from SessionEntity s
        where s.userId = :userId
          and (
              lower(s.title) like lower(concat('%', :query, '%'))
              or lower(coalesce(s.goal, '')) like lower(concat('%', :query, '%'))
          )
        order by s.updatedAt desc
        """)
    Page<SessionEntity> searchByUserId(UUID userId, String query, Pageable pageable);

    
}
