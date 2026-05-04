package com.speechgym.reports;

import java.util.Map;

public interface SpeechReportClient {
<<<<<<< Updated upstream
    ReportAnalysisResponse generateReport(Map<String, Object> whisperJson, String pitchType, int targetDurationSec, String notes);
=======
    ReportAnalysisResponse generateReport(
        Map<String, Object> whisperJson,
        String pitchType,
        int targetDurationSec,
        String notes
    );
>>>>>>> Stashed changes
}
