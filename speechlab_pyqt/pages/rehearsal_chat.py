# pages/rehearsal_chat.py — Rehearsal chat / upload / analysis page

from collections import defaultdict
from copy import deepcopy
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy, QFileDialog, QProgressBar,
    QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt5.QtGui import QFont, QDragEnterEvent, QDropEvent

from styles import (C, BTN_OUTLINE_SM, BTN_PRIMARY,
                     BTN_WHITE_TRANSPARENT, PROGRESS_STYLE, apply_scroll_area_theme)
from api_client import ApiWorker, api
from session_settings import (
    SessionSettingsDialog,
    format_duration_text,
    session_prompt_signature,
    session_prompt_text,
)
from widgets import (Card, BadgePill, ScoreCircle, SmallScoreCircle,
                     NumberCircle, Separator, Switch, make_label, show_toast)

MAX_UPLOAD_SIZE_MB = 100
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
ALLOWED_AUDIO_EXTENSIONS = ('.mp3', '.wav', '.m4a', '.mp4')

BACKEND_STAGE_LABELS = {
    'UPLOADED': 'Файл загружен...',
    'QUEUED': 'Задача в очереди...',
    'PENDING': 'Ожидаем запуск анализа...',
    'CREATED': 'Подготавливаем анализ...',
    'STARTED': 'Анализ запущен...',
    'PROCESSING': 'Идет обработка...',
    'TRANSCRIBING': 'Распознаем аудио...',
    'TRANSCRIPTION': 'Распознаем аудио...',
    'ANALYZING': 'Анализируем запись...',
    'REPORTING': 'Формируем отчет...',
    'GENERATING_REPORT': 'Формируем отчет...',
    'DONE': 'Анализ завершен',
    'COMPLETED': 'Анализ завершен',
    'SUCCESS': 'Анализ завершен',
    'FAILED': 'Анализ завершился с ошибкой',
    'ERROR': 'Анализ завершился с ошибкой',
}
BACKEND_STAGE_SUBSTRINGS = (
    ('transcrib', 'Распознаем аудио...'),
    ('report', 'Формируем отчет...'),
    ('analy', 'Анализируем запись...'),
    ('process', 'Идет обработка...'),
    ('queue', 'Задача в очереди...'),
    ('wait', 'Ожидаем запуск анализа...'),
)
BACKEND_MESSAGE_TRANSLATIONS = {
    'Unable to transcribe audio with ASR service.': 'Не удалось распознать аудио через ASR-сервис.',
    'Analysis completed with error.': 'Анализ завершился с ошибкой.',
}
BACKEND_MESSAGE_SUBSTRINGS = (
    ('Connection refused', 'Сервис обработки аудио временно недоступен. Попробуйте снова через несколько секунд.'),
    ('timed out', 'Сервис обработки аудио не ответил вовремя. Попробуйте еще раз.'),
)


def localize_backend_message(text) -> str:
    message = str(text or '').strip()
    if not message:
        return ''
    if message in BACKEND_MESSAGE_TRANSLATIONS:
        return BACKEND_MESSAGE_TRANSLATIONS[message]
    for needle, translation in BACKEND_MESSAGE_SUBSTRINGS:
        if needle.lower() in message.lower():
            return translation
    return message


def localize_job_stage(stage) -> str:
    raw_stage = str(stage or '').strip()
    if not raw_stage:
        return 'Идет обработка...'
    normalized = raw_stage.upper().replace(' ', '_').replace('-', '_')
    if normalized in BACKEND_STAGE_LABELS:
        return BACKEND_STAGE_LABELS[normalized]
    lowered = raw_stage.lower()
    for needle, translation in BACKEND_STAGE_SUBSTRINGS:
        if needle in lowered:
            return translation
    return raw_stage

# ── Mock analysis data ─────────────────────────────────────────────────────────
MOCK_REPORT = {
    'reportTitle': 'Разбор текущей версии питча',
    'reportSubtitle': 'Что исправить перед следующим выступлением',
    'context': {
        'timeLimit': '5 минут',
        'currentLength': '~6:20',
        'currentLengthTone': 'warning',
    },
    'statusPill': 'Нужна одна сильная итерация правок',
    'statusSummary': (
        'В питче уже есть сильные факты и подтвержденный спрос, но он пока не собирается в одну '
        'убедительную историю. Главные потери возникают в начале, в блоке «почему сейчас» '
        'и в финальном запросе.'
    ),
    'strengths': [
        'В питче уже есть конкретные метрики и подтвержденный спрос, поэтому база для сильной версии уже собрана.',
        'Продукт объясняется через понятную пользовательскую ценность, а не только через общие обещания.',
        'У спикера чувствуется энергия и реальное знание материала.',
        'В текущем тексте уже есть несколько сильных опорных тезисов, которые можно усилить без полного переписывания.',
    ],
    'blockers': [
        'Слишком рано уходит фокус в детали продукта, поэтому инвестиционная логика теряется.',
        'Блок актуальности проекта пока разрознен и не собирается в одно сильное «почему сейчас».',
        'Финальный запрос звучит слишком общо и не фиксирует структуру предложения.',
    ],
    'nextVersionChanges': [
        'Сократить лишние детали в начале и оставить одно сильное доказательство ценности.',
        'Собрать блок «почему сейчас» в короткую причинно-следственную связку.',
        'Добавить более зрелое объяснение, что делает решение труднокопируемым.',
        'Сделать описание альтернатив взрослее и точнее.',
        'Закрыть питч конкретным и запоминающимся запросом.',
    ],
    'nextVersion': {
        'title': 'Следующая версия питча',
        'summary': (
            'Это собранный черновик после правок. Его можно использовать как основу '
            'для следующей записи и дальше адаптировать под свой стиль.'
        ),
        'duration': '~5:10, укладывается в лимит',
        'blocks': [
            {
                'id': 'intro',
                'title': 'Вступление',
                'content': (
                    'Добрый день. Меня зовут Андрей, я основатель CodeKids. '
                    'За последние два года родители и школы всерьез приняли формат '
                    'структурированных онлайн-занятий для детей.'
                ),
                'changeKind': 'edited',
                'changes': ['Собран более сильный контекст'],
            },
            {
                'id': 'product',
                'title': 'Что делает продукт',
                'content': (
                    'CodeKids — это онлайн-платформа, где дети от 6 до 12 лет изучают '
                    'программирование через создание собственных игр. На первом занятии '
                    'ребенок получает быстрый результат и может поделиться им с родителями.'
                ),
                'changeKind': 'edited',
                'changes': ['Сокращены детали', 'Фокус на ценности'],
            },
            {
                'id': 'why-now',
                'title': 'Почему проект актуален сейчас',
                'content': (
                    'Рынок открыл окно возможностей: родители готовы платить за понятный '
                    'онлайн-формат, школы массово докупают внешние программы, а дети уже '
                    'привыкли учиться через экран.'
                ),
                'changeKind': 'combined',
                'changes': ['Собран единый блок «почему сейчас»'],
            },
            {
                'id': 'moat',
                'title': 'Что делает решение труднокопируемым',
                'content': (
                    'Наша сила не только в платформе, а в пошаговой методологии обучения, '
                    'которую команда оттачивала в пилотах со школами несколько лет.'
                ),
                'changeKind': 'new',
                'changes': ['Новый блок'],
            },
            {
                'id': 'alternatives',
                'title': 'Чем это отличается от альтернатив',
                'content': (
                    'Scratch перегружен для новичков, YouTube хаотичен, а Code.org не дает '
                    'ощущения собственного результата. Мы даем структуру, быстрый результат '
                    'и понятный путь для родителя и ребенка.'
                ),
                'changeKind': 'edited',
                'changes': ['Уточнено позиционирование'],
            },
            {
                'id': 'ask',
                'title': 'Что предлагаем инвестору',
                'content': (
                    'Мы привлекаем $500K на 18 месяцев для масштабирования в 200 школ и '
                    'запуска B2C-модели. Предлагаем 12% доли и готовы обсуждать детали.'
                ),
                'changeKind': 'edited',
                'changes': ['Конкретизирован финальный запрос'],
            },
        ],
        'note': (
            'Это рабочая версия на основе текущего питча. Ее задача — ускорить следующую '
            'выступление, а не навязать чужую лексику слово в слово.'
        ),
    },
    'recommendationsSummary': [
        'Убрать лишнюю демонстрацию продукта из первых минут.',
        'Собрать блок «почему сейчас» в одну убедительную конструкцию.',
        'Добавить блок про труднокопируемость решения.',
        'Переписать запрос к инвестору в форму конкретного предложения.',
    ],
    'recommendations': [
        {
            'id': 'rec-1',
            'section': 'Начало',
            'before': (
                'Мы довольно долго показываем механику продукта и уходим в детали, '
                'прежде чем слушатель понимает главную ценность.'
            ),
            'after': (
                'На первом занятии ребенок собирает простую игру и сразу может '
                'поделиться результатом. Это быстро доказывает ценность и удерживает внимание.'
            ),
            'whyOldWasWeaker': (
                'Старое начало тратит кредит внимания на детали интерфейса вместо того, '
                'чтобы быстро зафиксировать сильное доказательство ценности.'
            ),
            'whyNewIsBetter': (
                'Новая версия быстрее доводит слушателя до сути продукта и оставляет пространство '
                'для последующей бизнес-логики.'
            ),
            'whatAudienceUnderstands': 'Какую конкретную ценность продукт дает уже в первую минуту объяснения.',
            'whatAudienceFeels': 'Что спикер контролирует структуру и не теряет нить питча.',
        },
        {
            'id': 'rec-2',
            'section': 'Почему сейчас',
            'before': (
                'Аргументы про рынок и спрос звучат как отдельные наблюдения, а не как единое '
                'окно возможностей.'
            ),
            'after': (
                'Родители готовы к формату, школы массово закупают внешние решения, а дети '
                'уже привыкли учиться через экран — значит окно возможностей открыто именно сейчас.'
            ),
            'whyOldWasWeaker': (
                'Разрозненные факты не создают ощущение срочности и не усиливают инвестиционную '
                'часть истории.'
            ),
            'whyNewIsBetter': (
                'Единый блок «почему сейчас» дает причинно-следственную связку и делает рынок более осязаемым.'
            ),
            'whatAudienceUnderstands': 'Почему проект актуален именно в этот момент, а не вообще когда-нибудь.',
            'whatAudienceFeels': 'Что это реальное окно возможностей, а не набор красивых тезисов.',
        },
        {
            'id': 'rec-3',
            'section': 'Финальный запрос к инвестору',
            'before': 'Мы ищем инвестиции для роста и хотим обсудить сотрудничество.',
            'after': (
                'Мы привлекаем $500K на 18 месяцев, чтобы масштабироваться в 200 школ и '
                'запустить B2C-направление. Предлагаем 12% доли.'
            ),
            'whyOldWasWeaker': (
                'Размытый запрос не фиксирует предмет разговора и не создает ощущение готовой сделки.'
            ),
            'whyNewIsBetter': (
                'Конкретный запрос помогает слушателю быстро понять параметры предложения и серьезнее '
                'отнестись к финалу.'
            ),
            'whatAudienceUnderstands': 'Что именно предлагается и на каких базовых условиях.',
            'whatAudienceFeels': 'Что команда пришла не просто рассказать историю, а закрыть следующий шаг.',
        },
    ],
}


