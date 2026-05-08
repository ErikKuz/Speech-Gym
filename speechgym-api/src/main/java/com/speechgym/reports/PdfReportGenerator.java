package com.speechgym.reports;

import java.awt.Color;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.PDPageContentStream;
import org.apache.pdfbox.pdmodel.common.PDRectangle;
import org.apache.pdfbox.pdmodel.font.PDFont;
import org.apache.pdfbox.pdmodel.font.PDType0Font;
import org.apache.pdfbox.pdmodel.font.PDType1Font;
import org.apache.pdfbox.pdmodel.font.Standard14Fonts;
import org.springframework.stereotype.Service;

@Service
public class PdfReportGenerator {
    private static final PDRectangle PAGE_SIZE = PDRectangle.A4;
    private static final float PAGE_WIDTH = PAGE_SIZE.getWidth();
    private static final float PAGE_HEIGHT = PAGE_SIZE.getHeight();
    private static final float MARGIN = 42f;
    private static final float CONTENT_WIDTH = PAGE_WIDTH - (MARGIN * 2f);
    private static final float BOTTOM_MARGIN = 46f;
    private static final DateTimeFormatter DATE_FORMAT = DateTimeFormatter.ofPattern("dd.MM.yyyy");

    private static final Color WHITE = Color.WHITE;
    private static final Color SLATE_50 = new Color(248, 250, 252);
    private static final Color SLATE_100 = new Color(241, 245, 249);
    private static final Color SLATE_200 = new Color(226, 232, 240);
    private static final Color SLATE_500 = new Color(100, 116, 139);
    private static final Color SLATE_600 = new Color(71, 85, 105);
    private static final Color SLATE_700 = new Color(51, 65, 85);
    private static final Color SLATE_900 = new Color(15, 23, 42);
    private static final Color INDIGO_50 = new Color(238, 242, 255);
    private static final Color INDIGO_200 = new Color(199, 210, 254);
    private static final Color INDIGO_600 = new Color(79, 70, 229);
    private static final Color GREEN_50 = new Color(240, 253, 244);
    private static final Color GREEN_200 = new Color(187, 247, 208);
    private static final Color GREEN_700 = new Color(21, 128, 61);
    private static final Color AMBER_50 = new Color(255, 251, 235);
    private static final Color AMBER_200 = new Color(253, 230, 138);
    private static final Color AMBER_700 = new Color(180, 83, 9);
    private static final Color RED_50 = new Color(254, 242, 242);
    private static final Color RED_200 = new Color(254, 202, 202);
    private static final Color RED_700 = new Color(185, 28, 28);
    private static final Color VIOLET_50 = new Color(245, 243, 255);
    private static final Color VIOLET_200 = new Color(221, 214, 254);
    private static final Color VIOLET_700 = new Color(109, 40, 217);

    public byte[] generate(String sessionTitle, ReportGenerationResult result) {
        return generate(sessionTitle, result, null);
    }

    public byte[] generate(String sessionTitle, ReportGenerationResult result, ReportAnalysisResponse analysis) {
        try (PDDocument document = new PDDocument();
             ByteArrayOutputStream outputStream = new ByteArrayOutputStream()) {
            PdfFonts fonts = loadFonts(document);
            ReportPdfWriter writer = new ReportPdfWriter(document, fonts);
            writer.render(sessionTitle, result, analysis);
            document.save(outputStream);
            return outputStream.toByteArray();
        }
        catch (IOException exception) {
            throw new IllegalStateException("Unable to generate PDF report.", exception);
        }
    }

