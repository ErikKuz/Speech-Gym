package com.speechgym.reports;

import static org.assertj.core.api.Assertions.assertThat;

import java.nio.charset.StandardCharsets;
import java.util.List;

import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import org.junit.jupiter.api.Test;

class PdfReportGeneratorTest {
    private final PdfReportGenerator generator = new PdfReportGenerator();

    @Test
    void generateBuildsPdfForCurrentReportSummaryContract() throws Exception {
        ReportGenerationResult result = new ReportGenerationResult(
            84,
            88,
            142,
            3,
            81,
            86,
            "steady",
            List.of("Strong opening", "Clear problem"),
            List.of("Make the ask more concrete"),
            List.of("Add traction numbers", "Finish with one specific action")
        );

        byte[] pdf = generator.generate("Demo session", result);

        assertThat(new String(pdf, 0, 4, StandardCharsets.US_ASCII)).isEqualTo("%PDF");
        assertThat(pdf.length).isGreaterThan(500);
        try (PDDocument document = Loader.loadPDF(pdf)) {
            String text = new PDFTextStripper().getText(document);
            assertThat(text)
                .contains("SpeechGym Report")
                .contains("Session: Demo session")
                .contains("Overall score: 84")
                .contains("Clarity: 88, Pace WPM: 142")
                .contains("Confidence: 81, Structure: 86")
                .contains("Tone: steady")
                .contains("Top recommendation: Add traction numbers");
        }
    }
}