# ── Helper widgets ─────────────────────────────────────────────────────────────
class MetricCard(QFrame):
    _uid = 0

    def __init__(self, label, score, parent=None):
        super().__init__(parent)
        MetricCard._uid += 1
        name = f'MetricCard{MetricCard._uid}'
        self.setObjectName(name)
        self.setStyleSheet(f"""
            QFrame#{name} {{
                background: {C['slate_50']};
                border: 1px solid {C['slate_200']};
                border-radius: 12px;
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 14, 12, 14)
        lay.setSpacing(8)
        lay.setAlignment(Qt.AlignCenter)

        lbl = QLabel(label.upper())
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet(
            f"font-size: 10px; font-weight: 600; color: {C['slate_600']}; "
            f"letter-spacing: 1px; background: transparent; border: none;"
        )
        lay.addWidget(lbl)

        circle = SmallScoreCircle(score, size=56)
        lay.addWidget(circle, 0, Qt.AlignCenter)


class ChatBubbleUser(QFrame):
    _uid = 0

    def __init__(self, text, parent=None):
        super().__init__(parent)
        ChatBubbleUser._uid += 1
        name = f'CBU{ChatBubbleUser._uid}'
        self.setObjectName(name)
        self.setStyleSheet(f"""
            QFrame#{name} {{
                background: {C['indigo_600']};
                border-radius: 16px;
                border-top-right-radius: 4px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.setMaximumWidth(500)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 12, 18, 12)
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet('color: white; font-size: 14px; background: transparent; border: none;')
        lay.addWidget(lbl)


