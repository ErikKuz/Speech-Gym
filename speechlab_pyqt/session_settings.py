import re

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from styles import BTN_OUTLINE, BTN_PRIMARY, C, COMBOBOX_STYLE, INPUT_STYLE, TEXTAREA_STYLE
from widgets import Card, make_label, show_toast


LANGUAGE_OPTIONS = [
    ("English", "en"),
    ("Spanish", "es"),
    ("French", "fr"),
    ("German", "de"),
    ("Mandarin", "zh"),
]

AUDIENCE_OPTIONS = [
    "Executive/C-Suite",
    "Team/Colleagues",
    "Conference/Public",
    "Investors",
    "Students/Academic",
]

STYLE_OPTIONS = [
    "Professional",
    "Conversational",
    "Motivational",
    "Educational",
    "Persuasive",
]

DEFAULT_AUDIENCE = "General audience"
DEFAULT_STYLE = "General"
DEFAULT_DIFFICULTY = "INTERMEDIATE"
DEFAULT_COACHING = "BALANCED"

_LANGUAGE_LABELS_BY_CODE = {code: label for label, code in LANGUAGE_OPTIONS}
_LANGUAGE_CODES_BY_LABEL = {label: code for label, code in LANGUAGE_OPTIONS}


def parse_duration_seconds(text: str) -> int:
    match = re.search(r"\d+", text or "")
    minutes = int(match.group(0)) if match else 15
    return max(30, min(minutes * 60, 7200))


def format_duration_text(seconds) -> str:
    try:
        total_seconds = int(seconds or 0)
    except (TypeError, ValueError):
        total_seconds = 0
    minutes = max(1, round(total_seconds / 60)) if total_seconds else 15
    unit = "minute" if minutes == 1 else "minutes"
    return f"{minutes} {unit}"


def language_code_for_label(label: str) -> str:
    return _LANGUAGE_CODES_BY_LABEL.get(label or "", "en")


def language_label_for_code(code: str) -> str:
    return _LANGUAGE_LABELS_BY_CODE.get((code or "").strip().lower(), "English")


def build_session_payload_from_form(
    *,
    title: str,
    goal: str,
    language_label: str,
    audience_type: str,
    duration_text: str,
    presentation_style: str,
    notes: str,
    difficulty_level: str = DEFAULT_DIFFICULTY,
    coaching_mode: str = DEFAULT_COACHING,
) -> dict:
    clean_title = (title or "").strip()
    clean_goal = (goal or "").strip()
    clean_audience = (audience_type or "").strip() or DEFAULT_AUDIENCE
    clean_style = (presentation_style or "").strip() or DEFAULT_STYLE

    return {
        "title": clean_title,
        "goal": clean_goal,
        "scenario": (clean_goal or clean_title)[:100],
        "languageCode": language_code_for_label(language_label),
        "audienceType": clean_audience[:100],
        "durationTargetSeconds": parse_duration_seconds(duration_text),
        "presentationStyle": clean_style[:100],
        "notes": (notes or "").strip(),
        "difficultyLevel": difficulty_level,
        "coachingMode": coaching_mode,
    }


def session_prompt_signature(session: dict | None) -> tuple:
    data = session or {}
    return (
        data.get("title") or "",
        data.get("goal") or "",
        data.get("scenario") or "",
        data.get("languageCode") or "",
        data.get("audienceType") or "",
        int(data.get("durationTargetSeconds") or 0),
        data.get("presentationStyle") or "",
        data.get("notes") or "",
        data.get("difficultyLevel") or "",
        data.get("coachingMode") or "",
    )


def session_prompt_text(session: dict | None) -> str:
    data = session or {}
    if not data:
        return ""

    title = (data.get("title") or "").strip()
    goal = (data.get("goal") or "").strip()
    scenario = (data.get("scenario") or "").strip()
    notes = (data.get("notes") or "").strip()
    duration = format_duration_text(data.get("durationTargetSeconds"))
    audience = (data.get("audienceType") or DEFAULT_AUDIENCE).strip()
    style = (data.get("presentationStyle") or DEFAULT_STYLE).strip()
    language = language_label_for_code(data.get("languageCode"))

    lines = ["Project settings:"]
    if title:
        lines.append(f"Title: {title}")
    if goal:
        lines.append(f"Goal: {goal}")
    elif scenario:
        lines.append(f"Scenario: {scenario}")
    lines.append(f"Language: {language}")
    lines.append(f"Audience: {audience}")
    lines.append(f"Target duration: {duration}")
    lines.append(f"Style: {style}")
    if notes:
        lines.append(f"Notes: {notes}")
    return "\n".join(lines)


