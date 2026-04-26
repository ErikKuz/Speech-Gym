# pages/dashboard.py — Dashboard page

from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QFrame, QScrollArea,
    QSizePolicy, QGridLayout
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from styles import (C, BTN_PRIMARY, BTN_OUTLINE_SM, BTN_GHOST, BTN_GHOST_SM,
                    INPUT_STYLE, TEXTAREA_STYLE, COMBOBOX_STYLE, SCROLLBAR_STYLE)
from api_client import ApiWorker, api
from session_settings import (
    AUDIENCE_OPTIONS,
    DEFAULT_AUDIENCE,
    DEFAULT_STYLE,
    LANGUAGE_OPTIONS,
    STYLE_OPTIONS,
    build_session_payload_from_form,
)
from widgets import Card, AvatarLabel, BadgePill, Separator, make_label, show_toast

MOCK_REHEARSALS = [
    {'id': '1', 'title': 'Q4 Sales Presentation',   'date': 'March 12, 2026', 'duration': '12:34', 'score': 87, 'scenario': 'Executive board meeting'},
    {'id': '2', 'title': 'Product Launch Keynote',   'date': 'March 10, 2026', 'duration': '18:22', 'score': 92, 'scenario': 'Conference keynote'},
    {'id': '3', 'title': 'Team Standup Practice',    'date': 'March 8, 2026',  'duration': '5:12',  'score': 78, 'scenario': 'Team meeting'},
    {'id': '4', 'title': 'Investor Pitch Deck',      'date': 'March 5, 2026',  'duration': '15:45', 'score': 85, 'scenario': 'Investor meeting'},
    {'id': '5', 'title': 'Conference Workshop',      'date': 'March 1, 2026',  'duration': '28:15', 'score': 90, 'scenario': 'Workshop facilitation'},
]


class RehearsalItem(QFrame):
    """Clickable rehearsal list item for the sidebar."""
    clicked = pyqtSignal(dict)

    def __init__(self, rehearsal: dict, parent=None):
        super().__init__(parent)
        self._data = rehearsal
        self._normal_style = f"""
            QFrame {{
                background: {C['white']};
                border: 1px solid {C['slate_200']};
                border-radius: 12px;
            }}
        """
        self._hover_style = f"""
            QFrame {{
                background: {C['indigo_50']};
                border: 1px solid {C['indigo_200']};
                border-radius: 12px;
            }}
        """
        self.setStyleSheet(self._normal_style)
        self.setCursor(Qt.PointingHandCursor)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)
        title_text = rehearsal.get('title') or 'Untitled rehearsal'
        date_text = rehearsal.get('date') or 'No date'
        duration_text = rehearsal.get('duration') or '-'
        score = rehearsal.get('score')
        scenario_text = rehearsal.get('scenario') or rehearsal.get('goal') or 'Practice session'

        # Row 1: title + score badge
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        title = QLabel(title_text)
        title.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {C['slate_900']}; "
                            f"background: transparent; border: none;")
        title.setWordWrap(False)

        score_badge = QLabel(f"Score {score}" if score is not None else "New")
        score_badge.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {C['indigo_700']}; "
            f"background: {C['indigo_100']}; border-radius: 10px; "
            f"padding: 2px 7px; border: none;"
        )
        top_row.addWidget(title, 1)
        top_row.addWidget(score_badge, 0)
        lay.addLayout(top_row)

        # Row 2: date + duration
        meta_row = QHBoxLayout()
        meta_row.setSpacing(12)
        date_lbl = QLabel(f"Date: {date_text}")
        date_lbl.setStyleSheet(f"font-size: 11px; color: {C['slate_500']}; "
                               f"background: transparent; border: none;")
        dur_lbl = QLabel(f"Duration: {duration_text}")
        dur_lbl.setStyleSheet(f"font-size: 11px; color: {C['slate_500']}; "
                              f"background: transparent; border: none;")
        meta_row.addWidget(date_lbl)
        meta_row.addWidget(dur_lbl)
        meta_row.addStretch()
        lay.addLayout(meta_row)

        # Row 3: scenario
        sc = QLabel(scenario_text)
        sc.setStyleSheet(f"font-size: 11px; color: {C['slate_600']}; "
                         f"background: transparent; border: none;")
        lay.addWidget(sc)

    def enterEvent(self, e):
        self.setStyleSheet(self._hover_style)

    def leaveEvent(self, e):
        self.setStyleSheet(self._normal_style)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit(self._data)