class ChatBubbleAI(QFrame):
    _uid = 0

    def __init__(self, text, parent=None):
        super().__init__(parent)
        ChatBubbleAI._uid += 1
        name = f'CBAI{ChatBubbleAI._uid}'
        self.setObjectName(name)
        self.setStyleSheet(f"""
            QFrame#{name} {{
                background: {C['white']};
                border: 1px solid {C['slate_200']};
                border-radius: 16px;
                border-top-left-radius: 4px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.setMaximumWidth(500)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 12, 18, 12)
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet(f'color: {C["slate_700"]}; font-size: 14px; '
                          f'background: transparent; border: none;')
        lay.addWidget(lbl)


# ── PDF Report preview ─────────────────────────────────────────────────────────
class ReportWidget(QFrame):
    _uid = 0

    def __init__(self, data: dict, on_download, parent=None):
        super().__init__(parent)
        ReportWidget._uid += 1
        name = f'ReportWidget{ReportWidget._uid}'
        self.setObjectName(name)
        self.setStyleSheet(f"""
            QFrame#{name} {{
                background: {C['white']};
                border: 1px solid {C['slate_200']};
                border-radius: 16px;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Gradient header ────────────────────────────────────────
        header = QFrame()
        header.setObjectName('RHeader')
        header.setStyleSheet(f"""
            QFrame#RHeader {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {C['indigo_600']}, stop:1 {C['blue_600']}
                );
                border-radius: 0px;
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
            }
        """)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(28, 22, 28, 22)

        h_text = QVBoxLayout()
        h_text.setSpacing(4)
        h_title = QLabel('Отчет по анализу речи')
        h_title.setStyleSheet('color: white; font-size: 20px; font-weight: 700; '
                              'background: transparent; border: none;')
        h_sub = QLabel('Обратная связь и выводы, сформированные ИИ')
        h_sub.setStyleSheet('color: rgba(199,210,254,1); font-size: 13px; '
                            'background: transparent; border: none;')
        h_text.addWidget(h_title)
        h_text.addWidget(h_sub)

        btn_dl = QPushButton('⬇  Сохранить PDF')
        btn_dl.setStyleSheet(BTN_WHITE_TRANSPARENT)
        btn_dl.setFixedHeight(36)
        btn_dl.setCursor(Qt.PointingHandCursor)
        btn_dl.clicked.connect(on_download)

        h_lay.addLayout(h_text)
        h_lay.addStretch()
        h_lay.addWidget(btn_dl)
        root.addWidget(header)

        # ── Body ───────────────────────────────────────────────────
        body = QWidget()
        body.setStyleSheet('background: transparent;')
        b_lay = QVBoxLayout(body)
        b_lay.setContentsMargins(28, 24, 28, 24)
        b_lay.setSpacing(24)

        # Overall score
        score_sec = QVBoxLayout()
        score_sec.setSpacing(10)
        score_sec.setAlignment(Qt.AlignCenter)
        ov_lbl = QLabel('ОБЩАЯ ОЦЕНКА')
        ov_lbl.setAlignment(Qt.AlignCenter)
        ov_lbl.setStyleSheet(f'font-size: 11px; font-weight: 600; color: {C["slate_600"]}; '
                             f'letter-spacing: 1px; background: transparent; border: none;')
        score_circle = ScoreCircle(data['overallScore'], size=112)
        perf_txt = 'Отличное выступление!' if data['overallScore'] >= 85 \
            else ('Хорошее выступление!' if data['overallScore'] >= 70 else 'Есть, что улучшить')
        perf_lbl = QLabel(perf_txt)
        perf_lbl.setAlignment(Qt.AlignCenter)
        perf_lbl.setStyleSheet(f'font-size: 14px; color: {C["slate_600"]}; '
                               f'background: transparent; border: none;')
        score_sec.addWidget(ov_lbl)
        score_sec.addWidget(score_circle, 0, Qt.AlignCenter)
        score_sec.addWidget(perf_lbl)

        score_w = QWidget()
        score_w.setStyleSheet('background: transparent;')
        score_w_lay = QVBoxLayout(score_w)
        score_w_lay.addLayout(score_sec)
        b_lay.addWidget(score_w)
        b_lay.addWidget(Separator())

        # Metrics grid
        b_lay.addWidget(make_label('Метрики выступления', size=15, weight=QFont.DemiBold,
                                   color=C['slate_900']))
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(12)
        metrics = [
            ('Ясность', data['clarity']),
            ('Темп', data['pace']),
            ('Уверенность', data['confidence']),
            ('Структура', data['structure']),
            ('Эмоциональный тон', data['emotionalTone']),
            ('Слова-паразиты', 100 - data['fillerWords']),
        ]
        for i, (lbl, score) in enumerate(metrics):
            metrics_grid.addWidget(MetricCard(lbl, score), i // 3, i % 3)
        b_lay.addLayout(metrics_grid)

        # Strengths
        b_lay.addWidget(Separator())
        s_header = QHBoxLayout()
        s_icon = QLabel('↗')
        s_icon.setStyleSheet(f'color: {C["green_600"]}; font-size: 18px; '
                             f'background: transparent; border: none;')
        s_header.addWidget(s_icon)
        s_header.addWidget(make_label('Сильные стороны', size=15, weight=QFont.DemiBold,
                                      color=C['slate_900']))
        s_header.addStretch()
        b_lay.addLayout(s_header)

        for strength in data['strengths']:
            row = QFrame()
            row.setObjectName('StrengthRow')
            row.setStyleSheet(f"""
                QFrame#StrengthRow {{
                    background: {C['green_50']};
                    border: 1px solid {C['green_200']};
                    border-radius: 8px;
                }}
            """)
            r_lay = QHBoxLayout(row)
            r_lay.setContentsMargins(12, 10, 12, 10)
            r_lay.setSpacing(10)
            ic = QLabel('✓')
            ic.setFixedWidth(18)
            ic.setStyleSheet(f'color: {C["green_600"]}; font-size: 14px; font-weight: bold; '
                             f'background: transparent; border: none;')
            tx = make_label(strength, size=14, color=C['slate_700'], wrap=True)
            r_lay.addWidget(ic, 0, Qt.AlignTop)
            r_lay.addWidget(tx, 1)
            b_lay.addWidget(row)

        # Weaknesses
        b_lay.addWidget(Separator())
        w_header = QHBoxLayout()
        w_icon = QLabel('↘')
        w_icon.setStyleSheet(f'color: {C["amber_600"]}; font-size: 18px; '
                             f'background: transparent; border: none;')
        w_header.addWidget(w_icon)
        w_header.addWidget(make_label('Зоны роста', size=15,
                                      weight=QFont.DemiBold, color=C['slate_900']))
        w_header.addStretch()
        b_lay.addLayout(w_header)

        for weakness in data['weaknesses']:
            row = QFrame()
            row.setObjectName('WeakRow')
            row.setStyleSheet(f"""
                QFrame#WeakRow {{
                    background: {C['amber_50']};
                    border: 1px solid {C['amber_200']};
                    border-radius: 8px;
                }}
            """)
            r_lay = QHBoxLayout(row)
            r_lay.setContentsMargins(12, 10, 12, 10)
            r_lay.setSpacing(10)
            ic = QLabel('!')
            ic.setFixedWidth(18)
            ic.setStyleSheet(f'color: {C["amber_600"]}; font-size: 16px; font-weight: bold; '
                             f'background: transparent; border: none;')
            tx = make_label(weakness, size=14, color=C['slate_700'], wrap=True)
            r_lay.addWidget(ic, 0, Qt.AlignTop)
            r_lay.addWidget(tx, 1)
            b_lay.addWidget(row)

        # Recommendations
        b_lay.addWidget(Separator())
        rec_header = QHBoxLayout()
        rec_icon = QLabel('✦')
        rec_icon.setStyleSheet(f'color: {C["indigo_600"]}; font-size: 16px; '
                               f'background: transparent; border: none;')
        rec_header.addWidget(rec_icon)
        rec_header.addWidget(make_label('Практические рекомендации', size=15,
                                        weight=QFont.DemiBold, color=C['slate_900']))
        rec_header.addStretch()
        b_lay.addLayout(rec_header)

        for i, rec in enumerate(data['recommendations']):
            row = QFrame()
            row.setObjectName('RecRow')
            row.setStyleSheet(f"""
                QFrame#RecRow {{
                    background: {C['indigo_50']};
                    border: 1px solid {C['indigo_200']};
                    border-radius: 8px;
                }}
            """)
            r_lay = QHBoxLayout(row)
            r_lay.setContentsMargins(12, 12, 12, 12)
            r_lay.setSpacing(12)
            num = NumberCircle(i + 1, size=24)
            tx = make_label(rec, size=14, color=C['slate_700'], wrap=True)
            r_lay.addWidget(num, 0, Qt.AlignTop)
            r_lay.addWidget(tx, 1)
            b_lay.addWidget(row)

        root.addWidget(body)

        # Footer
        footer = QFrame()
        footer.setObjectName('RFooter')
        footer.setStyleSheet(f"""
            QFrame#RFooter {{
                background: {C['slate_50']};
                border-top: 1px solid {C['slate_200']};
                border-bottom-left-radius: 16px;
                border-bottom-right-radius: 16px;
            }}
        """)
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(28, 12, 28, 12)
        from datetime import date
        f_lbl = QLabel(f"Сформировано SpeechGym AI  •  {date.today().strftime('%d.%m.%Y')}")
        f_lbl.setAlignment(Qt.AlignCenter)
        f_lbl.setStyleSheet(f'font-size: 12px; color: {C["slate_500"]}; '
                            f'background: transparent; border: none;')
        f_lay.addStretch()
        f_lay.addWidget(f_lbl)
        f_lay.addStretch()
        root.addWidget(footer)


class PitchReportWidget(QFrame):
    _uid = 0
    TABS = (
        ('passport', 'Паспорт питча'),
        ('newVersion', 'Следующая версия'),
        ('recommendations', 'Рекомендации'),
    )

    def __init__(self, data: dict, on_download, parent=None):
        super().__init__(parent)
        PitchReportWidget._uid += 1
        object_name = f'PitchReportWidget{PitchReportWidget._uid}'
        self.setObjectName(object_name)
        self._data = deepcopy(data or {})
        self._active_tab = 'passport'
        self._tab_buttons = {}
        self._equal_height_pairs = []
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setStyleSheet(f"""
            QFrame#{object_name} {{
                background: {C['white']};
                border: 1px solid {C['slate_200']};
                border-radius: 20px;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        header = QFrame()
        header_name = f'{object_name}Header'
        header.setObjectName(header_name)
        header.setStyleSheet(f"""
            QFrame#{header_name} {{
                background: {C['slate_50']};
                border: none;
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
                border-bottom: 1px solid {C['slate_200']};
            }}
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(28, 22, 28, 22)
        header_layout.setSpacing(16)

        top_row = QHBoxLayout()
        top_row.setSpacing(14)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        brand = QLabel('SpeechGym')
        brand.setStyleSheet(
            f'color: {C["slate_500"]}; font-size: 11px; font-weight: 700; '
            'letter-spacing: 1px; background: transparent; border: none;'
        )
        title = QLabel(self._data.get('reportTitle') or 'Разбор текущей версии питча')
        title.setStyleSheet(
            f'color: {C["slate_900"]}; font-size: 22px; font-weight: 700; '
            'background: transparent; border: none;'
        )
        subtitle = QLabel(self._data.get('reportSubtitle') or '')
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(
            f'color: {C["slate_600"]}; font-size: 13px; background: transparent; border: none;'
        )
        title_col.addWidget(brand)
        title_col.addWidget(title)
        title_col.addWidget(subtitle)

        btn_dl = QPushButton('Сохранить PDF')
        btn_dl.setFixedHeight(36)
        btn_dl.setCursor(Qt.PointingHandCursor)
        btn_dl.setStyleSheet(f"""
            QPushButton {{
                background: {C['white']};
                color: {C['slate_700']};
                border: 1px solid {C['slate_300']};
                border-radius: 10px;
                padding: 0 16px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {C['slate_100']};
                border-color: {C['slate_400']};
            }}
            QPushButton:pressed {{
                background: {C['slate_200']};
            }}
        """)
        btn_dl.clicked.connect(on_download)

        top_row.addLayout(title_col, 1)
        top_row.addWidget(btn_dl, 0, Qt.AlignTop)
        header_layout.addLayout(top_row)

        tabs_row = QHBoxLayout()
        tabs_row.setSpacing(10)
        for tab_key, label in self.TABS:
            button = QPushButton(label)
            button.setCursor(Qt.PointingHandCursor)
            button.setFixedHeight(38)
            button.clicked.connect(lambda _, tab_key=tab_key: self._set_active_tab(tab_key))
            self._tab_buttons[tab_key] = button
            tabs_row.addWidget(button)
        tabs_row.addStretch()
        header_layout.addLayout(tabs_row)
        root.addWidget(header)

        self.content_host = QWidget()
        self.content_host.setStyleSheet('background: transparent; border: none;')
        self.content_host.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.content_layout = QVBoxLayout(self.content_host)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        root.addWidget(self.content_host, 0, Qt.AlignTop)

        self._passport_page, self._passport_layout = self._build_page()
        self._new_version_page, self._new_version_layout = self._build_page()
        self._recommendations_page, self._recommendations_layout = self._build_page()
        self._tab_pages = {
            'passport': self._passport_page,
            'newVersion': self._new_version_page,
            'recommendations': self._recommendations_page,
        }
        self._active_page = None

        self._populate_passport_page()
        self._populate_new_version_page()
        self._populate_recommendations_page()
        self._refresh_tab_buttons()
        self._set_active_tab('passport')
        QTimer.singleShot(0, self._sync_active_tab_height)

        footer = QFrame()
        footer_name = f'{object_name}Footer'
        footer.setObjectName(footer_name)
        footer.setStyleSheet(f"""
            QFrame#{footer_name} {{
                background: {C['slate_50']};
                border: none;
                border-top: 1px solid {C['slate_200']};
                border-bottom-left-radius: 20px;
                border-bottom-right-radius: 20px;
            }}
        """)
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(28, 12, 28, 12)
        from datetime import date
        footer_label = QLabel(f"Сформировано SpeechGym AI  •  {date.today().strftime('%d.%m.%Y')}")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet(
            f'font-size: 12px; color: {C["slate_500"]}; background: transparent; border: none;'
        )
        footer_layout.addStretch()
        footer_layout.addWidget(footer_label)
        footer_layout.addStretch()
        root.addWidget(footer)

    def _build_page(self):
        page = QWidget()
        page.setStyleSheet('background: transparent;')
        page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 28)
        layout.setSpacing(18)
        return page, layout

    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()
            if widget is not None:
                widget.deleteLater()
            elif child_layout is not None:
                PitchReportWidget._clear_layout(child_layout)

    def _set_active_tab(self, tab_key: str):
        self._active_tab = tab_key
        self._refresh_tab_buttons()
        target_page = self._tab_pages.get(tab_key, self._passport_page)
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)

        target_page.setParent(self.content_host)
        self.content_layout.addWidget(target_page, 0, Qt.AlignTop)
        target_page.show()
        self._active_page = target_page
        self._sync_active_tab_height()
        QTimer.singleShot(0, self._sync_active_tab_height)

    def _sync_active_tab_height(self):
        current_widget = self._active_page
        if current_widget is None:
            return
        layout = current_widget.layout()
        if layout is not None:
            layout.activate()
        if self._active_tab == 'recommendations':
            self._sync_equal_height_pairs()
        current_widget.adjustSize()
        self.content_host.adjustSize()
        self.content_host.updateGeometry()
        root_layout = self.layout()
        if root_layout is not None:
            root_layout.activate()
        self.updateGeometry()
        parent = self.parentWidget()
        if parent is not None:
            parent.updateGeometry()

    def _register_equal_height_pair(self, left: QFrame, right: QFrame):
        self._equal_height_pairs.append((left, right))
        left.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def _sync_equal_height_pairs(self):
        active_page = self._active_page
        if active_page is None:
            return
        for left, right in self._equal_height_pairs:
            if not self._is_child_of(left, active_page):
                continue
            for panel in (left, right):
                panel.setMinimumHeight(0)
                panel.setMaximumHeight(16777215)
                panel_layout = panel.layout()
                if panel_layout is not None:
                    panel_layout.activate()
            target_height = max(
                left.sizeHint().height(),
                right.sizeHint().height(),
                left.minimumSizeHint().height(),
                right.minimumSizeHint().height(),
            )
            left.setFixedHeight(target_height)
            right.setFixedHeight(target_height)

    @staticmethod
    def _is_child_of(widget, parent) -> bool:
        current = widget
        while current is not None:
            if current is parent:
                return True
            current = current.parentWidget()
        return False

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(0, self._sync_active_tab_height)

    def _refresh_tab_buttons(self):
        for tab_key, button in self._tab_buttons.items():
            if tab_key == self._active_tab:
                button.setStyleSheet(f"""
                    QPushButton {{
                        background: {C['indigo_600']};
                        color: #FFFFFF;
                        border: 1px solid {C['indigo_600']};
                        border-radius: 10px;
                        padding: 0 16px;
                        font-size: 13px;
                        font-weight: 600;
                    }}
                """)
            else:
                button.setStyleSheet(f"""
                    QPushButton {{
                        background: {C['slate_100']};
                        color: {C['slate_700']};
                        border: 1px solid {C['slate_200']};
                        border-radius: 10px;
                        padding: 0 16px;
                        font-size: 13px;
                        font-weight: 600;
                    }}
                    QPushButton:hover {{
                        background: {C['slate_200']};
                    }}
                """)

    @staticmethod
    def _tone_palette(tone: str) -> dict:
        palettes = {
            'success': {'bg': C['green_50'], 'border': C['green_200'], 'text': C['green_600']},
            'warning': {'bg': C['amber_50'], 'border': C['amber_200'], 'text': C['amber_600']},
            'danger': {'bg': C['red_50'], 'border': C['red_200'], 'text': C['red_700']},
            'info': {'bg': C['indigo_50'], 'border': C['indigo_200'], 'text': C['indigo_600']},
            'accent': {'bg': C['violet_100'], 'border': C['indigo_200'], 'text': C['violet_600']},
            'neutral': {'bg': C['slate_50'], 'border': C['slate_200'], 'text': C['slate_600']},
        }
        return palettes.get(tone, palettes['neutral'])

    def _make_panel(self, *, bg=None, border=None, radius=16):
        panel = QFrame()
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        PitchReportWidget._panel_uid = getattr(PitchReportWidget, '_panel_uid', 0) + 1
        panel_name = f'PitchReportPanel{PitchReportWidget._panel_uid}'
        panel.setObjectName(panel_name)
        panel.setStyleSheet(f"""
            QFrame#{panel_name} {{
                background: {bg or C['white']};
                border: 1px solid {border or C['slate_200']};
                border-radius: {radius}px;
            }}
        """)
        return panel

    def _make_context_card(self, label: str, value: str, *, tone='neutral'):
        palette = self._tone_palette(tone)
        card = self._make_panel(bg=C['white'], border=C['slate_200'], radius=14)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)
        layout.addWidget(make_label(label, size=11, weight=QFont.Medium, color=C['slate_500']))
        layout.addWidget(make_label(value, size=15, weight=QFont.DemiBold, color=palette['text'], wrap=True))
        return card

    def _make_banner(self, pill_text: str, body_text: str, *, tone='info'):
        palette = self._tone_palette(tone)
        banner = self._make_panel(bg=palette['bg'], border=palette['border'], radius=16)
        layout = QVBoxLayout(banner)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)
        layout.addWidget(
            make_label(pill_text, size=13, weight=QFont.DemiBold, color=C['slate_900']),
            0,
            Qt.AlignLeft,
        )
        layout.addWidget(make_label(body_text, size=14, color=C['slate_700'], wrap=True))
        return banner

    def _make_section_card(self, title: str, items: list[str], *, tone='neutral'):
        palette = self._tone_palette(tone)
        card = self._make_panel(bg=C['white'], border=C['slate_200'], radius=16)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(10)
        marker = QLabel('•')
        marker.setStyleSheet(
            f'color: {palette["text"]}; font-size: 22px; font-weight: 700; background: transparent; border: none;'
        )
        header.addWidget(marker, 0, Qt.AlignTop)
        header.addWidget(make_label(title, size=18, weight=QFont.Bold, color=C['slate_900']))
        header.addStretch()
        layout.addLayout(header)

        for item in items:
            row = QHBoxLayout()
            row.setSpacing(10)
            dot = QLabel('•')
            dot.setFixedWidth(12)
            dot.setStyleSheet(
                f'color: {palette["text"]}; font-size: 18px; background: transparent; border: none;'
            )
            row.addWidget(dot, 0, Qt.AlignTop)
            row.addWidget(make_label(item, size=14, color=C['slate_700'], wrap=True), 1)
            layout.addLayout(row)
        return card

    def _make_quote_panel(self, title: str, text: str, *, tone='neutral'):
        palette = self._tone_palette(tone)
        panel = self._make_panel(bg=palette['bg'], border=palette['border'], radius=14)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(make_label(title, size=11, weight=QFont.Bold, color=C['slate_500']))
        quote = make_label(f'“{text}”', size=14, color=C['slate_700'], wrap=True)
        font = quote.font()
        font.setItalic(True)
        quote.setFont(font)
        layout.addWidget(quote, 0, Qt.AlignTop)
        layout.addStretch()
        return panel

    def _make_text_panel(self, title: str, text: str, *, tone='neutral'):
        palette = self._tone_palette(tone)
        panel = self._make_panel(bg=palette['bg'], border=palette['border'], radius=14)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(make_label(title, size=12, weight=QFont.Bold, color=C['slate_700']))
        layout.addWidget(make_label(text, size=13, color=C['slate_700'], wrap=True), 0, Qt.AlignTop)
        layout.addStretch()
        return panel

    def _populate_passport_page(self):
        self._clear_layout(self._passport_layout)
        context = self._data.get('context') or {}

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)


        cards_row.addWidget(self._make_context_card('Лимит времени', context.get('timeLimit') or '5 минут'))
        cards_row.addWidget(
            self._make_context_card(
                'Текущая длина',
                context.get('currentLength') or '~6:20',
                tone=context.get('currentLengthTone') or 'warning',
            ),
            0,
            Qt.AlignTop,
        )
        self._passport_layout.addLayout(cards_row)
        self._passport_layout.addWidget(
            self._make_banner(
                self._data.get('statusPill') or 'Нужна доработка',
                self._data.get('statusSummary') or '',
                tone='info',
            )
        )
        strengths = self._data.get('strengths') or []
        blockers = self._data.get('blockers') or []
        next_changes = self._data.get('nextVersionChanges') or []
        if strengths:
            self._passport_layout.addWidget(
                self._make_section_card('Что уже сильное', strengths, tone='success')
            )
        if blockers:
            self._passport_layout.addWidget(
                self._make_section_card('Что мешает сейчас', blockers, tone='warning')
            )
        if next_changes:
            self._passport_layout.addWidget(
                self._make_section_card(
                    'Что изменится в следующей версии',
                    next_changes,
                    tone='info',
                )
            )

    def _populate_new_version_page(self):
        self._clear_layout(self._new_version_layout)
        next_version = self._data.get('nextVersion') or {}
        blocks = list(next_version.get('blocks') or [])
        if not blocks:
            full_text = str(next_version.get('fullText') or next_version.get('full_text') or '').strip()
            if full_text:
                blocks = [{
                    'title': next_version.get('title') or 'Следующая версия pitch',
                    'content': full_text,
                }]

        for block in blocks:
            card = self._make_panel(bg=C['white'], border=C['slate_200'], radius=16)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(0, 0, 0, 0)
            card_layout.setSpacing(0)

            head = QFrame()
            head.setStyleSheet(f"""
                background: {C['slate_50']};
                border: none;
                border-bottom: 1px solid {C['slate_200']};
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
            """)
            head_layout = QHBoxLayout(head)
            head_layout.setContentsMargins(18, 14, 18, 14)
            head_layout.setSpacing(10)
            head_layout.addWidget(make_label(block.get('title') or block.get('label') or '', size=15, weight=QFont.Bold))
            head_layout.addStretch()
            card_layout.addWidget(head)

            body = QWidget()
            body_layout = QVBoxLayout(body)
            body_layout.setContentsMargins(18, 16, 18, 18)
            body_layout.setSpacing(0)
            body_layout.addWidget(make_label(block.get('content') or block.get('text') or '', size=14, color=C['slate_700'], wrap=True))
            card_layout.addWidget(body)
            self._new_version_layout.addWidget(card)

        if not str(next_version.get('note') or '').strip():
            return

        note_card = self._make_panel(bg=C['blue_50'], border=C['blue_100'], radius=16)
        note_layout = QVBoxLayout(note_card)
        note_layout.setContentsMargins(18, 16, 18, 16)
        note_layout.setSpacing(6)
        note_layout.addWidget(make_label('Примечание', size=13, weight=QFont.Bold, color=C['slate_700']))
        note_layout.addWidget(make_label(next_version.get('note') or '', size=13, color=C['slate_700'], wrap=True))
        self._new_version_layout.addWidget(note_card)

    def _populate_recommendations_page(self):
        self._clear_layout(self._recommendations_layout)
        self._equal_height_pairs = []

        summary = self._make_panel(bg=C['violet_100'], border=C['indigo_200'], radius=16)
        summary_layout = QVBoxLayout(summary)
        summary_layout.setContentsMargins(20, 18, 20, 18)
        summary_layout.setSpacing(10)
        summary_layout.addWidget(make_label('Главные улучшения', size=20, weight=QFont.Bold))
        for item in self._data.get('recommendationsSummary') or []:
            row = QHBoxLayout()
            row.setSpacing(8)
            dot = QLabel('•')
            dot.setStyleSheet(
                f'color: {C["violet_600"]}; font-size: 18px; background: transparent; border: none;'
            )
            row.addWidget(dot, 0, Qt.AlignTop)
            row.addWidget(make_label(item, size=13, color=C['slate_700'], wrap=True), 1)
            summary_layout.addLayout(row)
        self._recommendations_layout.addWidget(summary)

        for change in self._data.get('recommendations') or []:
            card = self._make_panel(bg=C['white'], border=C['slate_200'], radius=16)
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(0, 0, 0, 0)
            card_layout.setSpacing(0)

            title_bar = QFrame()
            title_bar.setStyleSheet(f"""
                background: {C['indigo_600']};
                border: none;
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
            """)
            title_layout = QHBoxLayout(title_bar)
            title_layout.setContentsMargins(18, 14, 18, 14)
            title_layout.addWidget(make_label(change.get('section') or '', size=15, weight=QFont.Bold, color='#FFFFFF'))
            title_layout.addStretch()
            card_layout.addWidget(title_bar)

            content = QWidget()
            content_layout = QVBoxLayout(content)
            content_layout.setContentsMargins(18, 18, 18, 18)
            content_layout.setSpacing(14)

            compare_row = QHBoxLayout()
            compare_row.setSpacing(12)
            before_panel = self._make_quote_panel('Было', change.get('before') or '', tone='danger')
            after_panel = self._make_quote_panel('Стало', change.get('after') or '', tone='success')
            self._register_equal_height_pair(before_panel, after_panel)
            compare_row.addWidget(before_panel, 1, Qt.AlignTop)
            compare_row.addWidget(after_panel, 1, Qt.AlignTop)
            content_layout.addLayout(compare_row)

            explain_row = QHBoxLayout()
            explain_row.setSpacing(12)
            old_reason_panel = self._make_text_panel('Почему старая версия слабее', change.get('whyOldWasWeaker') or '', tone='warning')
            new_reason_panel = self._make_text_panel('Почему новая версия лучше', change.get('whyNewIsBetter') or '', tone='success')
            self._register_equal_height_pair(old_reason_panel, new_reason_panel)
            explain_row.addWidget(old_reason_panel, 1, Qt.AlignTop)
            explain_row.addWidget(new_reason_panel, 1, Qt.AlignTop)
            content_layout.addLayout(explain_row)

            impact_row = QHBoxLayout()
            impact_row.setSpacing(12)
            understands_panel = self._make_text_panel('Что аудитория понимает', change.get('whatAudienceUnderstands') or '', tone='info')
            feels_panel = self._make_text_panel('Что аудитория чувствует', change.get('whatAudienceFeels') or '', tone='accent')
            self._register_equal_height_pair(understands_panel, feels_panel)
            impact_row.addWidget(understands_panel, 1, Qt.AlignTop)
            impact_row.addWidget(feels_panel, 1, Qt.AlignTop)
            content_layout.addLayout(impact_row)

            card_layout.addWidget(content)
            self._recommendations_layout.addWidget(card)



