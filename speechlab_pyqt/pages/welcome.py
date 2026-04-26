# pages/welcome.py — Welcome / landing page

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from styles import C, BTN_PRIMARY_LG, BTN_OUTLINE_LG
from widgets import Card, IconBox, BadgePill, make_label


class WelcomePage(QWidget):
    navigate = pyqtSignal(str, object)

    def __init__(self):
        super().__init__()
        self.setObjectName('WelcomePage')
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QWidget#WelcomePage {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {C['bg_grad_0']}, stop:0.5 {C['bg_grad_1']}, stop:1 {C['bg_grad_2']}
                );
            }}
        """)
        self._build()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(80, 60, 80, 60)
        root.setSpacing(64)

        # ── LEFT SIDE ──────────────────────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(0)

        # Badge pill
        badge = BadgePill('✦', '',
                          bg=C['indigo_100'] + 'AA',
                          border=C['indigo_200'],
                          icon_color=C['indigo_600'],
                          text_color=C['indigo_900'])
        badge.hide()
        left.addWidget(badge, 0, Qt.AlignLeft)
        left.addSpacing(0)

        # Hero title (rich-text label)
        title = QLabel()
        title.setTextFormat(Qt.RichText)
        title.setText(
            f'<span style="font-size:42px; font-weight:700; color:{C["slate_900"]};">'
            f'Master Your<br>'
            f'<span style="color:{C["indigo_600"]};">Public Speaking</span>'
            f'</span>'
        )
        title.setWordWrap(True)
        title.setStyleSheet('background: transparent; border: none;')
        left.addWidget(title)
        left.addSpacing(18)

        # Sub-description
        desc = make_label(
            'Practice presentations with confidence. Upload your rehearsals and '
            'receive detailed AI-generated feedback to improve your delivery, pace, and impact.',
            size=16, color=C['slate_600'], wrap=True
        )
        left.addWidget(desc)
        left.addSpacing(30)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_start = QPushButton('Зарегистрироваться')
        btn_start.setStyleSheet(BTN_PRIMARY_LG)
        btn_start.setFixedHeight(48)
        btn_start.setCursor(Qt.PointingHandCursor)
        btn_start.clicked.connect(lambda: self.navigate.emit('signup', None))

        btn_login = QPushButton('Войти')
        btn_login.setStyleSheet(BTN_OUTLINE_LG)
        btn_login.setFixedHeight(48)
        btn_login.setCursor(Qt.PointingHandCursor)
        btn_login.clicked.connect(lambda: self.navigate.emit('login', None))

        btn_row.addWidget(btn_start)
        btn_row.addWidget(btn_login)
        btn_row.addStretch()
        left.addLayout(btn_row)
        left.addSpacing(38)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f'color: {C["slate_200"]}; background: {C["slate_200"]};')
        sep.setFixedHeight(0)
        left.addWidget(sep)
        left.addSpacing(0)

        # Stats row
        stats_row = QHBoxLayout()
        stats_row.setSpacing(0)
        for i, (val, lbl_text) in enumerate([]):
            col = QVBoxLayout()
            col.setSpacing(4)
            v = make_label(val, size=28, weight=QFont.Bold, color=C['indigo_600'])
            l = make_label(lbl_text, size=13, color=C['slate_600'])
            col.addWidget(v)
            col.addWidget(l)
            stats_row.addLayout(col)
            if i < 2:
                stats_row.addStretch()
        # Stats were removed from the landing requirements.
        left.addStretch()

        # ── RIGHT SIDE ─────────────────────────────────────────────
        right = QVBoxLayout()
        right.setSpacing(16)

        feature_cards = [
            ('🎙', 'Upload & Rehearse',
             'Simply upload your practice recording and let our AI analyze '
             'your performance in real-time.',
             C['indigo_100'], C['indigo_600']),
            ('📊', 'Detailed Analytics',
             'Get insights on pace, clarity, filler words, confidence, and '
             'emotional tone with actionable metrics.',
             C['blue_100'], C['blue_600']),
            ('📄', 'Professional Reports',
             'Receive comprehensive PDF feedback reports you can save and '
             'review before your big presentation.',
             C['violet_100'], C['violet_600']),
        ]

        for icon, title_text, body_text, icon_bg, icon_fg in feature_cards:
            card = Card(radius=16)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(24, 24, 24, 24)
            cl.setSpacing(12)

            ib = IconBox(icon, size=48, bg=icon_bg, fg=icon_fg, radius=12, font_size=22)
            cl.addWidget(ib, 0, Qt.AlignLeft)

            ct = make_label(title_text, size=16, weight=QFont.DemiBold,
                            color=C['slate_900'])
            cl.addWidget(ct)

            cb = make_label(body_text, size=14, color=C['slate_600'], wrap=True)
            cl.addWidget(cb)

            right.addWidget(card)

        right.addStretch()

        # ── COMBINE ────────────────────────────────────────────────
        left_w = QWidget()
        left_w.setStyleSheet('background: transparent;')
        left_w.setLayout(left)
        left_w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        right_w = QWidget()
        right_w.setStyleSheet('background: transparent;')
        right_w.setLayout(right)
        right_w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_w.setMinimumWidth(360)
        right_w.setMaximumWidth(500)

        root.addWidget(left_w, 1)
        root.addWidget(right_w, 1)
