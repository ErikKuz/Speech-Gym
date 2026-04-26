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

from styles import (
    BTN_OUTLINE,
    BTN_PRIMARY,
    C,
    project_combobox_style,
    project_input_style,
    project_textarea_style,
)
from widgets import Card, make_label, show_toast


LANGUAGE_OPTIONS = [
    ("Английский", "en"),
    ("Испанский", "es"),
    ("Французский", "fr"),
    ("Немецкий", "de"),
    ("Китайский", "zh"),
]

AUDIENCE_OPTIONS = [
    "Руководство / C-level",
    "Команда / коллеги",
    "Конференция / широкая аудитория",
    "Инвесторы",
    "Студенты / академическая аудитория",
]

STYLE_OPTIONS = [
    "Профессиональный",
    "Разговорный",
    "Мотивирующий",
    "Обучающий",
    "Убеждающий",
]

DEFAULT_AUDIENCE = "Общая аудитория"
DEFAULT_STYLE = "Общий"
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
    if minutes % 10 == 1 and minutes % 100 != 11:
        unit = "минута"
    elif 2 <= minutes % 10 <= 4 and not 12 <= minutes % 100 <= 14:
        unit = "минуты"
    else:
        unit = "минут"
    return f"{minutes} {unit}"


def language_code_for_label(label: str) -> str:
    return _LANGUAGE_CODES_BY_LABEL.get(label or "", "en")


def language_label_for_code(code: str) -> str:
    return _LANGUAGE_LABELS_BY_CODE.get((code or "").strip().lower(), "Английский")


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


def session_prompt_signature(session: dict | None, *, compact: bool = False) -> tuple:
    data = session or {}
    if compact:
        return (
            data.get("title") or "",
            int(data.get("durationTargetSeconds") or 0),
            data.get("notes") or "",
        )
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


def session_prompt_text(session: dict | None, *, compact: bool = False) -> str:
    data = session or {}
    if not data:
        return ""

    title = (data.get("title") or "").strip()
    notes = (data.get("notes") or "").strip()
    duration = format_duration_text(data.get("durationTargetSeconds"))

    lines = ["Настройки проекта:"]
    if title:
        lines.append(f"Название: {title}")
    lines.append(f"Целевая длительность: {duration}")
    if compact:
        if notes:
            lines.append(f"Заметки: {notes}")
        return "\n".join(lines)

    goal = (data.get("goal") or "").strip()
    scenario = (data.get("scenario") or "").strip()
    audience = (data.get("audienceType") or DEFAULT_AUDIENCE).strip()
    style = (data.get("presentationStyle") or DEFAULT_STYLE).strip()
    language = language_label_for_code(data.get("languageCode"))
    if goal:
        lines.append(f"Цель: {goal}")
    elif scenario:
        lines.append(f"Сценарий: {scenario}")
    lines.append(f"Язык: {language}")
    lines.append(f"Аудитория: {audience}")
    lines.append(f"Стиль: {style}")
    if notes:
        lines.append(f"Заметки: {notes}")
    return "\n".join(lines)