# ── Upload drop zone ───────────────────────────────────────────────────────────
class UploadZone(QFrame):
    file_selected = pyqtSignal(str)
    _uid = 0

    def __init__(self, parent=None):
        super().__init__(parent)
        UploadZone._uid += 1
        self._name = f'UploadZone{UploadZone._uid}'
        self.setObjectName(self._name)
        self.setAcceptDrops(True)
        self._idle_style = f"""
            QFrame#{self._name} {{
                background: {C['white']};
                border: 2px dashed {C['slate_300']};
                border-radius: 16px;
            }}
        """
        self._hover_style = f"""
            QFrame#{self._name} {{
                background: {C['indigo_50']};
                border: 2px dashed {C['indigo_400']};
                border-radius: 16px;
            }}
        """
        self.setStyleSheet(self._idle_style)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 40, 40, 40)
        lay.setSpacing(14)
        lay.setAlignment(Qt.AlignCenter)

        icon_box = QLabel('⬆')
        icon_box.setAlignment(Qt.AlignCenter)
        icon_box.setFixedSize(64, 64)
        icon_box.setStyleSheet(f"""
            background: {C['slate_100']};
            border-radius: 16px;
            font-size: 28px;
            color: {C['slate_400']};
            border: none;
        """)
        lay.addWidget(icon_box, 0, Qt.AlignCenter)

        lay.addWidget(make_label('Загрузите аудио выступления', size=17,
                                 weight=QFont.DemiBold, color=C['slate_900'],
                                 align=Qt.AlignHCenter))
        lay.addWidget(make_label('Перетащите аудиофайл сюда или нажмите, чтобы выбрать его',
                                 size=14, color=C['slate_600'], align=Qt.AlignHCenter))

        btn = QPushButton('⬆  Выбрать файл')
        btn.setStyleSheet(BTN_PRIMARY)
        btn.setFixedHeight(40)
        btn.setFixedWidth(160)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self._open_dialog)
        lay.addWidget(btn, 0, Qt.AlignCenter)

        lay.addWidget(make_label('Поддерживаются MP3, WAV, M4A, MP4  •  Максимальный размер: 100 МБ',
                                 size=12, color=C['slate_500'], align=Qt.AlignHCenter))
    def _open_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Выберите аудиофайл', '',
            'Аудиофайлы (*.mp3 *.wav *.m4a *.mp4);;Все файлы (*)'
        )
        if path:
            self.file_selected.emit(path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(self._hover_style)

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self._idle_style)

    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet(self._idle_style)
        urls = event.mimeData().urls()
        if urls:
            self.file_selected.emit(urls[0].toLocalFile())


