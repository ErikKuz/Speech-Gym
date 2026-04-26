package com.speechgym.reports;

import java.util.List;
import java.util.UUID;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.speechgym.common.security.CurrentUserService;
import com.speechgym.reports.dto.ReportSummaryResponse;

@RestController
@RequestMapping("/api/v1")
public class ReportController {
    private final ReportService reportService;
    private final CurrentUserService currentUserService;

    public ReportController(ReportService reportService, CurrentUserService currentUserService) {
        this.reportService = reportService;
        this.currentUserService = currentUserService;
    }

    @GetMapping("/sessions/{sessionId}/reports")
    public List<ReportSummaryResponse> list(@PathVariable UUID sessionId) {
        return reportService.listBySession(currentUserService.requireUserId(), sessionId);
    }

    @GetMapping("/reports/{reportId}")
    public ReportSummaryResponse get(@PathVariable UUID reportId) {
        return reportService.get(currentUserService.requireUserId(), reportId);
    }

    @GetMapping("/reports/{reportId}/pdf")
    public ResponseEntity<byte[]> downloadPdf(@PathVariable UUID reportId) {
        return reportService.downloadPdf(currentUserService.requireUserId(), reportId);
    }
}