    private PdfFonts loadFonts(PDDocument document) {
        for (FontCandidate candidate : fontCandidates()) {
            if (!Files.isRegularFile(candidate.regular())) {
                continue;
            }
            try {
                PDFont regular = loadUnicodeFont(document, candidate.regular());
                PDFont bold = Files.isRegularFile(candidate.bold())
                    ? loadUnicodeFont(document, candidate.bold())
                    : regular;
                return new PdfFonts(regular, bold, true);
            }
            catch (IOException ignored) {
                // Try the next known system font path.
            }
        }

        return new PdfFonts(
            new PDType1Font(Standard14Fonts.FontName.HELVETICA),
            new PDType1Font(Standard14Fonts.FontName.HELVETICA_BOLD),
            false
        );
    }

    private PDFont loadUnicodeFont(PDDocument document, Path path) throws IOException {
        try (InputStream inputStream = Files.newInputStream(path)) {
            return PDType0Font.load(document, inputStream, true);
        }
    }

    private List<FontCandidate> fontCandidates() {
        return List.of(
            new FontCandidate(Path.of("C:\\Windows\\Fonts\\arial.ttf"), Path.of("C:\\Windows\\Fonts\\arialbd.ttf")),
            new FontCandidate(Path.of("C:\\Windows\\Fonts\\segoeui.ttf"), Path.of("C:\\Windows\\Fonts\\segoeuib.ttf")),
            new FontCandidate(Path.of("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"), Path.of("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")),
            new FontCandidate(Path.of("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"), Path.of("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf")),
            new FontCandidate(Path.of("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"), Path.of("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"))
        );
    }

    private record FontCandidate(Path regular, Path bold) {
    }

    private record PdfFonts(PDFont regular, PDFont bold, boolean unicode) {
        String safeText(String value) {
            if (value == null || value.isBlank()) {
                return "";
            }
            String normalized = value.replaceAll("\\s+", " ").trim();
            return unicode ? normalized : transliterate(normalized);
        }
    }

    private static class ReportPdfWriter {
        private final PDDocument document;
        private final PdfFonts fonts;
        private PDPage page;
        private PDPageContentStream stream;
        private float y;
        private int pageNumber;

        ReportPdfWriter(PDDocument document, PdfFonts fonts) {
            this.document = document;
            this.fonts = fonts;
        }

        void render(String sessionTitle, ReportGenerationResult result, ReportAnalysisResponse analysis) throws IOException {
            startPage();
            renderHero(sessionTitle);
            renderPassport(result, analysis);
            renderNextVersion(analysis);
            renderRecommendations(result, analysis);
            closePage();
        }

        private void renderHero(String sessionTitle) throws IOException {
            float height = 126f;
            ensureSpace(height + 16f);
            drawPanel(MARGIN, y - height, CONTENT_WIDTH, height, SLATE_50, SLATE_200);

            writeText("SpeechGym", MARGIN + 20f, y - 26f, 10f, fonts.bold(), SLATE_500);
            writeText("Разбор текущей версии питча", MARGIN + 20f, y - 50f, 20f, fonts.bold(), SLATE_900);
            writeWrapped(
                "Что исправить перед следующим выступлением",
                MARGIN + 20f,
                y - 70f,
                CONTENT_WIDTH - 40f,
                11f,
                fonts.regular(),
                SLATE_600,
                14f
            );

            writeText("Сформировано " + LocalDate.now().format(DATE_FORMAT), MARGIN + 20f, y - 106f, 9f, fonts.regular(), SLATE_500);
            y -= height + 18f;
        }

        private void renderPassport(ReportGenerationResult result, ReportAnalysisResponse analysis) throws IOException {
            ReportAnalysisResponse.Meta meta = meta(analysis);
            ReportAnalysisResponse.PassportPitch passport = passport(analysis);

            sectionTitle("Паспорт питча");

            List<MetricCard> cards = List.of(
                new MetricCard("Лимит времени", durationLabel(meta.targetDurationSec()), INDIGO_600),
                new MetricCard("Текущая длина", actualDurationLabel(meta), AMBER_700)
            );
            renderMetricCards(cards);

            renderBanner(statusLabel(passport, result), statusSummary(passport, result), INDIGO_50, INDIGO_200, INDIGO_600);

            renderListCard("Что уже сильное", nonEmpty(passport.strengths(), result.strengths()), GREEN_50, GREEN_200, GREEN_700);
            renderListCard("Что мешает сейчас", nonEmpty(passport.blockers(), result.improvements()), AMBER_50, AMBER_200, AMBER_700);
            renderListCard("Что изменится в следующей версии", passport.nextVersionChanges(), INDIGO_50, INDIGO_200, INDIGO_600);
        }