# ── Main page ─────────────────────────────────────────────────────────────────
class RehearsalChatPage(QWidget):
    navigate = pyqtSignal(str, object)

    def __init__(self):
        super().__init__()
        self.setObjectName('RehearsalChatPage')
        self.setStyleSheet(f'QWidget#RehearsalChatPage {{ background: {C["slate_50"]}; }}')
        self._config = {}
        self._state = 'idle'   # idle | uploading | processing | success | error
        self._progress = 0
        self._messages = []
        self._workers = []
        self._session_id = None
        self._job_id = None
        self._report_id = None
        self._poll_timer = None
        self._polling = False
        self._current_pdf_path = None
        self._view_token = 0
        self._upload_zone = None
        self._has_attempts = False
        self._session = {}
        self._settings_prompt_widget = None
        self._settings_prompt_signature = None
        self._settings_busy = False
        self._scroll_request_id = 0
        self._pending_open_scroll_widget = None
        self._pending_open_scroll_to_bottom = False
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ────────────────────────────────────────────────
        self.header = QFrame()
        self.header.setFixedHeight(60)
        self.header.setStyleSheet(
            f"background: {C['white']}; border-bottom: 1px solid {C['slate_200']};"
        )
        h_lay = QHBoxLayout(self.header)
        h_lay.setContentsMargins(20, 0, 20, 0)
        h_lay.setSpacing(12)

        btn_back = QPushButton('← Назад к панели')
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background: {C['slate_100']};
                color: {C['slate_800']};
                border: 1px solid {C['slate_200']};
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: 600;
                text-align: left;
            }}
            QPushButton:hover {{
                background: {C['slate_200']};
                border-color: {C['slate_300']};
            }}
            QPushButton:pressed {{
                background: {C['slate_300']};
            }}
        """)
        btn_back.setFixedHeight(32)
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.clicked.connect(self._go_back)

        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setStyleSheet(f'color: {C["slate_200"]}; background: {C["slate_200"]};')
        divider.setFixedWidth(1)

        self.header_title = make_label('Сессия выступления', size=14,
                                       weight=QFont.DemiBold, color=C['slate_900'])
        self.header_sub = make_label('', size=13, color=C['slate_500'])

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_col.addWidget(self.header_title)
        title_col.addWidget(self.header_sub)

        self.btn_edit_settings = QPushButton('Изменить настройки')
        self.btn_edit_settings.setStyleSheet(BTN_OUTLINE_SM)
        self.btn_edit_settings.setFixedHeight(32)
        self.btn_edit_settings.setCursor(Qt.PointingHandCursor)
        self.btn_edit_settings.setEnabled(False)
        self.btn_edit_settings.clicked.connect(self._open_settings_dialog)

        h_lay.addWidget(btn_back)
        h_lay.addWidget(divider)
        h_lay.addLayout(title_col)
        h_lay.addStretch()
        h_lay.addWidget(self.btn_edit_settings)

        root.addWidget(self.header)

        # ── Chat scroll area ───────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        apply_scroll_area_theme(self.scroll, C['slate_50'])

        self.chat_widget = QWidget()
        self.chat_widget.setStyleSheet(f'background: {C["slate_50"]};')
        self.chat_layout = QVBoxLayout(self.chat_widget)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_layout.setSpacing(0)

        # Inner centering wrapper
        self.inner = QWidget()
        self.inner.setStyleSheet('background: transparent;')
        self.inner.setMaximumWidth(900)
        self.inner_lay = QVBoxLayout(self.inner)
        self.inner_lay.setContentsMargins(40, 32, 40, 32)
        self.inner_lay.setSpacing(18)

        self.chat_layout.addStretch()
        h_wrap = QHBoxLayout()
        h_wrap.addStretch()
        h_wrap.addWidget(self.inner, 2)
        h_wrap.addStretch()
        self.chat_layout.addLayout(h_wrap)

        self.scroll.setWidget(self.chat_widget)
        self.scroll.verticalScrollBar().rangeChanged.connect(self._on_open_scroll_range_changed)
        root.addWidget(self.scroll, 1)

        # Default: empty state
        self._show_empty_state()

    # ── Navigation / data loading ──────────────────────────────────
    def load_data(self, data: dict):
        self._view_token += 1
        self._reset_all()
        self._config = data or {}
        self._session = dict(self._config.get('session') or {})
        self._session_id = self._config.get('sessionId') or self._config.get('session', {}).get('sessionId')
        self.btn_edit_settings.setEnabled(bool(self._session_id))
        self.btn_edit_settings.setText('Изменить настройки')

        if self._session_id:
            self._apply_session_header(self._session or {
                'title': self._config.get('title', 'Сессия выступления'),
                'goal': self._config.get('goal', ''),
                'scenario': self._config.get('goal', ''),
            })
            self._restore_backend_session(self._view_token)
            return

        rehearsal = self._config.get('rehearsal', {})
        self.header_title.setText(rehearsal.get('title', 'Сессия выступления'))
        self.header_sub.setText(rehearsal.get('scenario', ''))
        self.btn_edit_settings.setEnabled(False)
        self._load_existing(rehearsal)

    def showEvent(self, event):
        super().showEvent(event)
        if self._pending_open_scroll_to_bottom or self._pending_open_scroll_widget is not None:
            self._apply_open_scroll_position(self._pending_open_scroll_widget)

    def _on_open_scroll_range_changed(self, _minimum, _maximum):
        if self._pending_open_scroll_to_bottom or self._pending_open_scroll_widget is not None:
            self._apply_open_scroll_position(self._pending_open_scroll_widget)

    def _set_settings_busy(self, busy: bool):
        self._settings_busy = busy
        self.btn_edit_settings.setEnabled(bool(self._session_id) and not busy)
        self.btn_edit_settings.setText('Сохранение...' if busy else 'Изменить настройки')

    def _open_settings_dialog(self):
        if not self._session_id or self._settings_busy:
            return

        dialog = SessionSettingsDialog(self, self._session or {
            'title': self.header_title.text(),
            'goal': self.header_sub.text(),
        }, compact=True)
        if dialog.exec_() != dialog.Accepted:
            return

        self._set_settings_busy(True)
        session_id = self._session_id
        self._start_session_worker(
            session_id,
            lambda: api.update_session(session_id, dialog.payload()),
            self._settings_updated,
            self._settings_update_failed,
        )

    def _settings_updated(self, session: dict):
        self._set_settings_busy(False)
        self._session = dict(session or {})
        self._config['session'] = dict(self._session)
        self._config['title'] = self._session.get('title') or self._config.get('title', '')
        self._config['goal'] = self._session.get('goal') or self._config.get('goal', '')
        self._apply_session_header(self._session)
        self._ensure_settings_prompt_visible()
        show_toast(self, 'Настройки проекта обновлены.', 'success')

    def _settings_update_failed(self, message: str):
        self._set_settings_busy(False)
        show_toast(self, localize_backend_message(message), 'error')

    def _go_back(self):
        self.navigate.emit('dashboard', {'refresh': True})

    def _guarded_callback(self, token, callback):
        def wrapped(*args):
            if token != self._view_token:
                return
            callback(*args)
        return wrapped

    def _guarded_session_callback(self, session_id, callback):
        expected_session_id = str(session_id or '')

        def wrapped(*args):
            if expected_session_id != str(self._session_id or ''):
                return
            callback(*args)
        return wrapped

    def _start_worker(self, fn, on_success, on_failure=None, token=None):
        view_token = self._view_token if token is None else token
        worker = ApiWorker(fn, self)
        worker.succeeded.connect(self._guarded_callback(view_token, on_success))
        if on_failure is None:
            on_failure = self._pipeline_failed
        worker.failed.connect(self._guarded_callback(view_token, on_failure))
        worker.finished.connect(lambda: self._forget_worker(worker))
        self._workers.append(worker)
        worker.start()
        return worker

    def _start_session_worker(self, session_id, fn, on_success, on_failure=None):
        worker = ApiWorker(fn, self)
        worker.succeeded.connect(self._guarded_session_callback(session_id, on_success))
        if on_failure is None:
            on_failure = self._pipeline_failed
        worker.failed.connect(self._guarded_session_callback(session_id, on_failure))
        worker.finished.connect(lambda: self._forget_worker(worker))
        self._workers.append(worker)
        worker.start()
        return worker

    def _clear_inner_layout(self):
        self._upload_zone = None
        self._settings_prompt_widget = None
        self._settings_prompt_signature = None
        while self.inner_lay.count():
            item = self.inner_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _remove_trailing_spacers(self):
        while self.inner_lay.count():
            last_index = self.inner_lay.count() - 1
            item = self.inner_lay.itemAt(last_index)
            if not item or not item.spacerItem():
                return
            self.inner_lay.takeAt(last_index)

    def _remove_upload_zone(self):
        if self._upload_zone is not None:
            self.inner_lay.removeWidget(self._upload_zone)
            self._upload_zone.deleteLater()
            self._upload_zone = None
        self._remove_trailing_spacers()

    def _append_content_widget(self, widget, before_upload_zone=False):
        if before_upload_zone and self._upload_zone is not None:
            index = self.inner_lay.indexOf(self._upload_zone)
            if index >= 0:
                self.inner_lay.insertWidget(index, widget)
                return

        index = self.inner_lay.count()
        if index > 0 and self.inner_lay.itemAt(index - 1).spacerItem():
            index -= 1
        self.inner_lay.insertWidget(index, widget)

    def _add_upload_zone(self):
        self._remove_upload_zone()
        upload_zone = UploadZone()
        upload_zone.file_selected.connect(self._on_file_selected)
        self._upload_zone = upload_zone
        self.inner_lay.addWidget(upload_zone)
        self.inner_lay.addStretch()

    def _add_user_message(self, text: str, *, scroll=True, before_upload_zone=False):
        user_row = QHBoxLayout()
        user_row.addStretch()
        user_row.addWidget(ChatBubbleUser(text))
        user_widget = QWidget()
        user_widget.setStyleSheet('background: transparent;')
        user_widget.setLayout(user_row)
        self._append_content_widget(user_widget, before_upload_zone=before_upload_zone)
        if scroll:
            self._request_scroll_to_bottom()
        return user_widget

    def _add_ai_message(self, text: str):
        ai_row = QHBoxLayout()
        ai_icon = QLabel('âœ¦')
        ai_icon.setFixedSize(32, 32)
        ai_icon.setAlignment(Qt.AlignCenter)
        ai_icon.setStyleSheet(f"""
            background: {C['indigo_100']};
            border-radius: 8px;
            font-size: 15px;
            color: {C['indigo_600']};
            border: none;
        """)
        ai_row.addWidget(ai_icon, 0, Qt.AlignTop)
        ai_row.addWidget(ChatBubbleAI(text))
        ai_row.addStretch()
        ai_w = QWidget()
        ai_w.setStyleSheet('background: transparent;')
        ai_w.setLayout(ai_row)
        self.inner_lay.addWidget(ai_w)

    def _apply_session_header(self, session: dict):
        self.header_title.setText(session.get('title') or 'Сессия выступления')
        self.header_sub.setText(session.get('goal') or session.get('scenario') or '')

    def _ensure_settings_prompt_visible(self, *, scroll=False):
        prompt_text = session_prompt_text(self._session, compact=True)
        if not prompt_text:
            self._remove_settings_prompt()
            return

        signature = session_prompt_signature(self._session, compact=True)
        if self._settings_prompt_widget is not None and self._settings_prompt_signature == signature:
            return

        self._remove_settings_prompt()
        self._settings_prompt_signature = signature
        self._settings_prompt_widget = self._add_user_message(
            prompt_text,
            scroll=scroll,
            before_upload_zone=True,
        )

    def _remove_settings_prompt(self):
        if self._settings_prompt_widget is None:
            self._settings_prompt_signature = None
            return

        self.inner_lay.removeWidget(self._settings_prompt_widget)
        self._settings_prompt_widget.deleteLater()
        self._settings_prompt_widget = None
        self._settings_prompt_signature = None

    def _build_upload_message(self, filename: str, size_str: str) -> str:
        settings_text = session_prompt_text(self._session, compact=True)
        file_text = f'Файл: {filename} ({size_str})'
        if not settings_text:
            return file_text
        return f'{settings_text}\n\n{file_text}'

    def _add_upload_message(self, filename: str, size_str: str, *, scroll=True):
        self._has_attempts = True
        self._add_user_message(self._build_upload_message(filename, size_str), scroll=scroll)

    def _show_session_ready_state(self):
        self._clear_inner_layout()
        self._has_attempts = False
        self._add_upload_zone()
        self._ensure_settings_prompt_visible()

    def _add_report_widget(self, report_data: dict, report_id: str):
        report = PitchReportWidget(
            report_data,
            lambda report_id=report_id: self._on_download_pdf(report_id),
        )
        self.inner_lay.addWidget(report, 0, Qt.AlignTop)
        return report

    def _show_status_state(self, title: str, body: str):
        self._clear_inner_layout()
        wrapper = QWidget()
        wrapper.setStyleSheet('background: transparent;')
        layout = QVBoxLayout(wrapper)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel('âœ¦')
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setFixedSize(64, 64)
        icon_lbl.setStyleSheet(f"""
            background: {C['indigo_100']};
            border-radius: 16px;
            font-size: 30px;
            color: {C['indigo_600']};
            border: none;
        """)
        layout.addWidget(icon_lbl, 0, Qt.AlignCenter)
        layout.addWidget(make_label(title, size=20, weight=QFont.DemiBold,
                                    color=C['slate_900'], align=Qt.AlignHCenter))
        layout.addWidget(make_label(body, size=14, color=C['slate_600'],
                                    align=Qt.AlignHCenter, wrap=True))
        self._add_to_chat(wrapper)
        self.inner_lay.addStretch()

    def _restore_backend_session(self, token: int):
        self._show_status_state(
            'Загрузка статуса выступления',
            'Проверяем загрузки, задачи анализа и отчеты для этой сессии.',
        )
        self._start_worker(
            lambda: self._fetch_backend_session_state(self._session_id),
            self._restore_backend_session_loaded,
            self._restore_backend_session_failed,
            token=token,
        )

    def _fetch_backend_session_state(self, session_id: str) -> dict:
        return {
            'session': api.get_session(session_id),
            'uploads': api.list_uploads(session_id),
            'jobs': api.list_jobs(session_id),
            'reports': api.list_reports(session_id),
        }

    def _restore_backend_session_loaded(self, payload: dict):
        if self._state in ('uploading', 'processing'):
            return

        session = payload.get('session') or {}
        self._session = dict(session)
        attempts = self._build_attempts(
            payload.get('uploads') or [],
            payload.get('jobs') or [],
            payload.get('reports') or [],
        )
        active_job_id = self._find_latest_active_job_id(attempts)

        self._apply_session_header(session or {
                'title': self.header_title.text() or 'Сессия выступления',
            'goal': self.header_sub.text(),
            'scenario': self.header_sub.text(),
        })

        if not attempts:
            self._show_session_ready_state()
            return

        self._cancel_pending_scroll()
        self.setUpdatesEnabled(False)
        try:
            self._clear_inner_layout()
            self._has_attempts = False

            for attempt in attempts:
                upload = attempt.get('upload') or {}
                job = attempt.get('job') or {}
                report = attempt.get('report') or {}
                self._render_uploaded_bubble(upload, scroll=False)

                if report:
                    report_id = str(report.get('reportId') or '')
                    self._report_id = report_id or self._report_id
                    self._add_ai_message('Анализ завершен. Ниже ваш подробный отчет с обратной связью.')
                    self._add_report_widget(self._map_report(report), report_id)
                    continue

                if not job:
                    self._add_ai_message('Аудио загружено. Вы можете продолжить проект, добавив еще одну запись.')
                    continue

                state = str(job.get('status', '')).upper()
                if self._is_failed_state(state):
                    self._add_ai_message(localize_backend_message(job.get('errorMessage')) or 'Не удалось завершить анализ этой записи.')
                    continue

                if self._is_completed_state(state):
                    self._add_ai_message('Анализ завершен, но отчет пока недоступен.')
                    continue

                if str(job.get('jobId') or '') == active_job_id:
                    self._job_id = active_job_id
                    self._start_processing()
                else:
                    self._add_ai_message('Анализ этой записи все еще выполняется.')

            if active_job_id:
                self._start_polling()
                self._apply_open_scroll_position()
                return

            self._state = 'idle'
            self._add_upload_zone()
            self._ensure_settings_prompt_visible()
            self._apply_open_scroll_position()
        finally:
            if not self._pending_open_scroll_to_bottom and self._pending_open_scroll_widget is None:
                self.setUpdatesEnabled(True)
                self.update()

    def _restore_backend_session_failed(self, message: str):
        if self._state in ('uploading', 'processing'):
            return
        self._show_empty_state()
        show_toast(self, localize_backend_message(message), 'error')

    def _render_uploaded_bubble(self, upload: dict, scroll=True):
        filename = upload.get('originalFilename') or upload.get('filename') or 'аудиофайл'
        size_str = self._fmt_size(int(upload.get('sizeBytes') or 0))
        self._add_upload_message(filename, size_str, scroll=scroll)

    def _build_attempts(self, uploads: list, jobs: list, reports: list) -> list[dict]:
        jobs_by_upload = defaultdict(list)
        for job in jobs:
            jobs_by_upload[str(job.get('uploadId') or '')].append(job)

        reports_by_job = {
            str(report.get('jobId') or ''): report
            for report in reports
        }

        attempts = []
        for upload in sorted(uploads, key=lambda item: str(item.get('createdAt') or '')):
            upload_id = str(upload.get('uploadId') or '')
            upload_jobs = sorted(jobs_by_upload.get(upload_id, []), key=lambda item: str(item.get('createdAt') or ''))
            latest_job = upload_jobs[-1] if upload_jobs else {}
            report = reports_by_job.get(str(latest_job.get('jobId') or ''), {})
            attempts.append({
                'upload': upload,
                'job': latest_job,
                'report': report,
            })
        return attempts

    @staticmethod
    def _find_latest_active_job_id(attempts: list[dict]) -> str:
        for attempt in reversed(attempts):
            job = attempt.get('job') or {}
            report = attempt.get('report') or {}
            state = str(job.get('status', '')).upper()
            if job and not report and state and state not in ('DONE', 'COMPLETED', 'SUCCESS', 'FAILED', 'ERROR'):
                return str(job.get('jobId') or '')
        return ''

    @staticmethod
    def _is_completed_state(state: str) -> bool:
        return state in ('DONE', 'COMPLETED', 'SUCCESS')

    @staticmethod
    def _is_failed_state(state: str) -> bool:
        return state in ('FAILED', 'ERROR')

    # ── State management ───────────────────────────────────────────
    def _reset_all(self):
        if self._poll_timer is not None:
            self._poll_timer.stop()
            self._poll_timer = None
        if hasattr(self, '_spin_timer') and self._spin_timer is not None:
            self._spin_timer.stop()
        if hasattr(self, '_prog_timer') and self._prog_timer is not None:
            self._prog_timer.stop()
        self._clear_inner_layout()
        self._state = 'idle'
        self._progress = 0
        self._job_id = None
        self._report_id = None
        self._polling = False
        self._current_pdf_path = None
        self._proc_card = None
        self._prog_card = None
        self._prog_bar = None
        self._prog_lbl = None
        self._upload_zone = None
        self._has_attempts = False
        self._session = {}
        self._settings_prompt_widget = None
        self._settings_prompt_signature = None
        self._set_settings_busy(False)
        self._pending_open_scroll_widget = None
        self._pending_open_scroll_to_bottom = False
        self._cancel_pending_scroll()

    def _cancel_pending_scroll(self):
        self._scroll_request_id += 1

    def _run_requested_scroll(self, request_id: int, callback):
        if request_id != self._scroll_request_id:
            return
        callback()

    def _request_scroll(self, callback):
        self._scroll_request_id += 1
        request_id = self._scroll_request_id
        QTimer.singleShot(
            0,
            lambda request_id=request_id, callback=callback: self._run_requested_scroll(request_id, callback)
        )

    def _scroll_to_bottom(self):
        bar = self.scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _request_scroll_to_bottom(self):
        self._request_scroll(self._scroll_to_bottom)

    def _scroll_to_widget_top(self, widget, margin=16):
        if widget is None:
            return
        bar = self.scroll.verticalScrollBar()
        target_y = widget.mapTo(self.chat_widget, QPoint(0, 0)).y()
        bar.setValue(max(0, target_y - margin))

    def _request_scroll_to_widget_top(self, widget):
        if widget is None:
            return
        self._request_scroll(lambda widget=widget: self._scroll_to_widget_top(widget))

    def _open_scroll_waits_for_range(self) -> bool:
        content_height = max(self.chat_widget.sizeHint().height(), self.inner.sizeHint().height())
        viewport_height = self.scroll.viewport().height()
        return content_height > viewport_height and self.scroll.verticalScrollBar().maximum() <= 0

    def _apply_open_scroll_position(self, widget=None):
        self.chat_layout.activate()
        self.inner_lay.activate()
        self.chat_widget.adjustSize()
        self.inner.adjustSize()
        self._pending_open_scroll_widget = widget
        self._pending_open_scroll_to_bottom = widget is None
        if not self.isVisible():
            return
        if widget is None and self._open_scroll_waits_for_range():
            return
        self._pending_open_scroll_widget = None
        self._pending_open_scroll_to_bottom = False
        if widget is not None:
            self._scroll_to_widget_top(widget)
        else:
            self._scroll_to_bottom()
        if not self.updatesEnabled():
            self.setUpdatesEnabled(True)
            self.update()

    def _add_to_chat(self, widget):
        self.inner_lay.addWidget(widget)
        self._request_scroll_to_bottom()

    # ── Empty state ────────────────────────────────────────────────
    def _show_empty_state(self):
        self._clear_inner_layout()
        self._has_attempts = False
        wrapper = QWidget()
        wrapper.setStyleSheet('background: transparent;')
        w_lay = QVBoxLayout(wrapper)
        w_lay.setSpacing(10)
        w_lay.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel('✦')
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setFixedSize(64, 64)
        icon_lbl.setStyleSheet(f"""
            background: {C['indigo_100']};
            border-radius: 16px;
            font-size: 30px;
            color: {C['indigo_600']};
            border: none;
        """)
        w_lay.addWidget(icon_lbl, 0, Qt.AlignCenter)
        w_lay.addWidget(make_label('Все готово к анализу выступления', size=20,
                                   weight=QFont.DemiBold, color=C['slate_900'],
                                   align=Qt.AlignHCenter))
        w_lay.addWidget(make_label(
            'Загрузите аудиозапись, чтобы получить подробную обратную связь от ИИ',
            size=14, color=C['slate_600'], align=Qt.AlignHCenter, wrap=True
        ))
        self._add_to_chat(wrapper)
        self._add_upload_zone()

    # ── File upload simulation ─────────────────────────────────────
    def _on_file_selected(self, path: str):
        if self._state != 'idle':
            return

        ext = os.path.splitext(path)[1].lower()
        if ext not in ALLOWED_AUDIO_EXTENSIONS:
            show_toast(self, 'Загрузите корректный аудиофайл (MP3, WAV, M4A, MP4)', 'error')
            return

        size = os.path.getsize(path)
        if size > MAX_UPLOAD_SIZE_BYTES:
            show_toast(self, f'Размер файла должен быть меньше {MAX_UPLOAD_SIZE_MB} МБ', 'error')
            return

        if not self._session_id:
            show_toast(self, 'Сначала создайте сессию на сервере, затем загружайте аудио', 'error')
            return

        self._state = 'uploading'
        session_id = self._session_id
        filename = os.path.basename(path)
        size_str = self._fmt_size(size)

        if self._has_attempts or self._settings_prompt_widget is not None:
            self._remove_upload_zone()
            self._remove_settings_prompt()
        else:
            self._clear_inner_layout()

        # User bubble
        self._add_upload_message(filename, size_str)

        # Upload progress card
        self._prog_card = self._make_progress_card(filename, size_str)
        self.inner_lay.addWidget(self._prog_card)
        self.inner_lay.addStretch()

        self._set_upload_progress(10, 'Загрузка на сервер...')
        self._start_session_worker(
            session_id,
            lambda: api.upload_audio(session_id, path),
            self._upload_done,
        )

    def _make_progress_card(self, filename, size_str):
        card = Card(radius=16)
        lay = QHBoxLayout(card)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(16)

        icon_box = QLabel('🎵')
        icon_box.setFixedSize(48, 48)
        icon_box.setAlignment(Qt.AlignCenter)
        icon_box.setStyleSheet(f"""
            background: {C['indigo_100']};
            border-radius: 12px;
            font-size: 22px;
            border: none;
        """)
        lay.addWidget(icon_box, 0, Qt.AlignTop)

        right = QVBoxLayout()
        right.setSpacing(8)
        name_lbl = make_label(filename, size=14, weight=QFont.DemiBold, color=C['slate_900'])
        size_lbl = make_label(size_str, size=13, color=C['slate_500'])
        right.addWidget(name_lbl)
        right.addWidget(size_lbl)

        self._prog_bar = QProgressBar()
        self._prog_bar.setRange(0, 100)
        self._prog_bar.setValue(0)
        self._prog_bar.setFixedHeight(8)
        self._prog_bar.setStyleSheet(PROGRESS_STYLE)
        right.addWidget(self._prog_bar)

        self._prog_lbl = make_label('Загрузка... 0%', size=13, color=C['slate_600'])
        right.addWidget(self._prog_lbl)

        lay.addLayout(right, 1)
        return card

    def _set_upload_progress(self, value: int, message: str):
        self._prog_val = value
        if getattr(self, '_prog_bar', None) is not None:
            self._prog_bar.setValue(value)
        if getattr(self, '_prog_lbl', None) is not None:
            self._prog_lbl.setText(f'{message} {value}%')

    def _tick_upload(self):
        self._prog_val += 10
        self._prog_bar.setValue(self._prog_val)
        self._prog_lbl.setText(f'Загрузка... {self._prog_val}%')
        if self._prog_val >= 100:
            self._prog_timer.stop()
            QTimer.singleShot(200, self._start_processing)

    def _upload_done(self, upload: dict):
        self._set_upload_progress(45, 'Файл загружен. Запускаем анализ...')
        upload_id = upload.get('uploadId')
        if not upload_id:
            self._pipeline_failed('Сервер не вернул uploadId.')
            return
        session_id = self._session_id
        self._start_session_worker(
            session_id,
            lambda: api.create_job(session_id, str(upload_id)),
            self._job_created,
        )

    def _job_created(self, job: dict):
        self._job_id = str(job.get('jobId', ''))
        if not self._job_id:
            self._pipeline_failed('Сервер не вернул jobId.')
            return
        self._set_upload_progress(70, 'Задача анализа создана...')
        self._start_processing()
        self._start_polling()

    # ── Processing ─────────────────────────────────────────────────
    def _start_processing(self):
        self._state = 'processing'
        # Remove progress card
        if hasattr(self, '_prog_card') and self._prog_card is not None:
            self._prog_card.deleteLater()
            self._prog_card = None
            self._prog_bar = None
            self._prog_lbl = None
        self._remove_trailing_spacers()

        # AI typing bubble
        ai_row = QHBoxLayout()
        ai_icon = QLabel('✦')
        ai_icon.setFixedSize(32, 32)
        ai_icon.setAlignment(Qt.AlignCenter)
        ai_icon.setStyleSheet(f"""
            background: {C['indigo_100']};
            border-radius: 8px;
            font-size: 15px;
            color: {C['indigo_600']};
            border: none;
        """)
        ai_row.addWidget(ai_icon, 0, Qt.AlignTop)
        ai_row.addWidget(ChatBubbleAI(
            'Анализирую ваше выступление... Это может занять немного времени, пока я оцениваю '
            'подачу, темп, ясность речи и общее качество выступления.'
        ))
        ai_row.addStretch()
        ai_w = QWidget()
        ai_w.setStyleSheet('background: transparent;')
        ai_w.setLayout(ai_row)
        self.inner_lay.addWidget(ai_w)

        # Processing card
        proc_card = QFrame()
        proc_card.setObjectName('ProcCard')
        proc_card.setStyleSheet(f"""
            QFrame#ProcCard {{
                background: {C['white']};
                border: 1px solid {C['indigo_200']};
                border-radius: 16px;
            }}
        """)
        pc_lay = QVBoxLayout(proc_card)
        pc_lay.setContentsMargins(32, 32, 32, 32)
        pc_lay.setSpacing(12)
        pc_lay.setAlignment(Qt.AlignCenter)

        spin_lbl = QLabel('◌')
        spin_lbl.setAlignment(Qt.AlignCenter)
        spin_lbl.setStyleSheet(
            f'font-size: 40px; color: {C["indigo_600"]}; background: transparent; border: none;'
        )
        pc_lay.addWidget(spin_lbl, 0, Qt.AlignCenter)
        pc_lay.addWidget(make_label('Анализирую ваше выступление...', size=17,
                                    weight=QFont.DemiBold, color=C['slate_900'],
                                    align=Qt.AlignHCenter))
        pc_lay.addWidget(make_label(
            'ИИ оценивает вашу подачу, темп, ясность речи и общее качество выступления.',
            size=14, color=C['slate_600'], wrap=True, align=Qt.AlignHCenter
        ))
        self.inner_lay.addWidget(proc_card)
        self.inner_lay.addStretch()
        self._proc_card = proc_card

        # Animate spinner
        self._spin_chars = ['◌', '○', '◎', '●', '◎', '○']
        self._spin_idx = 0
        self._spin_lbl = spin_lbl
        self._spin_timer = QTimer(self)
        self._spin_timer.timeout.connect(self._tick_spin)
        self._spin_timer.start(200)

    def _tick_spin(self):
        self._spin_lbl.setText(self._spin_chars[self._spin_idx % len(self._spin_chars)])
        self._spin_idx += 1

    def _start_polling(self):
        if self._poll_timer is None:
            self._poll_timer = QTimer(self)
            self._poll_timer.timeout.connect(self._poll_job)
        self._poll_timer.start(2000)
        self._poll_job()

    def _poll_job(self):
        if self._polling or not self._job_id:
            return
        self._polling = True
        session_id = self._session_id
        worker = ApiWorker(lambda: api.get_job(self._job_id), self)
        worker.succeeded.connect(self._guarded_session_callback(session_id, self._job_status_loaded))
        worker.failed.connect(self._guarded_session_callback(session_id, self._pipeline_failed))
        worker.finished.connect(lambda: self._poll_finished(worker))
        self._workers.append(worker)
        worker.start()

    def _poll_finished(self, worker):
        self._polling = False
        self._forget_worker(worker)

    def _job_status_loaded(self, status: dict):
        progress = status.get('progress')
        if progress is not None and getattr(self, '_prog_bar', None) is not None:
            self._prog_bar.setValue(max(0, min(int(progress), 100)))

        state = str(status.get('status', '')).upper()
        stage = localize_job_stage(status.get('currentStage') or state or 'PROCESSING')
        if getattr(self, '_prog_lbl', None) is not None:
            self._prog_lbl.setText(stage)

        if state in ('FAILED', 'ERROR'):
            self._pipeline_failed(localize_backend_message(status.get('errorMessage')) or 'Анализ завершился с ошибкой.')
            return

        report_id = status.get('reportId')
        if self._is_completed_state(state) and report_id:
            if self._poll_timer is not None:
                self._poll_timer.stop()
            self._report_id = str(report_id)
            self._start_session_worker(
                self._session_id,
                lambda: api.get_report(self._report_id),
                self._report_loaded,
            )

    def _report_loaded(self, report: dict):
        self._report_id = str(report.get('reportId') or self._report_id or '')
        self._complete_analysis(self._map_report(report), report_id=self._report_id)

    # ── Analysis complete ──────────────────────────────────────────
    def _complete_analysis(self, report_data=None, show_success_toast=True, report_id=None):
        if hasattr(self, '_spin_timer') and self._spin_timer is not None:
            self._spin_timer.stop()
        self._state = 'success'
        if hasattr(self, '_proc_card') and self._proc_card is not None:
            self._proc_card.deleteLater()
            self._proc_card = None

        self._remove_trailing_spacers()
        resolved_report_id = str(report_id or self._report_id or '')
        self._report_id = resolved_report_id or self._report_id
        self._add_ai_message('Анализ завершен. Ниже ваш подробный отчет с обратной связью.')
        report_widget = self._add_report_widget(report_data or self._build_report_payload(score=0), resolved_report_id)
        self._state = 'idle'
        self._add_upload_zone()
        self._ensure_settings_prompt_visible()

        if show_success_toast:
            show_toast(self, 'Анализ завершен!', 'success')

        self._request_scroll_to_widget_top(report_widget)
        return

        # AI complete message
        ai_row = QHBoxLayout()
        ai_icon = QLabel('✦')
        ai_icon.setFixedSize(32, 32)
        ai_icon.setAlignment(Qt.AlignCenter)
        ai_icon.setStyleSheet(f"""
            background: {C['indigo_100']};
            border-radius: 8px;
            font-size: 15px;
            color: {C['indigo_600']};
            border: none;
        """)
        ai_row.addWidget(ai_icon, 0, Qt.AlignTop)
        ai_row.addWidget(ChatBubbleAI('Анализ завершен. Ниже ваш подробный отчет с обратной связью.'))
        ai_row.addStretch()
        ai_w = QWidget()
        ai_w.setStyleSheet('background: transparent;')
        ai_w.setLayout(ai_row)
        self.inner_lay.addWidget(ai_w)

        # Report widget
        report = PitchReportWidget(report_data or self._build_report_payload(score=0), self._on_download_pdf)
        self.inner_lay.addWidget(report, 0, Qt.AlignTop)
        self.inner_lay.addStretch()

        if show_success_toast:
            show_toast(self, 'Анализ завершен!', 'success')

        QTimer.singleShot(100, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))

    # ── Existing rehearsal ─────────────────────────────────────────
    def _load_existing(self, rehearsal: dict):
        report_data = self._build_report_payload(
            score=self._score(rehearsal.get('score', 87)),
            current_length=str(rehearsal.get('duration') or '').strip(),
        )

        user_row = QHBoxLayout()
        user_row.addStretch()
        user_row.addWidget(
            ChatBubbleUser(
                f"Загружено: {rehearsal.get('title', 'выступление')}.mp3 "
                f"({rehearsal.get('duration', '')})"
            )
        )
        user_w = QWidget()
        user_w.setStyleSheet('background: transparent;')
        user_w.setLayout(user_row)
        self.inner_lay.addWidget(user_w)

        ai_row = QHBoxLayout()
        ai_icon = QLabel('✦')
        ai_icon.setFixedSize(32, 32)
        ai_icon.setAlignment(Qt.AlignCenter)
        ai_icon.setStyleSheet(f"""
            background: {C['indigo_100']};
            border-radius: 8px;
            font-size: 15px;
            color: {C['indigo_600']};
            border: none;
        """)
        ai_row.addWidget(ai_icon, 0, Qt.AlignTop)
        ai_row.addWidget(ChatBubbleAI(
            "Готово! Я проанализировал ваше выступление. Ниже подробный отчет с обратной связью."
        ))
        ai_row.addStretch()
        ai_w = QWidget()
        ai_w.setStyleSheet('background: transparent;')
        ai_w.setLayout(ai_row)
        self.inner_lay.addWidget(ai_w)

        report = PitchReportWidget(report_data, self._on_download_pdf)
        self.inner_lay.addWidget(report, 0, Qt.AlignTop)
        self.inner_lay.addStretch()
        self._state = 'success'
        self._apply_open_scroll_position()

    # ── Helpers ────────────────────────────────────────────────────
    @staticmethod
    def _fmt_size(b):
        if b < 1024:
            return f'{b} B'
        if b < 1024 ** 2:
            return f'{b/1024:.1f} KB'
        return f'{b/1024**2:.1f} MB'

    def _map_report(self, report: dict) -> dict:
        analysis_meta = report.get('analysisMeta') or {}
        return self._build_report_payload(
            score=self._score(report.get('overallScore')),
            strengths=report.get('strengths') or [],
            blockers=report.get('improvements') or [],
            recommendations=report.get('recommendations') or [],
            current_length=self._report_duration_label(report),
            next_version_changes=report.get('nextVersionChanges') or [],
            next_version=report.get('nextVersion') or {},
            recommendations_summary=report.get('recommendationsSummary') or [],
            recommendation_details=report.get('recommendationDetails') or [],
            analysis_meta=analysis_meta,
        )

    def _build_report_payload(
        self,
        *,
        score: int,
        strengths: list[str] | None = None,
        blockers: list[str] | None = None,
        recommendations: list[str] | None = None,
        current_length: str = '',
        next_version_changes: list[str] | None = None,
        next_version: dict | None = None,
        recommendations_summary: list[str] | None = None,
        recommendation_details: list[dict] | None = None,
        analysis_meta: dict | None = None,
    ) -> dict:
        strengths = [str(item).strip() for item in (strengths or []) if str(item).strip()]
        blockers = [str(item).strip() for item in (blockers or []) if str(item).strip()]
        recommendations = [str(item).strip() for item in (recommendations or []) if str(item).strip()]
        next_version_changes = [str(item).strip() for item in (next_version_changes or []) if str(item).strip()]
        recommendations_summary = [str(item).strip() for item in (recommendations_summary or []) if str(item).strip()]

        report_data = {
            'reportTitle': '\u0420\u0430\u0437\u0431\u043e\u0440 \u0442\u0435\u043a\u0443\u0449\u0435\u0439 \u0432\u0435\u0440\u0441\u0438\u0438 \u043f\u0438\u0442\u0447\u0430',
            'reportSubtitle': '\u0427\u0442\u043e \u0438\u0441\u043f\u0440\u0430\u0432\u0438\u0442\u044c \u043f\u0435\u0440\u0435\u0434 \u0441\u043b\u0435\u0434\u0443\u044e\u0449\u0438\u043c \u0432\u044b\u0441\u0442\u0443\u043f\u043b\u0435\u043d\u0438\u0435\u043c',
            'context': {},
            'strengths': strengths[:4],
            'blockers': blockers[:4],
            'nextVersionChanges': next_version_changes[:5],
            'nextVersion': self._map_next_version(next_version),
            'recommendationsSummary': recommendations_summary[:7] or recommendations[:7],
            'recommendations': self._map_recommendation_details(recommendation_details),
        }
        report_data['statusPill'] = self._report_status_label(score)
        report_data['statusSummary'] = self._report_status_summary(score, strengths, blockers)

        context = dict(report_data.get('context') or {})
        session = self._session or self._config.get('session') or {}
        analysis_meta = analysis_meta or {}

        duration_target_seconds = self._as_int(session.get('durationTargetSeconds')) or self._as_int(analysis_meta.get('targetDurationSec'))
        if duration_target_seconds:
            context['timeLimit'] = format_duration_text(duration_target_seconds)

        if current_length:
            context['currentLength'] = current_length

        report_data['context'] = context
        return report_data

    @staticmethod
    def _report_status_label(score: int) -> str:
        if score >= 90:
            return 'Готово к финальному прогону'
        if score >= 75:
            return 'Близко к готовому'
        return 'Нужна одна сильная итерация правок'

    def _report_status_summary(self, score: int, strengths: list[str], blockers: list[str]) -> str:
        if score >= 90:
            return (
                'Версия уже звучит собранно и уверенно. Следующий шаг — полировка формулировок '
                'и более точная подача ключевых тезисов.'
            )
        if score >= 75:
            if blockers:
                return (
                    'Основа уже сильная, но есть несколько мест, которые еще тормозят убедительность. '
                    f'В первую очередь стоит добить: {blockers[0]}'
                )
            return 'Основа уже сильная, но для следующей версии все еще нужна точечная редактура структуры и подачи.'
        if strengths:
            return (
                'В материале уже есть рабочая база, но текущая версия пока не держит одну собранную линию. '
                f'Сохраняем сильную сторону: {strengths[0]}'
            )
        return (
            'Питч уже содержит полезный материал, но пока не собран в одну убедительную историю. '
            'Следующая итерация должна сократить лишнее и усилить структуру.'
        )

    @staticmethod
    def _report_duration_label(report: dict) -> str:
        for key in ('durationSeconds', 'audioDurationSeconds', 'transcriptDurationSeconds', 'durationSec'):
            try:
                seconds = int(report.get(key) or 0)
            except (TypeError, ValueError):
                seconds = 0
            if seconds > 0:
                minutes, remainder = divmod(seconds, 60)
                return f'~{minutes}:{remainder:02d}'
        analysis_meta = report.get('analysisMeta') or {}
        actual_duration = str(analysis_meta.get('actualDuration') or '').strip()
        if actual_duration:
            return f'~{actual_duration}'
        return ''

    @staticmethod
    def _build_recommendation_cards(blockers: list[str], recommendations: list[str]) -> list[dict]:
        sections = ['Структура', 'Аргумент', 'Подача', 'Финал']
        cards = []
        for index, recommendation in enumerate(recommendations[:4]):
            blocker = blockers[index] if index < len(blockers) else 'Текущая формулировка звучит слабее и требует уточнения.'
            cards.append({
                'id': f'generated-{index + 1}',
                'section': sections[index] if index < len(sections) else f'Рекомендация {index + 1}',
                'before': blocker,
                'after': recommendation,
                'whyOldWasWeaker': 'Текущая версия создает лишнюю когнитивную нагрузку и замедляет понимание сути.',
                'whyNewIsBetter': 'Новая формулировка быстрее доводит до ключевого вывода и усиливает ощущение контроля.',
                'whatAudienceUnderstands': 'Главную мысль быстрее, с меньшим количеством лишних допущений.',
                'whatAudienceFeels': 'Больше уверенности в спикере и в логике самого питча.',
            })
        return cards or deepcopy(MOCK_REPORT['recommendations'])

    @staticmethod
    def _map_next_version(next_version: dict | None) -> dict:
        next_version = next_version or {}
        blocks = []
        for index, block in enumerate(next_version.get('blocks') or []):
            if not isinstance(block, dict):
                continue
            title = str(block.get('title') or block.get('label') or '').strip()
            content = str(block.get('content') or block.get('text') or '').strip()
            if title and content:
                blocks.append({
                    'id': f'next-version-{index + 1}',
                    'title': title,
                    'content': content,
                })
        return {
            'title': str(next_version.get('title') or 'Ð¡Ð»ÐµÐ´ÑƒÑŽÑ‰Ð°Ñ Ð²ÐµÑ€ÑÐ¸Ñ pitch').strip() or 'Ð¡Ð»ÐµÐ´ÑƒÑŽÑ‰Ð°Ñ Ð²ÐµÑ€ÑÐ¸Ñ pitch',
            'fullText': str(next_version.get('fullText') or next_version.get('full_text') or '').strip(),
            'blocks': blocks,
            'note': str(next_version.get('note') or '').strip(),
        }

    @staticmethod
    def _map_recommendation_details(recommendation_details: list[dict] | None) -> list[dict]:
        cards = []
        for index, change in enumerate(recommendation_details or []):
            if not isinstance(change, dict):
                continue
            audience_effect = change.get('audienceEffect') or {}
            if not isinstance(audience_effect, dict):
                audience_effect = {}
            cards.append({
                'id': f'real-{index + 1}',
                'section': str(change.get('title') or f'Ð ÐµÐºÐ¾Ð¼ÐµÐ½Ð´Ð°Ñ†Ð¸Ñ {index + 1}').strip(),
                'before': str(change.get('before') or '').strip(),
                'after': str(change.get('after') or '').strip(),
                'whyOldWasWeaker': str(change.get('whyBeforeWeaker') or '').strip(),
                'whyNewIsBetter': str(change.get('whyAfterBetter') or '').strip(),
                'whatAudienceUnderstands': str(audience_effect.get('understandsBetter') or '').strip(),
                'whatAudienceFeels': str(audience_effect.get('feelsMore') or '').strip(),
            })
        return cards

    @staticmethod
    def _as_int(value) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _score(value) -> int:
        try:
            return max(0, min(int(value), 100))
        except (TypeError, ValueError):
            return 0

    def _pipeline_failed(self, message: str):
        message = localize_backend_message(message)
        self._state = 'error'
        self._polling = False
        if self._poll_timer is not None:
            self._poll_timer.stop()
        if hasattr(self, '_spin_timer') and self._spin_timer is not None:
            self._spin_timer.stop()
        if getattr(self, '_proc_card', None) is not None:
            self._proc_card.deleteLater()
            self._proc_card = None
        if getattr(self, '_prog_card', None) is not None:
            self._prog_card.deleteLater()
            self._prog_card = None
            self._prog_bar = None
            self._prog_lbl = None
        self._remove_upload_zone()
        self._remove_trailing_spacers()
        self._add_ai_message(message)
        self._state = 'idle'
        if self._session_id:
            self._add_upload_zone()
            self._ensure_settings_prompt_visible()
        show_toast(self, message, 'error')

    def _forget_worker(self, worker):
        if worker in self._workers:
            self._workers.remove(worker)

    def _on_download_pdf(self, report_id=None):
        resolved_report_id = str(report_id or self._report_id or '')
        if not resolved_report_id:
            show_toast(self, 'PDF-отчет для этого элемента недоступен.', 'error')
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            'Сохранить PDF-отчет',
            f'speechgym-report-{resolved_report_id}.pdf',
            'PDF-файлы (*.pdf);;Все файлы (*)',
        )
        if not path:
            return

        self._current_pdf_path = path
        worker = ApiWorker(lambda: api.download_pdf(resolved_report_id), self)
        worker.succeeded.connect(self._pdf_downloaded)
        worker.failed.connect(lambda message: show_toast(self, localize_backend_message(message), 'error'))
        worker.finished.connect(lambda: self._forget_worker(worker))
        self._workers.append(worker)
        worker.start()

    def _pdf_downloaded(self, content: bytes):
        with open(self._current_pdf_path, 'wb') as pdf_file:
            pdf_file.write(content)
        show_toast(self, 'PDF-отчет успешно скачан', 'success')
