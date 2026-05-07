package com.speechgym.reports;

import java.util.Map;

public interface SpeechReportClient {
    ReportAnalysisResponse generateReport(
        Map<String, Object> whisperJson,
        String pitchType,
        int targetDurationSec,
        String notes
    );
}