        private void renderNextVersion(ReportAnalysisResponse analysis) throws IOException {
            ReportAnalysisResponse.NextPitch nextPitch = nextPitch(analysis);
            List<ReportAnalysisResponse.NextPitchBlock> blocks = nextPitch.blocks();
            if ((blocks == null || blocks.isEmpty()) && !blank(nextPitch.fullText())) {
                blocks = List.of(new ReportAnalysisResponse.NextPitchBlock(
                    fallback(nextPitch.title(), "Следующая версия pitch"),
                    nextPitch.fullText()
                ));
            }
            if (blocks == null || blocks.isEmpty()) {
                return;
            }

            sectionTitle("Следующая версия");
            for (ReportAnalysisResponse.NextPitchBlock block : blocks) {
                renderTextBlock(fallback(block.label(), "Блок"), block.text(), SLATE_50, SLATE_200, SLATE_900);
            }
        }

        private void renderRecommendations(ReportGenerationResult result, ReportAnalysisResponse analysis) throws IOException {
            ReportAnalysisResponse.Recommendations recommendations = recommendations(analysis);
            List<String> summary = nonEmpty(recommendations.summary(), result.recommendations());
            List<ReportAnalysisResponse.RecommendationChange> changes = recommendations.changes();

            if (summary.isEmpty() && changes.isEmpty()) {
                return;
            }

            sectionTitle("Рекомендации");
            renderListCard("Главные улучшения", summary, VIOLET_50, VIOLET_200, VIOLET_700);

            for (ReportAnalysisResponse.RecommendationChange change : changes) {
                renderRecommendationChange(change);
            }
        }

        private void renderMetricCards(List<MetricCard> cards) throws IOException {
            float gap = 8f;
            float cardWidth = (CONTENT_WIDTH - gap * (cards.size() - 1)) / cards.size();
            float height = 58f;
            ensureSpace(height + 12f);
            float x = MARGIN;
            for (MetricCard card : cards) {
                drawPanel(x, y - height, cardWidth, height, WHITE, SLATE_200);
                writeText(card.label(), x + 12f, y - 18f, 8.5f, fonts.bold(), SLATE_500);
                writeWrapped(card.value(), x + 12f, y - 34f, cardWidth - 24f, 12f, fonts.bold(), card.color(), 14f);
                x += cardWidth + gap;
            }
            y -= height + 14f;
        }

        private void renderBanner(String pill, String body, Color bg, Color border, Color accent) throws IOException {
            float headerHeight = 32f;
            float bodyTopOffset = headerHeight + 22f;
            float bodyHeight = wrappedHeight(body, CONTENT_WIDTH - 40f, 10.5f, fonts.regular(), 13f);
            float height = Math.max(94f, bodyTopOffset + bodyHeight + 16f);
            ensureSpace(height + 12f);
            drawPanel(MARGIN, y - height, CONTENT_WIDTH, height, bg, border);
            drawPanel(MARGIN, y - headerHeight, CONTENT_WIDTH, headerHeight, accent, accent);
            writeText(pill, MARGIN + 18f, y - 20f, 10f, fonts.bold(), WHITE);
            writeWrapped(body, MARGIN + 18f, y - bodyTopOffset, CONTENT_WIDTH - 36f, 10.5f, fonts.regular(), SLATE_700, 13f);
            y -= height + 14f;
        }

