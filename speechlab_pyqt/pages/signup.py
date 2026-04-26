# pages/signup.py — Sign-up page

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QCheckBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from styles import C, BTN_PRIMARY, INPUT_STYLE, CHECKBOX_STYLE
from api_client import ApiWorker, api
from widgets import Card, IconBox, make_label, show_toast


class SignUpPage(QWidget):
    navigate = pyqtSignal(str, object)

    def __init__(self):
        super().__init__()
        self._workers = []
        self.setObjectName('SignUpPage')
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(f"""
            QWidget#SignUpPage {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 {C['bg_grad_0']}, stop:0.5 {C['bg_grad_1']}, stop:1 {C['bg_grad_2']}
                );
            }}
        """)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addStretch()

        center_w = QWidget()
        center_w.setStyleSheet('background: transparent;')
        center_w.setFixedWidth(440)
        cl = QVBoxLayout(center_w)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        # Logo
        logo_row = QHBoxLayout()
        logo_row.setSpacing(10)
        logo_row.setAlignment(Qt.AlignCenter)
        mic_box = IconBox('🎙', size=40, bg=C['indigo_600'], fg='white', radius=10, font_size=18)
        brand = make_label('SpeechLab', size=20, weight=QFont.Bold, color=C['slate_900'])
        logo_row.addWidget(mic_box)
        logo_row.addWidget(brand)
        cl.addLayout(logo_row)
        cl.addSpacing(24)

        h1 = make_label('Create your account', size=28, weight=QFont.Bold,
                        color=C['slate_900'], align=Qt.AlignHCenter)
        sub = make_label('Start improving your presentations today', size=15,
                         color=C['slate_600'], align=Qt.AlignHCenter)
        cl.addWidget(h1)
        cl.addSpacing(6)
        cl.addWidget(sub)
        cl.addSpacing(28)

        # Card
        card = Card(radius=20)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 32)
        card_layout.setSpacing(20)

        # Full Name
        card_layout.addWidget(make_label('Full Name', size=14, weight=QFont.Medium,
                                         color=C['slate_700']))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText('Jane Smith')
        self.name_input.setStyleSheet(INPUT_STYLE)
        self.name_input.setFixedHeight(44)
        card_layout.addWidget(self.name_input)

        # Email
        card_layout.addWidget(make_label('Email', size=14, weight=QFont.Medium,
                                         color=C['slate_700']))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText('jane@company.com')
        self.email_input.setStyleSheet(INPUT_STYLE)
        self.email_input.setFixedHeight(44)
        card_layout.addWidget(self.email_input)

        # Password
        card_layout.addWidget(make_label('Password', size=14, weight=QFont.Medium,
                                         color=C['slate_700']))
        self.pw_input = QLineEdit()
        self.pw_input.setPlaceholderText('••••••••')
        self.pw_input.setEchoMode(QLineEdit.Password)
        self.pw_input.setStyleSheet(INPUT_STYLE)
        self.pw_input.setFixedHeight(44)
        card_layout.addWidget(self.pw_input)

        # Terms checkbox
        self.terms_cb = QCheckBox(
            'I agree to the Terms of Service and Privacy Policy'
        )
        self.terms_cb.setStyleSheet(CHECKBOX_STYLE)
        card_layout.addWidget(self.terms_cb)

        # Submit
        self.btn_submit = QPushButton('Create Account')
        self.btn_submit.setStyleSheet(BTN_PRIMARY)
        self.btn_submit.setFixedHeight(44)
        self.btn_submit.setCursor(Qt.PointingHandCursor)
        self.btn_submit.clicked.connect(self._on_submit)
        card_layout.addWidget(self.btn_submit)

        cl.addWidget(card)
        cl.addSpacing(20)

        # Footer
        foot = QLabel(
            f'<span style="color:{C["slate_600"]}; font-size:14px;">Already have an account? </span>'
            f'<a href="#" style="color:{C["indigo_600"]}; font-size:14px; font-weight:600; '
            f'text-decoration:none;">Sign in</a>'
        )
        foot.setAlignment(Qt.AlignCenter)
        foot.setTextFormat(Qt.RichText)
        foot.setStyleSheet('background: transparent; border: none;')
        foot.linkActivated.connect(lambda: self.navigate.emit('login', None))
        cl.addWidget(foot)

        h = QHBoxLayout()
        h.addStretch()
        h.addWidget(center_w)
        h.addStretch()
        root.addLayout(h)
        root.addStretch()

    def _on_submit(self):
        full_name = self.name_input.text().strip()
        email = self.email_input.text().strip()
        password = self.pw_input.text()
        if not full_name or not email or not password:
            show_toast(self, 'Fill in name, email and password', 'error')
            return
        if len(password) < 8:
            show_toast(self, 'Password must be at least 8 characters', 'error')
            return
        if not self.terms_cb.isChecked():
            show_toast(self, 'Accept the terms to continue', 'error')
            return

        self.btn_submit.setText('Creating account...')
        self.btn_submit.setEnabled(False)

        worker = ApiWorker(lambda: api.register(email, password, full_name), self)
        worker.succeeded.connect(self._finish)
        worker.failed.connect(self._fail)
        worker.finished.connect(lambda: self._forget_worker(worker))
        self._workers.append(worker)
        worker.start()

    def _finish(self, _result):
        self.btn_submit.setText('Create Account')
        self.btn_submit.setEnabled(True)
        self.navigate.emit('dashboard', {'refresh': True})

    def _fail(self, message):
        self.btn_submit.setText('Create Account')
        self.btn_submit.setEnabled(True)
        show_toast(self, message, 'error')

    def _forget_worker(self, worker):
        if worker in self._workers:
            self._workers.remove(worker)
