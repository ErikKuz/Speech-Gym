# pages/rehearsal_chat.py — Rehearsal chat / upload / analysis page

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy, QFileDialog, QProgressBar,
    QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QDragEnterEvent, QDropEvent

from styles import (C, BTN_OUTLINE_SM, BTN_PRIMARY,
                    BTN_WHITE_TRANSPARENT, PROGRESS_STYLE, SCROLLBAR_STYLE)
from api_client import ApiWorker, api
from widgets import (Card, BadgePill, ScoreCircle, SmallScoreCircle,
                     NumberCircle, Separator, make_label, show_toast)

# ── Mock analysis data ─────────────────────────────────────────────────────────
MOCK_REPORT = {
    'overallScore': 87,
    'clarity': 85,
    'pace': 88,
    'fillerWords': 12,
    'confidence': 90,
    'structure': 87,
    'emotionalTone': 83,
    'strengths': [
        'Strong opening that captures attention immediately',
        'Clear articulation and pronunciation throughout',
        'Good use of pauses for emphasis',
        'Confident body language and vocal tone',
    ],
    'weaknesses': [
        "Slight tendency to rush through complex topics",
        "Could benefit from more varied vocal inflection",
        "A few instances of filler words ('um', 'uh') during transitions",
    ],
    'recommendations': [
        'Practice breathing exercises before presentations to maintain steady pace',
        'Use sticky notes with key transitions to reduce reliance on filler words',
        'Record yourself and listen back to identify patterns in vocal variety',
        'Consider adding one more strategic pause before key points',
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
        header.setStyleSheet("""
            QFrame#RHeader {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4F46E5, stop:1 #2563EB
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
        h_title = QLabel('Speech Analysis Report')
        h_title.setStyleSheet('color: white; font-size: 20px; font-weight: 700; '
                              'background: transparent; border: none;')
        h_sub = QLabel('AI-Generated Feedback & Insights')
        h_sub.setStyleSheet('color: rgba(199,210,254,1); font-size: 13px; '
                            'background: transparent; border: none;')
        h_text.addWidget(h_title)
        h_text.addWidget(h_sub)

        btn_dl = QPushButton('⬇  Save PDF')
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
        ov_lbl = QLabel('OVERALL SCORE')
        ov_lbl.setAlignment(Qt.AlignCenter)
        ov_lbl.setStyleSheet(f'font-size: 11px; font-weight: 600; color: {C["slate_600"]}; '
                             f'letter-spacing: 1px; background: transparent; border: none;')
        score_circle = ScoreCircle(data['overallScore'], size=112)
        perf_txt = 'Excellent performance!' if data['overallScore'] >= 85 \
            else ('Good performance!' if data['overallScore'] >= 70 else 'Room for improvement')
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
        b_lay.addWidget(make_label('Performance Metrics', size=15, weight=QFont.DemiBold,
                                   color=C['slate_900']))
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(12)
        metrics = [
            ('Clarity', data['clarity']),
            ('Pace', data['pace']),
            ('Confidence', data['confidence']),
            ('Structure', data['structure']),
            ('Emotional Tone', data['emotionalTone']),
            ('Filler Words', 100 - data['fillerWords']),
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
        s_header.addWidget(make_label('Strengths', size=15, weight=QFont.DemiBold,
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
        w_header.addWidget(make_label('Areas for Improvement', size=15,
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
        rec_header.addWidget(make_label('Actionable Recommendations', size=15,
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
        f_lbl = QLabel(f"Generated by SpeechLab AI  •  {date.today().strftime('%B %d, %Y')}")
        f_lbl.setAlignment(Qt.AlignCenter)
        f_lbl.setStyleSheet(f'font-size: 12px; color: {C["slate_500"]}; '
                            f'background: transparent; border: none;')
        f_lay.addStretch()
        f_lay.addWidget(f_lbl)
        f_lay.addStretch()
        root.addWidget(footer)


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

        lay.addWidget(make_label('Upload your rehearsal audio', size=17,
                                 weight=QFont.DemiBold, color=C['slate_900'],
                                 align=Qt.AlignHCenter))
        lay.addWidget(make_label('Drag and drop your audio file here, or click to browse',
                                 size=14, color=C['slate_600'], align=Qt.AlignHCenter))

        btn = QPushButton('⬆  Choose File')
        btn.setStyleSheet(BTN_PRIMARY)
        btn.setFixedHeight(40)
        btn.setFixedWidth(160)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self._open_dialog)
        lay.addWidget(btn, 0, Qt.AlignCenter)

        lay.addWidget(make_label('Supports MP3, WAV, M4A  •  Max file size: 50 MB',
                                 size=12, color=C['slate_500'], align=Qt.AlignHCenter))

    def _open_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, 'Select Audio File', '',
            'Audio Files (*.mp3 *.wav *.m4a *.mp4);;All Files (*)'
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

        btn_back = QPushButton('← Back to Dashboard')
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

        self.header_title = make_label('Rehearsal Session', size=14,
                                       weight=QFont.DemiBold, color=C['slate_900'])
        self.header_sub = make_label('', size=13, color=C['slate_500'])

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_col.addWidget(self.header_title)
        title_col.addWidget(self.header_sub)

        h_lay.addWidget(btn_back)
        h_lay.addWidget(divider)
        h_lay.addLayout(title_col)
        h_lay.addStretch()

        root.addWidget(self.header)

        # ── Chat scroll area ───────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet(SCROLLBAR_STYLE)

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
        root.addWidget(self.scroll, 1)

        # Default: empty state
        self._show_empty_state()

    # ── Navigation / data loading ──────────────────────────────────
    def load_data(self, data: dict):
        self._reset_all()
        self._config = data
        self._session_id = data.get('sessionId') or data.get('session', {}).get('sessionId')

        if data.get('is_new') or self._session_id:
            self.header_title.setText(data.get('title', 'New Rehearsal'))
            self.header_sub.setText(data.get('goal', ''))
            self._show_empty_state()
        else:
            rehearsal = data.get('rehearsal', {})
            self.header_title.setText(rehearsal.get('title', 'Rehearsal Session'))
            self.header_sub.setText(rehearsal.get('scenario', ''))
            self._load_existing(rehearsal)

    def _go_back(self):
        self.navigate.emit('dashboard', {'refresh': True})

    # ── State management ───────────────────────────────────────────
    def _reset_all(self):
        if self._poll_timer is not None:
            self._poll_timer.stop()
            self._poll_timer = None
        if hasattr(self, '_spin_timer') and self._spin_timer is not None:
            self._spin_timer.stop()
        if hasattr(self, '_prog_timer') and self._prog_timer is not None:
            self._prog_timer.stop()
        # Remove all widgets from inner_lay
        while self.inner_lay.count():
            item = self.inner_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._state = 'idle'
        self._progress = 0
        self._job_id = None
        self._report_id = None
        self._polling = False
        self._current_pdf_path = None

    def _add_to_chat(self, widget):
        self.inner_lay.addWidget(widget)
        # Scroll to bottom
        QTimer.singleShot(50, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))

    # ── Empty state ────────────────────────────────────────────────
    def _show_empty_state(self):
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
        w_lay.addWidget(make_label('Ready to analyze your rehearsal', size=20,
                                   weight=QFont.DemiBold, color=C['slate_900'],
                                   align=Qt.AlignHCenter))
        w_lay.addWidget(make_label(
            'Upload your audio recording to receive detailed AI-powered feedback',
            size=14, color=C['slate_600'], align=Qt.AlignHCenter, wrap=True
        ))
        self._add_to_chat(wrapper)

        # Upload zone
        upload_zone = UploadZone()
        upload_zone.file_selected.connect(self._on_file_selected)
        self.inner_lay.addWidget(upload_zone)
        self.inner_lay.addStretch()

    # ── File upload simulation ─────────────────────────────────────
    def _on_file_selected(self, path: str):
        if self._state != 'idle':
            return

        ext = os.path.splitext(path)[1].lower()
        if ext not in ('.mp3', '.wav', '.m4a', '.mp4'):
            show_toast(self, 'Please upload a valid audio file (MP3, WAV, M4A)', 'error')
            return

        size = os.path.getsize(path)
        if size > 50 * 1024 * 1024:
            show_toast(self, 'File size must be less than 50 MB', 'error')
            return

        if not self._session_id:
            show_toast(self, 'Create a backend session before uploading audio', 'error')
            return

        self._state = 'uploading'

        # Clear inner layout
        while self.inner_lay.count():
            item = self.inner_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # User bubble
        filename = os.path.basename(path)
        size_str = self._fmt_size(size)
        user_row = QHBoxLayout()
        user_row.addStretch()
        user_row.addWidget(ChatBubbleUser(f'Uploaded: {filename} ({size_str})'))
        user_w = QWidget()
        user_w.setStyleSheet('background: transparent;')
        user_w.setLayout(user_row)
        self.inner_lay.addWidget(user_w)

        # Upload progress card
        self._prog_card = self._make_progress_card(filename, size_str)
        self.inner_lay.addWidget(self._prog_card)
        self.inner_lay.addStretch()

        self._set_upload_progress(10, 'Uploading to backend...')
        worker = ApiWorker(lambda: api.upload_audio(self._session_id, path), self)
        worker.succeeded.connect(self._upload_done)
        worker.failed.connect(self._pipeline_failed)
        worker.finished.connect(lambda: self._forget_worker(worker))
        self._workers.append(worker)
        worker.start()

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

        self._prog_lbl = make_label('Uploading... 0%', size=13, color=C['slate_600'])
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
        self._prog_lbl.setText(f'Uploading... {self._prog_val}%')
        if self._prog_val >= 100:
            self._prog_timer.stop()
            QTimer.singleShot(200, self._start_processing)

    def _upload_done(self, upload: dict):
        self._set_upload_progress(45, 'Upload stored. Starting analysis...')
        upload_id = upload.get('uploadId')
        if not upload_id:
            self._pipeline_failed('Backend did not return uploadId.')
            return
        worker = ApiWorker(lambda: api.create_job(self._session_id, str(upload_id)), self)
        worker.succeeded.connect(self._job_created)
        worker.failed.connect(self._pipeline_failed)
        worker.finished.connect(lambda: self._forget_worker(worker))
        self._workers.append(worker)
        worker.start()

    def _job_created(self, job: dict):
        self._job_id = str(job.get('jobId', ''))
        if not self._job_id:
            self._pipeline_failed('Backend did not return jobId.')
            return
        self._set_upload_progress(70, 'Analysis queued...')
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
        # Remove stretch
        while self.inner_lay.count():
            item = self.inner_lay.itemAt(self.inner_lay.count() - 1)
            if item and item.spacerItem():
                self.inner_lay.removeItem(item)
                break

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
            'Analyzing your rehearsal... This may take a moment while I evaluate '
            'your delivery, pace, clarity, and overall performance.'
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
        pc_lay.addWidget(make_label('Analyzing your rehearsal...', size=17,
                                    weight=QFont.DemiBold, color=C['slate_900'],
                                    align=Qt.AlignHCenter))
        pc_lay.addWidget(make_label(
            'Our AI is evaluating your delivery, pace, clarity, and overall performance.',
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
        worker = ApiWorker(lambda: api.get_job(self._job_id), self)
        worker.succeeded.connect(self._job_status_loaded)
        worker.failed.connect(self._pipeline_failed)
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
        stage = status.get('currentStage') or state or 'Processing'
        if getattr(self, '_prog_lbl', None) is not None:
            self._prog_lbl.setText(stage)

        if state in ('FAILED', 'ERROR'):
            self._pipeline_failed(status.get('errorMessage') or 'Analysis failed.')
            return

        report_id = status.get('reportId')
        if state in ('DONE', 'COMPLETED', 'SUCCESS') and report_id:
            if self._poll_timer is not None:
                self._poll_timer.stop()
            self._report_id = str(report_id)
            worker = ApiWorker(lambda: api.get_report(self._report_id), self)
            worker.succeeded.connect(self._report_loaded)
            worker.failed.connect(self._pipeline_failed)
            worker.finished.connect(lambda: self._forget_worker(worker))
            self._workers.append(worker)
            worker.start()

    def _report_loaded(self, report: dict):
        self._report_id = str(report.get('reportId') or self._report_id or '')
        self._complete_analysis(self._map_report(report))

    # ── Analysis complete ──────────────────────────────────────────
    def _complete_analysis(self, report_data=None):
        if hasattr(self, '_spin_timer') and self._spin_timer is not None:
            self._spin_timer.stop()
        self._state = 'success'
        if hasattr(self, '_proc_card') and self._proc_card is not None:
            self._proc_card.deleteLater()

        # Remove stretch
        while self.inner_lay.count():
            item = self.inner_lay.itemAt(self.inner_lay.count() - 1)
            if item and item.spacerItem():
                self.inner_lay.removeItem(item)
                break

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
        ai_row.addWidget(ChatBubbleAI('Analysis complete! Here\'s your detailed feedback report:'))
        ai_row.addStretch()
        ai_w = QWidget()
        ai_w.setStyleSheet('background: transparent;')
        ai_w.setLayout(ai_row)
        self.inner_lay.addWidget(ai_w)

        # Report widget
        report = ReportWidget(report_data or MOCK_REPORT, self._on_download_pdf)
        self.inner_lay.addWidget(report)
        self.inner_lay.addStretch()

        show_toast(self, 'Analysis complete!', 'success')

        QTimer.singleShot(100, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))

    # ── Existing rehearsal ─────────────────────────────────────────
    def _load_existing(self, rehearsal: dict):
        report_data = dict(MOCK_REPORT)
        report_data['overallScore'] = rehearsal.get('score', 87)

        user_row = QHBoxLayout()
        user_row.addStretch()
        user_row.addWidget(
            ChatBubbleUser(
                f"Uploaded: {rehearsal.get('title', 'rehearsal')}.mp3 "
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
            "Great! I've analyzed your rehearsal. Here's your detailed feedback report:"
        ))
        ai_row.addStretch()
        ai_w = QWidget()
        ai_w.setStyleSheet('background: transparent;')
        ai_w.setLayout(ai_row)
        self.inner_lay.addWidget(ai_w)

        report = ReportWidget(report_data, self._on_download_pdf)
        self.inner_lay.addWidget(report)
        self.inner_lay.addStretch()
        self._state = 'success'

    # ── Helpers ────────────────────────────────────────────────────
    @staticmethod
    def _fmt_size(b):
        if b < 1024:
            return f'{b} B'
        if b < 1024 ** 2:
            return f'{b/1024:.1f} KB'
        return f'{b/1024**2:.1f} MB'

    def _map_report(self, report: dict) -> dict:
        filler_count = int(report.get('fillerWordsCount') or 0)
        pace_wpm = int(report.get('paceWpm') or 0)
        pace_score = self._score(100 - abs(pace_wpm - 140)) if pace_wpm else 0
        confidence = self._score(report.get('confidence'))
        return {
            'overallScore': self._score(report.get('overallScore')),
            'clarity': self._score(report.get('clarity')),
            'pace': pace_score,
            'fillerWords': max(0, min(filler_count, 100)),
            'confidence': confidence,
            'structure': self._score(report.get('structure')),
            'emotionalTone': confidence,
            'strengths': report.get('strengths') or ['Report generated successfully.'],
            'weaknesses': report.get('improvements') or ['No specific improvements returned.'],
            'recommendations': report.get('recommendations') or ['Keep practicing with new recordings.'],
        }

    @staticmethod
    def _score(value) -> int:
        try:
            return max(0, min(int(value), 100))
        except (TypeError, ValueError):
            return 0

    def _pipeline_failed(self, message: str):
        self._state = 'error'
        self._polling = False
        if self._poll_timer is not None:
            self._poll_timer.stop()
        if hasattr(self, '_spin_timer') and self._spin_timer is not None:
            self._spin_timer.stop()
        show_toast(self, message, 'error')

    def _forget_worker(self, worker):
        if worker in self._workers:
            self._workers.remove(worker)

    def _on_download_pdf(self):
        if not self._report_id:
            show_toast(self, 'PDF report downloaded successfully', 'success')
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            'Save PDF Report',
            f'speechgym-report-{self._report_id}.pdf',
            'PDF Files (*.pdf);;All Files (*)',
        )
        if not path:
            return

        self._current_pdf_path = path
        worker = ApiWorker(lambda: api.download_pdf(self._report_id), self)
        worker.succeeded.connect(self._pdf_downloaded)
        worker.failed.connect(lambda message: show_toast(self, message, 'error'))
        worker.finished.connect(lambda: self._forget_worker(worker))
        self._workers.append(worker)
        worker.start()

    def _pdf_downloaded(self, content: bytes):
        with open(self._current_pdf_path, 'wb') as pdf_file:
            pdf_file.write(content)
        show_toast(self, 'PDF report downloaded successfully', 'success')