        private void renderListCard(String title, List<String> items, Color bg, Color border, Color accent) throws IOException {
            List<String> values = cleanList(items);
            if (values.isEmpty()) {
                return;
            }
            float height = 44f;
            for (String item : values) {
                height += Math.max(18f, wrappedHeight(item, CONTENT_WIDTH - 70f, 10f, fonts.regular(), 13f)) + 8f;
            }
            ensureSpace(height + 12f);
            drawPanel(MARGIN, y - height, CONTENT_WIDTH, height, bg, border);
            writeText(title, MARGIN + 18f, y - 24f, 14f, fonts.bold(), SLATE_900);
            float cursor = y - 48f;
            for (String item : values) {
                drawCircle(MARGIN + 24f, cursor + 4f, 2.6f, accent);
                float used = writeWrapped(item, MARGIN + 38f, cursor, CONTENT_WIDTH - 56f, 10f, fonts.regular(), SLATE_700, 13f);
                cursor -= Math.max(18f, used) + 8f;
            }
            y -= height + 14f;
        }

        private void renderTextBlock(String title, String text, Color bg, Color border, Color accent) throws IOException {
            String safeText = fallback(text, "");
            if (safeText.isBlank()) {
                return;
            }
            float textHeight = wrappedHeight(safeText, CONTENT_WIDTH - 36f, 10f, fonts.regular(), 13f);
            float height = Math.max(84f, textHeight + 58f);
            ensureSpace(height + 12f);
            drawPanel(MARGIN, y - height, CONTENT_WIDTH, height, WHITE, border);
            drawPanel(MARGIN, y - 34f, CONTENT_WIDTH, 34f, bg, border);
            writeText(title, MARGIN + 16f, y - 22f, 12f, fonts.bold(), accent);
            writeWrapped(safeText, MARGIN + 18f, y - 54f, CONTENT_WIDTH - 36f, 10f, fonts.regular(), SLATE_700, 13f);
            y -= height + 14f;
        }

        private void renderRecommendationChange(ReportAnalysisResponse.RecommendationChange change) throws IOException {
            String title = fallback(change.title(), "Изменение");
            float halfWidth = (CONTENT_WIDTH - 10f) / 2f;
            float beforeHeight = quoteHeight(change.before(), halfWidth);
            float afterHeight = quoteHeight(change.after(), halfWidth);
            float whyHeight = textPanelHeight(change.whyBeforeWeaker(), halfWidth);
            float betterHeight = textPanelHeight(change.whyAfterBetter(), halfWidth);
            float effectHeight = textPanelHeight(effect(change).understandsBetter(), halfWidth);
            float feelsHeight = textPanelHeight(effect(change).feelsMore(), halfWidth);
            float height = 48f
                + Math.max(beforeHeight, afterHeight)
                + Math.max(whyHeight, betterHeight)
                + Math.max(effectHeight, feelsHeight)
                + 34f;

            ensureSpace(height + 14f);
            drawPanel(MARGIN, y - height, CONTENT_WIDTH, height, WHITE, SLATE_200);
            drawPanel(MARGIN, y - 34f, CONTENT_WIDTH, 34f, INDIGO_600, INDIGO_600);
            writeText(title, MARGIN + 16f, y - 22f, 12f, fonts.bold(), WHITE);

            float cursor = y - 48f;
            float rowHeight = Math.max(beforeHeight, afterHeight);
            renderSmallPanel("Было", change.before(), MARGIN + 14f, cursor, halfWidth, rowHeight, RED_50, RED_200, RED_700, true);
            renderSmallPanel("Стало", change.after(), MARGIN + 24f + halfWidth, cursor, halfWidth, rowHeight, GREEN_50, GREEN_200, GREEN_700, true);
            cursor -= rowHeight + 10f;

            rowHeight = Math.max(whyHeight, betterHeight);
            renderSmallPanel("Почему старая версия слабее", change.whyBeforeWeaker(), MARGIN + 14f, cursor, halfWidth, rowHeight, AMBER_50, AMBER_200, AMBER_700, false);
            renderSmallPanel("Почему новая версия лучше", change.whyAfterBetter(), MARGIN + 24f + halfWidth, cursor, halfWidth, rowHeight, GREEN_50, GREEN_200, GREEN_700, false);
            cursor -= rowHeight + 10f;

            rowHeight = Math.max(effectHeight, feelsHeight);
            renderSmallPanel("Что аудитория понимает", effect(change).understandsBetter(), MARGIN + 14f, cursor, halfWidth, rowHeight, INDIGO_50, INDIGO_200, INDIGO_600, false);
            renderSmallPanel("Что аудитория чувствует", effect(change).feelsMore(), MARGIN + 24f + halfWidth, cursor, halfWidth, rowHeight, VIOLET_50, VIOLET_200, VIOLET_700, false);

            y -= height + 14f;
        }