class SessionSettingsDialog(QDialog):
    def __init__(self, parent=None, session: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Edit Project Settings")
        self.setModal(True)
        self.resize(760, 0)
        self.setStyleSheet(f"background: {C['white']};")
        self._build()
        if session:
            self.load_session(session)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 24)
        root.setSpacing(18)

        root.addWidget(make_label("Edit Project Settings", size=22, weight=QFont.Bold, color=C["slate_900"]))
        root.addWidget(make_label(
            "Update the rehearsal context that will be used for the next recording in this chat project.",
            size=14,
            color=C["slate_600"],
            wrap=True,
        ))

        form_card = Card(radius=16)
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(28, 28, 28, 28)
        form_layout.setSpacing(18)

        form_layout.addWidget(make_label("Rehearsal Title *", size=14, weight=QFont.Medium, color=C["slate_700"]))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g., Q4 Sales Presentation")
        self.title_input.setStyleSheet(INPUT_STYLE)
        self.title_input.setFixedHeight(44)
        form_layout.addWidget(self.title_input)

        form_layout.addWidget(make_label("Goal / Scenario", size=14, weight=QFont.Medium, color=C["slate_700"]))
        self.goal_input = QLineEdit()
        self.goal_input.setPlaceholderText("e.g., Executive board meeting, Conference keynote")
        self.goal_input.setStyleSheet(INPUT_STYLE)
        self.goal_input.setFixedHeight(44)
        form_layout.addWidget(self.goal_input)

        first_row = QHBoxLayout()
        first_row.setSpacing(16)

        lang_col = QVBoxLayout()
        lang_col.setSpacing(8)
        lang_col.addWidget(make_label("Language", size=14, weight=QFont.Medium, color=C["slate_700"]))
        self.lang_combo = QComboBox()
        for label, code in LANGUAGE_OPTIONS:
            self.lang_combo.addItem(label, code)
        self.lang_combo.setStyleSheet(COMBOBOX_STYLE)
        lang_col.addWidget(self.lang_combo)
        first_row.addLayout(lang_col)

        duration_col = QVBoxLayout()
        duration_col.setSpacing(8)
        duration_col.addWidget(make_label("Target Duration", size=14, weight=QFont.Medium, color=C["slate_700"]))
        self.duration_input = QLineEdit()
        self.duration_input.setPlaceholderText("e.g., 15 minutes")
        self.duration_input.setStyleSheet(INPUT_STYLE)
        self.duration_input.setFixedHeight(44)
        duration_col.addWidget(self.duration_input)
        first_row.addLayout(duration_col)

        form_layout.addLayout(first_row)

        second_row = QHBoxLayout()
        second_row.setSpacing(16)

        audience_col = QVBoxLayout()
        audience_col.setSpacing(8)
        audience_col.addWidget(make_label("Audience Type", size=14, weight=QFont.Medium, color=C["slate_700"]))
        self.audience_combo = QComboBox()
        self.audience_combo.addItem("Select audience", "")
        for item in AUDIENCE_OPTIONS:
            self.audience_combo.addItem(item)
        self.audience_combo.setStyleSheet(COMBOBOX_STYLE)
        audience_col.addWidget(self.audience_combo)
        second_row.addLayout(audience_col)

        style_col = QVBoxLayout()
        style_col.setSpacing(8)
        style_col.addWidget(make_label("Speaking Style / Tone", size=14, weight=QFont.Medium, color=C["slate_700"]))
        self.style_combo = QComboBox()
        self.style_combo.addItem("Select style", "")
        for item in STYLE_OPTIONS:
            self.style_combo.addItem(item)
        self.style_combo.setStyleSheet(COMBOBOX_STYLE)
        style_col.addWidget(self.style_combo)
        second_row.addLayout(style_col)

        form_layout.addLayout(second_row)

        form_layout.addWidget(make_label("Additional Notes (Optional)", size=14, weight=QFont.Medium, color=C["slate_700"]))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText(
            "Any specific areas you'd like feedback on, concerns, or context..."
        )
        self.notes_input.setStyleSheet(TEXTAREA_STYLE)
        self.notes_input.setFixedHeight(110)
        form_layout.addWidget(self.notes_input)

        root.addWidget(form_card)

        button_row = QHBoxLayout()
        button_row.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet(BTN_OUTLINE)
        cancel_button.setFixedHeight(42)
        cancel_button.setMinimumWidth(130)
        cancel_button.clicked.connect(self.reject)
        button_row.addWidget(cancel_button)

        save_button = QPushButton("Save Settings")
        save_button.setStyleSheet(BTN_PRIMARY)
        save_button.setFixedHeight(42)
        save_button.setMinimumWidth(150)
        save_button.clicked.connect(self.accept)
        button_row.addWidget(save_button)

        root.addLayout(button_row)

    def load_session(self, session: dict):
        self.title_input.setText((session.get("title") or "").strip())
        self.goal_input.setText((session.get("goal") or "").strip())
        self.notes_input.setPlainText((session.get("notes") or "").strip())
        self.duration_input.setText(format_duration_text(session.get("durationTargetSeconds")))

        language_index = self.lang_combo.findData((session.get("languageCode") or "en").strip().lower())
        self.lang_combo.setCurrentIndex(max(language_index, 0))

        audience = (session.get("audienceType") or DEFAULT_AUDIENCE).strip()
        audience_index = self.audience_combo.findText(audience, Qt.MatchFixedString)
        if audience_index < 0:
            self.audience_combo.addItem(audience)
            audience_index = self.audience_combo.count() - 1
        self.audience_combo.setCurrentIndex(audience_index)

        style = (session.get("presentationStyle") or DEFAULT_STYLE).strip()
        style_index = self.style_combo.findText(style, Qt.MatchFixedString)
        if style_index < 0:
            self.style_combo.addItem(style)
            style_index = self.style_combo.count() - 1
        self.style_combo.setCurrentIndex(style_index)

    def payload(self) -> dict:
        audience = self.audience_combo.currentText()
        style = self.style_combo.currentText()
        if self.audience_combo.currentData() == "":
            audience = DEFAULT_AUDIENCE
        if self.style_combo.currentData() == "":
            style = DEFAULT_STYLE

        return build_session_payload_from_form(
            title=self.title_input.text(),
            goal=self.goal_input.text(),
            language_label=self.lang_combo.currentText(),
            audience_type=audience,
            duration_text=self.duration_input.text(),
            presentation_style=style,
            notes=self.notes_input.toPlainText(),
        )

    def accept(self):
        if not self.title_input.text().strip():
            show_toast(self, "Please enter a rehearsal title", "error")
            return
        super().accept()