class DashboardPage(QWidget):
    navigate = pyqtSignal(str, object)

    def __init__(self):
        super().__init__()
        self._workers = []
        self.setObjectName('DashboardPage')
        self.setStyleSheet(f"QWidget#DashboardPage {{ background: {C['slate_50']}; }}")
        self._build()

    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── SIDEBAR ────────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(300)
        sidebar.setStyleSheet(
            f"QFrame {{ background: {C['white']}; border-right: 1px solid {C['slate_200']}; }}"
        )
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        # User profile section
        profile_section = QWidget()
        profile_section.setStyleSheet(
            f"background: {C['white']}; border-bottom: 1px solid {C['slate_200']};"
        )
        ps_lay = QVBoxLayout(profile_section)
        ps_lay.setContentsMargins(20, 20, 20, 16)
        ps_lay.setSpacing(0)

        user_row = QHBoxLayout()
        user_row.setSpacing(12)
        self.avatar = AvatarLabel('JS', size=48)
        user_info = QVBoxLayout()
        user_info.setSpacing(2)
        self.name_lbl = make_label('Jane Smith', size=14, weight=QFont.DemiBold,
                                   color=C['slate_900'])
        self.email_lbl = make_label('jane@company.com', size=13, color=C['slate_500'])
        user_info.addWidget(self.name_lbl)
        user_info.addWidget(self.email_lbl)
        user_row.addWidget(self.avatar)
        user_row.addLayout(user_info)
        user_row.addStretch()
        ps_lay.addLayout(user_row)
        ps_lay.addSpacing(14)

        btn_settings = QPushButton('⚙  Settings')
        btn_settings.setStyleSheet(BTN_OUTLINE_SM)
        btn_settings.setFixedHeight(34)
        btn_settings.setCursor(Qt.PointingHandCursor)
        btn_settings.clicked.connect(lambda: self.navigate.emit('settings', None))
        ps_lay.addWidget(btn_settings)

        sb_layout.addWidget(profile_section)

        # Rehearsals heading
        rh_heading = QWidget()
        rh_heading.setStyleSheet(
            f"background: {C['white']}; border-bottom: 1px solid {C['slate_200']};"
        )
        rh_h_lay = QHBoxLayout(rh_heading)
        rh_h_lay.setContentsMargins(20, 14, 20, 14)
        rh_h_lay.addWidget(
            make_label('Recent Rehearsals', size=14, weight=QFont.DemiBold,
                       color=C['slate_900'])
        )
        sb_layout.addWidget(rh_heading)

        # Scrollable rehearsal list
        list_scroll = QScrollArea()
        list_scroll.setWidgetResizable(True)
        list_scroll.setFrameShape(QFrame.NoFrame)
        list_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        list_scroll.setStyleSheet(SCROLLBAR_STYLE + f" QScrollArea {{ background: {C['slate_50']}; }}")

        list_container = QWidget()
        list_container.setStyleSheet(f"background: {C['slate_50']};")
        lc_lay = QVBoxLayout(list_container)
        lc_lay.setContentsMargins(12, 12, 12, 12)
        lc_lay.setSpacing(8)
        self.lc_lay = lc_lay

        for r in MOCK_REHEARSALS:
            item = RehearsalItem(r)
            item.clicked.connect(self._open_rehearsal)
            lc_lay.addWidget(item)
        lc_lay.addStretch()

        list_scroll.setWidget(list_container)
        sb_layout.addWidget(list_scroll, 1)

        # Sign out button
        signout_section = QWidget()
        signout_section.setStyleSheet(
            f"background: {C['white']}; border-top: 1px solid {C['slate_200']};"
        )
        so_lay = QHBoxLayout(signout_section)
        so_lay.setContentsMargins(12, 10, 12, 10)

        btn_signout = QPushButton('⬅  Sign Out')
        btn_signout.setStyleSheet(BTN_GHOST)
        btn_signout.setFixedHeight(36)
        btn_signout.setCursor(Qt.PointingHandCursor)
        btn_signout.clicked.connect(self._sign_out)
        so_lay.addWidget(btn_signout)
        sb_layout.addWidget(signout_section)

        root.addWidget(sidebar)

        # ── MAIN CONTENT ───────────────────────────────────────────
        content_scroll = QScrollArea()
        content_scroll.setWidgetResizable(True)
        content_scroll.setFrameShape(QFrame.NoFrame)
        content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content_scroll.setStyleSheet(SCROLLBAR_STYLE)

        content_w = QWidget()
        content_w.setStyleSheet(f"background: {C['slate_50']};")
        cw_lay = QVBoxLayout(content_w)
        cw_lay.setContentsMargins(60, 48, 60, 48)
        cw_lay.setSpacing(0)

        # Header
        badge = BadgePill('＋', 'New Rehearsal',
                          bg=C['indigo_100'], border=C['indigo_200'],
                          icon_color=C['indigo_600'], text_color=C['indigo_900'])
        cw_lay.addWidget(badge, 0, Qt.AlignLeft)
        cw_lay.addSpacing(16)

        cw_lay.addWidget(
            make_label('Configure Your Practice Session', size=32,
                       weight=QFont.Bold, color=C['slate_900'])
        )
        cw_lay.addSpacing(8)
        cw_lay.addWidget(
            make_label('Set up your rehearsal details to receive personalized feedback and insights.',
                       size=16, color=C['slate_600'], wrap=True)
        )
        cw_lay.addSpacing(28)

        # Form card
        form_card = Card(radius=16)
        fc_lay = QVBoxLayout(form_card)
        fc_lay.setContentsMargins(32, 32, 32, 32)
        fc_lay.setSpacing(20)

        # Rehearsal Title
        fc_lay.addWidget(make_label('Rehearsal Title *', size=14, weight=QFont.Medium,
                                    color=C['slate_700']))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText('e.g., Q4 Sales Presentation')
        self.title_input.setStyleSheet(INPUT_STYLE)
        self.title_input.setFixedHeight(44)
        fc_lay.addWidget(self.title_input)

        # Goal / Scenario
        fc_lay.addWidget(make_label('Goal / Scenario', size=14, weight=QFont.Medium,
                                    color=C['slate_700']))
        self.goal_input = QLineEdit()
        self.goal_input.setPlaceholderText('e.g., Executive board meeting, Conference keynote')
        self.goal_input.setStyleSheet(INPUT_STYLE)
        self.goal_input.setFixedHeight(44)
        fc_lay.addWidget(self.goal_input)

        # Language + Duration (2-col grid)
        grid1 = QHBoxLayout()
        grid1.setSpacing(16)

        lang_col = QVBoxLayout()
        lang_col.setSpacing(8)
        lang_col.addWidget(make_label('Language', size=14, weight=QFont.Medium,
                                      color=C['slate_700']))
        self.lang_combo = QComboBox()
        for label, code in LANGUAGE_OPTIONS:
            self.lang_combo.addItem(label, code)
        self.lang_combo.setStyleSheet(COMBOBOX_STYLE)
        lang_col.addWidget(self.lang_combo)

        dur_col = QVBoxLayout()
        dur_col.setSpacing(8)
        dur_col.addWidget(make_label('Target Duration', size=14, weight=QFont.Medium,
                                     color=C['slate_700']))
        self.dur_input = QLineEdit()
        self.dur_input.setPlaceholderText('e.g., 15 minutes')
        self.dur_input.setStyleSheet(INPUT_STYLE)
        self.dur_input.setFixedHeight(44)
        dur_col.addWidget(self.dur_input)

        grid1.addLayout(lang_col)
        grid1.addLayout(dur_col)
        fc_lay.addLayout(grid1)

        # Audience + Style (2-col grid)
        grid2 = QHBoxLayout()
        grid2.setSpacing(16)

        aud_col = QVBoxLayout()
        aud_col.setSpacing(8)
        aud_col.addWidget(make_label('Audience Type', size=14, weight=QFont.Medium,
                                     color=C['slate_700']))
        self.aud_combo = QComboBox()
        self.aud_combo.addItem('Select audience', '')
        for item in AUDIENCE_OPTIONS:
            self.aud_combo.addItem(item)
        self.aud_combo.setStyleSheet(COMBOBOX_STYLE)
        aud_col.addWidget(self.aud_combo)

        style_col = QVBoxLayout()
        style_col.setSpacing(8)
        style_col.addWidget(make_label('Speaking Style / Tone', size=14, weight=QFont.Medium,
                                       color=C['slate_700']))
        self.style_combo = QComboBox()
        self.style_combo.addItem('Select style', '')
        for item in STYLE_OPTIONS:
            self.style_combo.addItem(item)
        self.style_combo.setStyleSheet(COMBOBOX_STYLE)
        style_col.addWidget(self.style_combo)

        grid2.addLayout(aud_col)
        grid2.addLayout(style_col)
        fc_lay.addLayout(grid2)

        # Notes
        fc_lay.addWidget(make_label('Additional Notes (Optional)', size=14,
                                    weight=QFont.Medium, color=C['slate_700']))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText(
            "Any specific areas you'd like feedback on, concerns, or context..."
        )
        self.notes_input.setStyleSheet(TEXTAREA_STYLE)
        self.notes_input.setFixedHeight(110)
        fc_lay.addWidget(self.notes_input)

        cw_lay.addWidget(form_card)
        cw_lay.addSpacing(20)

        # Bottom row: required hint + submit button
        bottom_row = QHBoxLayout()
        bottom_row.addWidget(
            make_label('* Required fields', size=13, color=C['slate_500'])
        )
        bottom_row.addStretch()

        self.btn_create = QPushButton('✦  Create Rehearsal')
        self.btn_create.setStyleSheet(BTN_PRIMARY)
        self.btn_create.setFixedHeight(46)
        self.btn_create.setMinimumWidth(180)
        self.btn_create.setCursor(Qt.PointingHandCursor)
        self.btn_create.clicked.connect(self._on_create)
        bottom_row.addWidget(self.btn_create)
        cw_lay.addLayout(bottom_row)
        cw_lay.addStretch()

        content_scroll.setWidget(content_w)
        root.addWidget(content_scroll, 1)

    # ── Actions ────────────────────────────────────────────────────
    def load_data(self, _data: dict):
        if api.has_auth():
            self._load_dashboard()

    def _on_create(self):
        title = self.title_input.text().strip()
        if not title:
            show_toast(self, 'Please enter a rehearsal title', 'error')
            return
        if not api.has_auth():
            show_toast(self, 'Sign in before creating a rehearsal', 'error')
            return

        self.btn_create.setText('Creating...')
        self.btn_create.setEnabled(False)
        worker = ApiWorker(lambda: api.create_session(self._session_payload(title)), self)
        worker.succeeded.connect(self._session_created)
        worker.failed.connect(self._create_failed)
        worker.finished.connect(lambda: self._forget_worker(worker))
        self._workers.append(worker)
        worker.start()

    def _open_rehearsal(self, rehearsal: dict):
        if rehearsal.get('is_backend_session'):
            self.navigate.emit('rehearsal', {
                'sessionId': rehearsal.get('sessionId'),
                'title': rehearsal.get('title'),
                'goal': rehearsal.get('goal') or rehearsal.get('scenario'),
                'is_new': False,
            })
            return
        self.navigate.emit('rehearsal', {'rehearsal': rehearsal, 'is_new': False})

    def _session_created(self, session: dict):
        self.btn_create.setText('Create Rehearsal')
        self.btn_create.setEnabled(True)
        self.title_input.clear()
        self.goal_input.clear()
        self.dur_input.clear()
        self.notes_input.clear()
        session_id = str(session.get('sessionId', ''))
        self.navigate.emit('rehearsal', {
            'sessionId': session_id,
            'title': session.get('title', 'New Rehearsal'),
            'goal': session.get('goal') or session.get('scenario') or '',
            'session': session,
            'is_new': True,
        })

    def _create_failed(self, message: str):
        self.btn_create.setText('Create Rehearsal')
        self.btn_create.setEnabled(True)
        show_toast(self, message, 'error')

    def _load_dashboard(self):
        worker = ApiWorker(lambda: {
            'me': api.me(),
            'sessions': api.list_sessions().get('items', []),
        }, self)
        worker.succeeded.connect(self._dashboard_loaded)
        worker.failed.connect(lambda message: show_toast(self, message, 'error'))
        worker.finished.connect(lambda: self._forget_worker(worker))
        self._workers.append(worker)
        worker.start()

    def _dashboard_loaded(self, result: dict):
        user = result.get('me') or api.user or {}
        full_name = user.get('fullName') or 'Signed in user'
        email = user.get('email') or ''
        self.name_lbl.setText(full_name)
        self.email_lbl.setText(email)
        self.avatar.initials = self._initials(full_name, email)
        self.avatar.update()
        self._render_sessions(result.get('sessions') or [])

    def _render_sessions(self, sessions: list):
        while self.lc_lay.count():
            item = self.lc_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not sessions:
            empty = make_label('No rehearsals yet', size=13, color=C['slate_500'],
                               align=Qt.AlignHCenter)
            self.lc_lay.addWidget(empty)
            self.lc_lay.addStretch()
            return

        for session in sessions:
            item_data = {
                'id': str(session.get('sessionId', '')),
                'sessionId': str(session.get('sessionId', '')),
                'title': session.get('title') or 'Untitled rehearsal',
                'goal': session.get('goal') or '',
                'scenario': session.get('goal') or 'Practice session',
                'date': self._format_date(session.get('updatedAt')),
                'duration': '-',
                'score': None,
                'is_backend_session': True,
            }
            item = RehearsalItem(item_data)
            item.clicked.connect(self._open_rehearsal)
            self.lc_lay.addWidget(item)
        self.lc_lay.addStretch()

    def _session_payload(self, title: str) -> dict:
        goal = self.goal_input.text().strip()
        audience = self.aud_combo.currentText()
        style = self.style_combo.currentText()
        if self.aud_combo.currentData() == '':
            audience = DEFAULT_AUDIENCE
        if self.style_combo.currentData() == '':
            style = DEFAULT_STYLE

        return build_session_payload_from_form(
            title=title,
            goal=goal,
            language_label=self.lang_combo.currentText(),
            audience_type=audience,
            duration_text=self.dur_input.text(),
            presentation_style=style,
            notes=self.notes_input.toPlainText(),
        )

    def _sign_out(self):
        api.clear_auth()
        self.navigate.emit('welcome', None)

    def _forget_worker(self, worker):
        if worker in self._workers:
            self._workers.remove(worker)

    @staticmethod
    def _format_date(value: str) -> str:
        if not value:
            return 'No date'
        try:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
            return parsed.strftime('%B %d, %Y')
        except ValueError:
            return value

    @staticmethod
    def _initials(full_name: str, email: str) -> str:
        parts = [p for p in (full_name or '').split() if p]
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        if parts:
            return parts[0][:2].upper()
        return (email[:2] or '?').upper()