        private void renderSmallPanel(
            String title,
            String text,
            float x,
            float top,
            float width,
            float height,
            Color bg,
            Color border,
            Color accent,
            boolean quote
        ) throws IOException {
            drawPanel(x, top - height, width, height, bg, border);
            writeText(title, x + 10f, top - 16f, 8.5f, fonts.bold(), accent);
            String body = quote && !blank(text) ? "\"" + text + "\"" : fallback(text, "");
            writeWrapped(body, x + 10f, top - 32f, width - 20f, 9.2f, fonts.regular(), SLATE_700, 12f);
        }

        private void sectionTitle(String title) throws IOException {
            ensureSpace(40f);
            writeText(title, MARGIN, y - 12f, 15f, fonts.bold(), SLATE_900);
            line(MARGIN, y - 22f, MARGIN + CONTENT_WIDTH, y - 22f, SLATE_200, 0.8f);
            y -= 36f;
        }

        private void startPage() throws IOException {
            page = new PDPage(PAGE_SIZE);
            document.addPage(page);
            pageNumber++;
            stream = new PDPageContentStream(document, page);
            y = PAGE_HEIGHT - MARGIN;
        }

        private void closePage() throws IOException {
            if (stream == null) {
                return;
            }
            renderFooter();
            stream.close();
            stream = null;
        }

        private void ensureSpace(float needed) throws IOException {
            if (y - needed >= BOTTOM_MARGIN) {
                return;
            }
            closePage();
            startPage();
        }

        private void renderFooter() throws IOException {
            line(MARGIN, 34f, MARGIN + CONTENT_WIDTH, 34f, SLATE_200, 0.6f);
            writeText("Сформировано SpeechGym AI", MARGIN, 22f, 8.5f, fonts.regular(), SLATE_500);
            writeText("Страница " + pageNumber, MARGIN + CONTENT_WIDTH - 60f, 22f, 8.5f, fonts.regular(), SLATE_500);
        }

        private void drawPanel(float x, float yBottom, float width, float height, Color fill, Color stroke) throws IOException {
            stream.setNonStrokingColor(fill);
            stream.addRect(x, yBottom, width, height);
            stream.fill();
            stream.setStrokingColor(stroke);
            stream.setLineWidth(0.8f);
            stream.addRect(x, yBottom, width, height);
            stream.stroke();
        }

        private void drawCircle(float centerX, float centerY, float radius, Color fill) throws IOException {
            float magic = radius * 0.55228475f;
            stream.setNonStrokingColor(fill);
            stream.moveTo(centerX + radius, centerY);
            stream.curveTo(centerX + radius, centerY + magic, centerX + magic, centerY + radius, centerX, centerY + radius);
            stream.curveTo(centerX - magic, centerY + radius, centerX - radius, centerY + magic, centerX - radius, centerY);
            stream.curveTo(centerX - radius, centerY - magic, centerX - magic, centerY - radius, centerX, centerY - radius);
            stream.curveTo(centerX + magic, centerY - radius, centerX + radius, centerY - magic, centerX + radius, centerY);
            stream.fill();
        }

