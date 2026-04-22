package com.speechgym.reports;

import java.io.ByteArrayOutputStream;
import java.io.IOException;

import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.PDPageContentStream;
import org.apache.pdfbox.pdmodel.common.PDRectangle;
import org.apache.pdfbox.pdmodel.font.PDType1Font;
import org.apache.pdfbox.pdmodel.font.Standard14Fonts;
import org.springframework.stereotype.Service;

@Service
public class PdfReportGenerator {
    public byte[] generate(String sessionTitle, ReportGenerationResult result) {
        try (PDDocument document = new PDDocument();
             ByteArrayOutputStream outputStream = new ByteArrayOutputStream()) {
            PDPage page = new PDPage(PDRectangle.A4);
            document.addPage(page);
            try (PDPageContentStream contentStream = new PDPageContentStream(document, page)) {
                contentStream.beginText();
                contentStream.setFont(new PDType1Font(Standard14Fonts.FontName.HELVETICA_BOLD), 16);
                contentStream.newLineAtOffset(50, 780);
                contentStream.showText("SpeechGym Report");
                contentStream.setFont(new PDType1Font(Standard14Fonts.FontName.HELVETICA), 11);
                contentStream.newLineAtOffset(0, -30);
                contentStream.showText("Session: " + sessionTitle);
                contentStream.newLineAtOffset(0, -20);
                contentStream.showText("Overall score: " + result.overallScore());
                contentStream.newLineAtOffset(0, -18);
                contentStream.showText("Clarity: " + result.clarity() + ", Pace WPM: " + result.paceWpm());
                contentStream.newLineAtOffset(0, -18);
                contentStream.showText("Confidence: " + result.confidence() + ", Structure: " + result.structureScore());
                contentStream.newLineAtOffset(0, -18);
                contentStream.showText("Tone: " + result.emotionalTone());
                contentStream.newLineAtOffset(0, -18);
                contentStream.showText("Top recommendation: " + result.recommendations().getFirst());
                contentStream.endText();
            }
            document.save(outputStream);
            return outputStream.toByteArray();
        }
        catch (IOException exception) {
            throw new IllegalStateException("Unable to generate PDF report.", exception);
        }
    }
}