class SessionSettingsDialog(QDialog):
    def __init__(self, parent=None, session: dict | None = None, *, compact: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Изменить настройки проекта")
        self.setModal(True)
        self.resize(760, 0)
        self.setStyleSheet(f"background: {C['white']};")
        self._compact = compact
        self._session_snapshot = dict(session or {})
        self._build()
        if session:
            self.load_session(session)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 24)
        root.setSpacing(18)

        root.addWidget(make_label("Изменить настройки проекта", size=22, weight=QFont.Bold, color=C["slate_900"]))
        root.addWidget(make_label(
            "Обновите контекст выступления, который будет использоваться для следующей записи в этом чат-проекте.",
            size=14,
            color=C["slate_600"],
            wrap=True,
        ))

        form_card = Card(radius=16)
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(28, 28, 28, 28)
        form_layout.setSpacing(18)

        form_layout.addWidget(make_label("Название выступления *", size=14, weight=QFont.Medium, color=C["slate_700"]))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Например: Презентация продаж за 4 квартал")
        self.title_input.setStyleSheet(project_input_style())
        self.title_input.setFixedHeight(44)
        form_layout.addWidget(self.title_input)

        if not self._compact:
            form_layout.addWidget(make_label("Цель / сценарий", size=14, weight=QFont.Medium, color=C["slate_700"]))
            self.goal_input = QLineEdit()
            self.goal_input.setPlaceholderText("Например: заседание совета директоров, выступление на конференции")
            self.goal_input.setStyleSheet(project_input_style())
            self.goal_input.setFixedHeight(44)
            form_layout.addWidget(self.goal_input)

            first_row = QHBoxLayout()
            first_row.setSpacing(16)

            lang_col = QVBoxLayout()
            lang_col.setSpacing(8)
            lang_col.addWidget(make_label("Язык", size=14, weight=QFont.Medium, color=C["slate_700"]))
            self.lang_combo = QComboBox()
            for label, code in LANGUAGE_OPTIONS:
                self.lang_combo.addItem(label, code)
            self.lang_combo.setStyleSheet(project_combobox_style())
            lang_col.addWidget(self.lang_combo)
            first_row.addLayout(lang_col)

            duration_col = QVBoxLayout()
            duration_col.setSpacing(8)
            duration_col.addWidget(make_label("Целевая длительность", size=14, weight=QFont.Medium, color=C["slate_700"]))
            self.duration_input = QLineEdit()
            self.duration_input.setPlaceholderText("Например: 15 минут")
            self.duration_input.setStyleSheet(project_input_style())
            self.duration_input.setFixedHeight(44)
            duration_col.addWidget(self.duration_input)
            first_row.addLayout(duration_col)

            form_layout.addLayout(first_row)

            second_row = QHBoxLayout()
            second_row.setSpacing(16)

            audience_col = QVBoxLayout()
            audience_col.setSpacing(8)
            audience_col.addWidget(make_label("Тип аудитории", size=14, weight=QFont.Medium, color=C["slate_700"]))
            self.audience_combo = QComboBox()
            self.audience_combo.addItem("Выберите аудиторию", "")
            for item in AUDIENCE_OPTIONS:
                self.audience_combo.addItem(item)
            self.audience_combo.setStyleSheet(project_combobox_style())
            audience_col.addWidget(self.audience_combo)
            second_row.addLayout(audience_col)

            style_col = QVBoxLayout()
            style_col.setSpacing(8)
            style_col.addWidget(make_label("Стиль / тон выступления", size=14, weight=QFont.Medium, color=C["slate_700"]))
            self.style_combo = QComboBox()
            self.style_combo.addItem("Выберите стиль", "")
            for item in STYLE_OPTIONS:
                self.style_combo.addItem(item)
            self.style_combo.setStyleSheet(project_combobox_style())
            style_col.addWidget(self.style_combo)
            second_row.addLayout(style_col)

            form_layout.addLayout(second_row)
        else:
            form_layout.addWidget(make_label("Целевая длительность", size=14, weight=QFont.Medium, color=C["slate_700"]))
            self.duration_input = QLineEdit()
            self.duration_input.setPlaceholderText("Например: 15 минут")
            self.duration_input.setStyleSheet(project_input_style())
            self.duration_input.setFixedHeight(44)
            form_layout.addWidget(self.duration_input)

        form_layout.addWidget(make_label("Дополнительные заметки (необязательно)", size=14, weight=QFont.Medium, color=C["slate_700"]))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText(
            "Укажите, на что особенно обратить внимание, какие есть опасения или дополнительный контекст..."
        )
        self.notes_input.setStyleSheet(project_textarea_style())
        self.notes_input.setFixedHeight(110)
        form_layout.addWidget(self.notes_input)

        root.addWidget(form_card)

        button_row = QHBoxLayout()
        button_row.addStretch()

        cancel_button = QPushButton("Отмена")
        cancel_button.setStyleSheet(BTN_OUTLINE)
        cancel_button.setFixedHeight(42)
        cancel_button.setMinimumWidth(130)
        cancel_button.clicked.connect(self.reject)
        button_row.addWidget(cancel_button)

        save_button = QPushButton("Сохранить настройки")
        save_button.setStyleSheet(BTN_PRIMARY)
        save_button.setFixedHeight(42)
        save_button.setMinimumWidth(150)
        save_button.clicked.connect(self.accept)
        button_row.addWidget(save_button)

        root.addLayout(button_row)

    def load_session(self, session: dict):
        self.title_input.setText((session.get("title") or "").strip())
        self.notes_input.setPlainText((session.get("notes") or "").strip())
        self.duration_input.setText(format_duration_text(session.get("durationTargetSeconds")))
        if self._compact:
            return

        self.goal_input.setText((session.get("goal") or "").strip())

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
        if self._compact:
            payload = build_session_payload_from_form(
                title=self.title_input.text(),
                goal=(self._session_snapshot.get("goal") or ""),
                language_label="Английский",
                audience_type=DEFAULT_AUDIENCE,
                duration_text=self.duration_input.text(),
                presentation_style=DEFAULT_STYLE,
                notes=self.notes_input.toPlainText(),
                difficulty_level=(self._session_snapshot.get("difficultyLevel") or DEFAULT_DIFFICULTY),
                coaching_mode=(self._session_snapshot.get("coachingMode") or DEFAULT_COACHING),
            )
            payload["scenario"] = (
                (self._session_snapshot.get("scenario") or payload["scenario"] or payload["title"])[:100]
            )
            payload["languageCode"] = (self._session_snapshot.get("languageCode") or "en").strip()
            payload["audienceType"] = (
                (self._session_snapshot.get("audienceType") or DEFAULT_AUDIENCE).strip()[:100]
            )
            payload["presentationStyle"] = (
                (self._session_snapshot.get("presentationStyle") or DEFAULT_STYLE).strip()[:100]
            )
            return payload

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
            show_toast(self, "Введите название выступления", "error")
            return
        super().accept()