        private void line(float x1, float y1, float x2, float y2, Color color, float width) throws IOException {
            stream.setStrokingColor(color);
            stream.setLineWidth(width);
            stream.moveTo(x1, y1);
            stream.lineTo(x2, y2);
            stream.stroke();
        }

        private void writeText(String text, float x, float baseline, float size, PDFont font, Color color) throws IOException {
            String safeText = fonts.safeText(text);
            if (safeText.isBlank()) {
                return;
            }
            stream.beginText();
            stream.setNonStrokingColor(color);
            stream.setFont(font, size);
            stream.newLineAtOffset(x, baseline);
            stream.showText(safeText);
            stream.endText();
        }

        private float writeWrapped(String text, float x, float top, float width, float size, PDFont font, Color color, float leading) throws IOException {
            List<String> lines = wrap(text, width, size, font);
            float cursor = top;
            for (String line : lines) {
                writeText(line, x, cursor, size, font, color);
                cursor -= leading;
            }
            return Math.max(leading, lines.size() * leading);
        }

        private List<String> wrap(String text, float width, float size, PDFont font) throws IOException {
            String safeText = fonts.safeText(text);
            if (safeText.isBlank()) {
                return List.of("");
            }

            List<String> lines = new ArrayList<>();
            for (String paragraph : safeText.split("\\n+")) {
                String[] words = paragraph.replaceAll("\\s+", " ").trim().split(" ");
                StringBuilder line = new StringBuilder();
                for (String word : words) {
                    String candidate = line.isEmpty() ? word : line + " " + word;
                    if (textWidth(candidate, size, font) <= width) {
                        line = new StringBuilder(candidate);
                        continue;
                    }
                    if (!line.isEmpty()) {
                        lines.add(line.toString());
                    }
                    line = new StringBuilder(word);
                }
                if (!line.isEmpty()) {
                    lines.add(line.toString());
                }
            }
            return lines.isEmpty() ? List.of("") : lines;
        }

        private float wrappedHeight(String text, float width, float size, PDFont font, float leading) throws IOException {
            return Math.max(leading, wrap(text, width, size, font).size() * leading);
        }

        private float quoteHeight(String text, float width) throws IOException {
            return Math.max(58f, wrappedHeight(text, width - 20f, 9.2f, fonts.regular(), 12f) + 34f);
        }

        private float textPanelHeight(String text, float width) throws IOException {
            return Math.max(58f, wrappedHeight(text, width - 20f, 9.2f, fonts.regular(), 12f) + 34f);
        }

        private float textWidth(String text, float size, PDFont font) throws IOException {
            return font.getStringWidth(fonts.safeText(text)) / 1000f * size;
        }

        private ReportAnalysisResponse.Meta meta(ReportAnalysisResponse analysis) {
            return analysis == null ? new ReportAnalysisResponse.Meta(null, null, null, null, null, null, null, null) : analysis.meta();
        }

        private ReportAnalysisResponse.PassportPitch passport(ReportAnalysisResponse analysis) {
            return analysis == null ? new ReportAnalysisResponse.PassportPitch(null, null, null) : analysis.report().passportPitch();
        }

        private ReportAnalysisResponse.NextPitch nextPitch(ReportAnalysisResponse analysis) {
            return analysis == null ? new ReportAnalysisResponse.NextPitch(null, null, null) : analysis.report().nextPitch();
        }

        private ReportAnalysisResponse.Recommendations recommendations(ReportAnalysisResponse analysis) {
            return analysis == null ? new ReportAnalysisResponse.Recommendations(null, null) : analysis.report().recommendations();
        }

