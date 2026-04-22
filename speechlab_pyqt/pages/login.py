# pages/login.py — Login page

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from styles import C, BTN_PRIMARY, INPUT_STYLE, CHECKBOX_STYLE
from api_client import ApiWorker, api
from widgets import Card, IconBox, make_label, show_toast


class LoginPage(QWidget):
    navigate = pyqtSignal(str, object)

    def __init__(self):
        super().__init__()
        self._workers = []
        self.setObjectName('LoginPage')
        self.setStyleSheet("""
            QWidget#LoginPage {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F8FAFC, stop:0.5 #EFF6FF, stop:1 #EEF2FF
                );
            }
        """)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addStretch()

        # Centered container
        center_w = QWidget()
        center_w.setStyleSheet('background: transparent;')
        center_w.setFixedWidth(440)
        center_layout = QVBoxLayout(center_w)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(0)

        # ── Logo ──────────────────────────────────
        logo_row = QHBoxLayout()
        logo_row.setSpacing(10)
        logo_row.setAlignment(Qt.AlignCenter)

        mic_box = IconBox('🎙', size=40, bg=C['indigo_600'], fg='white', radius=10, font_size=18)
        brand = make_label('SpeechLab', size=20, weight=QFont.Bold, color=C['slate_900'])
        logo_row.addWidget(mic_box)
        logo_row.addWidget(brand)
        center_layout.addLayout(logo_row)
        center_layout.addSpacing(24)

        # ── Titles ────────────────────────────────
        h1 = make_label('Welcome back', size=28, weight=QFont.Bold,
                        color=C['slate_900'], align=Qt.AlignHCenter)
        sub = make_label('Sign in to continue your practice', size=15,
                         color=C['slate_600'], align=Qt.AlignHCenter)
        center_layout.addWidget(h1)
        center_layout.addSpacing(6)
        center_layout.addWidget(sub)
        center_layout.addSpacing(28)

        # ── Card ──────────────────────────────────
        card = Card(radius=20)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(20)

        # Email
        card_layout.addWidget(make_label('Email', size=14, weight=QFont.Medium,
                                         color=C['slate_700']))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText('jane@company.com')
        self.email_input.setStyleSheet(INPUT_STYLE)
        self.email_input.setFixedHeight(44)
        card_layout.addWidget(self.email_input)

        # Password row header
        pw_header = QHBoxLayout()
        pw_header.addWidget(make_label('Password', size=14, weight=QFont.Medium,
                                       color=C['slate_700']))
        pw_header.addStretch()
        forgot = QLabel('<a href="#" style="color:#4F46E5; text-decoration:none;">Forgot password?</a>')
        forgot.setStyleSheet('background: transparent; border: none;')
        forgot.setOpenExternalLinks(False)
        forgot.setTextFormat(Qt.RichText)
        pw_header.addWidget(forgot)
        card_layout.addLayout(pw_header)

        self.pw_input = QLineEdit()
        self.pw_input.setPlaceholderText('••••••••')
        self.pw_input.setEchoMode(QLineEdit.Password)
        self.pw_input.setStyleSheet(INPUT_STYLE)
        self.pw_input.setFixedHeight(44)
        card_layout.addWidget(self.pw_input)

        # Remember me
        self.remember = QCheckBox('Remember me for 30 days')
        self.remember.setStyleSheet(CHECKBOX_STYLE)
        card_layout.addWidget(self.remember)

        # Submit button
        self.btn_submit = QPushButton('Sign In')
        self.btn_submit.setStyleSheet(BTN_PRIMARY)
        self.btn_submit.setFixedHeight(44)
        self.btn_submit.setCursor(Qt.PointingHandCursor)
        self.btn_submit.clicked.connect(self._on_submit)
        card_layout.addWidget(self.btn_submit)

        center_layout.addWidget(card)
        center_layout.addSpacing(20)

        # ── Footer link ───────────────────────────
        foot = QLabel(
            f'<span style="color:{C["slate_600"]}; font-size:14px;">Don\'t have an account? </span>'
            f'<a href="#" style="color:{C["indigo_600"]}; font-size:14px; font-weight:600; '
            f'text-decoration:none;">Sign up for free</a>'
        )
        foot.setAlignment(Qt.AlignCenter)
        foot.setTextFormat(Qt.RichText)
        foot.setStyleSheet('background: transparent; border: none;')
        foot.linkActivated.connect(lambda: self.navigate.emit('signup', None))
        center_layout.addWidget(foot)

        # Wrap center widget in hbox for horizontal centering
        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(center_w)
        h.addStretch()
        root.addLayout(h)
        root.addStretch()

    def _on_submit(self):
        email = self.email_input.text().strip()
        password = self.pw_input.text()
        if not email or not password:
            show_toast(self, 'Enter email and password', 'error')
            return

        self.btn_submit.setText('Signing in...')
        self.btn_submit.setEnabled(False)

        worker = ApiWorker(lambda: api.login(email, password), self)
        worker.succeeded.connect(self._finish)
        worker.failed.connect(self._fail)
        worker.finished.connect(lambda: self._forget_worker(worker))
        self._workers.append(worker)
        worker.start()

    def _finish(self, _result):
        self.btn_submit.setText('Sign In')
        self.btn_submit.setEnabled(True)
        self.navigate.emit('dashboard', {'refresh': True})

    def _fail(self, message):
        self.btn_submit.setText('Sign In')
        self.btn_submit.setEnabled(True)
        show_toast(self, message, 'error')

    def _forget_worker(self, worker):
        if worker in self._workers:
            self._workers.remove(worker)
