package com.speechgym.reports;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.Locale;

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
            String safeSessionTitle = shortenForPdf(sessionTitle, 72);
            String safeRecommendation = shortenForPdf(firstRecommendation(result), 110);
            try (PDPageContentStream contentStream = new PDPageContentStream(document, page)) {
                contentStream.beginText();
                contentStream.setFont(new PDType1Font(Standard14Fonts.FontName.HELVETICA_BOLD), 16);
                contentStream.newLineAtOffset(50, 780);
                contentStream.showText("SpeechGym Report");
                contentStream.setFont(new PDType1Font(Standard14Fonts.FontName.HELVETICA), 11);
                contentStream.newLineAtOffset(0, -30);
                contentStream.showText("Session: " + safeSessionTitle);
                contentStream.newLineAtOffset(0, -20);
                contentStream.showText("Overall score: " + result.overallScore());
                contentStream.newLineAtOffset(0, -18);
                contentStream.showText("Clarity: " + result.clarity() + ", Pace WPM: " + result.paceWpm());
                contentStream.newLineAtOffset(0, -18);
                contentStream.showText("Confidence: " + result.confidence() + ", Structure: " + result.structureScore());
                contentStream.newLineAtOffset(0, -18);
                contentStream.showText("Tone: " + result.emotionalTone());
                contentStream.newLineAtOffset(0, -18);
                contentStream.showText("Top recommendation: " + safeRecommendation);
                contentStream.endText();
            }
            document.save(outputStream);
            return outputStream.toByteArray();
        }
        catch (IOException exception) {
            throw new IllegalStateException("Unable to generate PDF report.", exception);
        }
    }

    private String firstRecommendation(ReportGenerationResult result) {
        if (result.recommendations() == null || result.recommendations().isEmpty()) {
            return "See structured recommendations in the application.";
        }
        return result.recommendations().getFirst();
    }

    private String shortenForPdf(String value, int maxLength) {
        String safeValue = toPdfSafeText(value);
        if (safeValue.length() <= maxLength) {
            return safeValue;
        }
        return safeValue.substring(0, Math.max(0, maxLength - 3)).trim() + "...";
    }

    private String toPdfSafeText(String value) {
        if (value == null || value.isBlank()) {
            return "n/a";
        }
        StringBuilder builder = new StringBuilder();
        for (char character : value.replaceAll("\\s+", " ").trim().toCharArray()) {
            if (character >= 32 && character <= 126) {
                builder.append(character);
                continue;
            }
            builder.append(transliterate(character));
        }
        String normalized = builder.toString().replaceAll("\\s+", " ").trim();
        return normalized.isBlank() ? "n/a" : normalized;
    }

    private String transliterate(char character) {
        return switch (Character.toLowerCase(character)) {
            case 'а' -> preserveCase(character, "a");
            case 'б' -> preserveCase(character, "b");
            case 'в' -> preserveCase(character, "v");
            case 'г' -> preserveCase(character, "g");
            case 'д' -> preserveCase(character, "d");
            case 'е' -> preserveCase(character, "e");
            case 'ё' -> preserveCase(character, "e");
            case 'ж' -> preserveCase(character, "zh");
            case 'з' -> preserveCase(character, "z");
            case 'и' -> preserveCase(character, "i");
            case 'й' -> preserveCase(character, "y");
            case 'к' -> preserveCase(character, "k");
            case 'л' -> preserveCase(character, "l");
            case 'м' -> preserveCase(character, "m");
            case 'н' -> preserveCase(character, "n");
            case 'о' -> preserveCase(character, "o");
            case 'п' -> preserveCase(character, "p");
            case 'р' -> preserveCase(character, "r");
            case 'с' -> preserveCase(character, "s");
            case 'т' -> preserveCase(character, "t");
            case 'у' -> preserveCase(character, "u");
            case 'ф' -> preserveCase(character, "f");
            case 'х' -> preserveCase(character, "kh");
            case 'ц' -> preserveCase(character, "ts");
            case 'ч' -> preserveCase(character, "ch");
            case 'ш' -> preserveCase(character, "sh");
            case 'щ' -> preserveCase(character, "sch");
            case 'ъ' -> "";
            case 'ы' -> preserveCase(character, "y");
            case 'ь' -> "";
            case 'э' -> preserveCase(character, "e");
            case 'ю' -> preserveCase(character, "yu");
            case 'я' -> preserveCase(character, "ya");
            default -> " ";
        };
    }

    private String preserveCase(char sourceCharacter, String latin) {
        if (!Character.isUpperCase(sourceCharacter) || latin.isBlank()) {
            return latin;
        }
        if (latin.length() == 1) {
            return latin.toUpperCase(Locale.ROOT);
        }
        return Character.toUpperCase(latin.charAt(0)) + latin.substring(1);
    }
}