        private ReportAnalysisResponse.AudienceEffect effect(ReportAnalysisResponse.RecommendationChange change) {
            return change.audienceEffect() == null ? new ReportAnalysisResponse.AudienceEffect(null, null) : change.audienceEffect();
        }

        private String durationLabel(Integer seconds) {
            if (seconds == null || seconds <= 0) {
                return "n/a";
            }
            int minutes = Math.max(1, Math.round(seconds / 60.0f));
            return minutes + " мин";
        }

        private String actualDurationLabel(ReportAnalysisResponse.Meta meta) {
            if (!blank(meta.actualDuration())) {
                return meta.actualDuration();
            }
            if (meta.actualDurationSec() == null || meta.actualDurationSec() <= 0.0d) {
                return "n/a";
            }
            int totalSeconds = Math.max(1, (int) Math.round(meta.actualDurationSec()));
            return (totalSeconds / 60) + ":" + String.format(Locale.ROOT, "%02d", totalSeconds % 60);
        }

        private String statusLabel(ReportAnalysisResponse.PassportPitch passport, ReportGenerationResult result) {
            List<String> blockers = nonEmpty(passport.blockers(), result.improvements());
            List<String> strengths = nonEmpty(passport.strengths(), result.strengths());
            if (blockers.isEmpty() && !strengths.isEmpty()) {
                return "Готово к финальному прогону";
            }
            if (!strengths.isEmpty() && blockers.size() <= 2) {
                return "Близко к готовому";
            }
            return "Нужна одна сильная итерация";
        }

        private String statusSummary(ReportAnalysisResponse.PassportPitch passport, ReportGenerationResult result) {
            List<String> blockers = nonEmpty(passport.blockers(), result.improvements());
            List<String> strengths = nonEmpty(passport.strengths(), result.strengths());
            if (blockers.isEmpty() && !strengths.isEmpty()) {
                return "Версия уже звучит собранно и уверенно. Следующий шаг - полировка формулировок и более точная подача ключевых тезисов.";
            }
            if (!blockers.isEmpty()) {
                return "Основа уже сильная, но есть несколько мест, которые еще тормозят убедительность. В первую очередь стоит добить: " + blockers.getFirst();
            }
            if (!strengths.isEmpty()) {
                return "В материале уже есть рабочая база, но текущая версия пока не держит одну собранную линию. Сохраняем сильную сторону: " + strengths.getFirst();
            }
            return "Питч уже содержит полезный материал, но пока не собран в одну убедительную историю. Следующая итерация должна сократить лишнее и усилить структуру.";
        }

        private List<String> cleanList(List<String> items) {
            if (items == null) {
                return List.of();
            }
            return items.stream()
                .filter(item -> item != null && !item.isBlank())
                .map(String::trim)
                .toList();
        }

        private List<String> nonEmpty(List<String> primary, List<String> fallback) {
            List<String> primaryClean = cleanList(primary);
            return primaryClean.isEmpty() ? cleanList(fallback) : primaryClean;
        }

        private String fallback(String value, String fallback) {
            return value == null || value.isBlank() ? fallback : value.trim();
        }

        private boolean blank(String value) {
            return value == null || value.isBlank();
        }

        private record MetricCard(String label, String value, Color color) {
        }
    }

    private static String transliterate(String value) {
        StringBuilder builder = new StringBuilder();
        for (char character : value.toCharArray()) {
            if (character >= 32 && character <= 126) {
                builder.append(character);
                continue;
            }
            builder.append(transliterate(character));
        }
        return builder.toString().replaceAll("\\s+", " ").trim();
    }

    private static String transliterate(char character) {
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

    private static String preserveCase(char sourceCharacter, String latin) {
        if (!Character.isUpperCase(sourceCharacter) || latin.isBlank()) {
            return latin;
        }
        if (latin.length() == 1) {
            return latin.toUpperCase(Locale.ROOT);
        }
        return Character.toUpperCase(latin.charAt(0)) + latin.substring(1);
    }
}
