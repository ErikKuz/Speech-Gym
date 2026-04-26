# pages/settings_page.py — Settings page

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QFrame, QScrollArea,
    QSizePolicy, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from styles import (C, BTN_PRIMARY, BTN_OUTLINE, BTN_OUTLINE_SM,
                    BTN_DANGER_OUTLINE, BTN_DANGER,
                    INPUT_STYLE, TEXTAREA_STYLE, COMBOBOX_STYLE, SCROLLBAR_STYLE)
from widgets import Card, AvatarLabel, Separator, Switch, make_label, show_toast


class ConfirmDeleteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Confirm Deletion')
        self.setFixedWidth(440)
        self.setModal(True)
        self.setStyleSheet(f"background: {C['white']};")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 28, 28, 20)
        lay.setSpacing(16)

        lay.addWidget(make_label('Are you absolutely sure?', size=17,
                                 weight=QFont.Bold, color=C['slate_900']))
        lay.addWidget(make_label(
            'This action cannot be undone. This will permanently delete your account and '
            'remove all your data from our servers, including all rehearsal recordings '
            'and analysis reports.',
            size=14, color=C['slate_600'], wrap=True
        ))

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton('Cancel')
        btn_cancel.setStyleSheet(BTN_OUTLINE)
        btn_cancel.setFixedHeight(40)
        btn_cancel.clicked.connect(self.reject)

        btn_delete = QPushButton('Yes, delete my account')
        btn_delete.setStyleSheet(BTN_DANGER)
        btn_delete.setFixedHeight(40)
        btn_delete.clicked.connect(self.accept)

        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_delete)
        lay.addLayout(btn_box)


class SettingsPage(QWidget):
    navigate = pyqtSignal(str, object)

    def __init__(self):
        super().__init__()
        self.setObjectName('SettingsPage')
        self.setStyleSheet(f'QWidget#SettingsPage {{ background: {C["slate_50"]}; }}')
        self._notif = {
            'emailReports': True,
            'weeklyDigest': True,
            'practiceReminders': False,
            'productUpdates': True,
        }
        self._theme_dark = False
        self._saving = False
        self._build()

    def load_data(self, data: dict):
        if not isinstance(data, dict):
            return
        theme_name = str(data.get('theme', '')).strip().lower()
        if theme_name in ('light', 'dark'):
            self._theme_dark = theme_name == 'dark'
            if hasattr(self, 'theme_switch'):
                self.theme_switch.blockSignals(True)
                self.theme_switch.setChecked(self._theme_dark)
                self.theme_switch.blockSignals(False)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top header ─────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(58)
        header.setStyleSheet(
            f'background: {C["white"]}; border-bottom: 1px solid {C["slate_200"]};'
        )
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(24, 0, 24, 0)
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
        btn_back.clicked.connect(lambda: self.navigate.emit('dashboard', {'refresh': True}))

        div = QFrame()
        div.setFrameShape(QFrame.VLine)
        div.setStyleSheet(f'color: {C["slate_200"]}; background: {C["slate_200"]};')
        div.setFixedWidth(1)

        h_lay.addWidget(btn_back)
        h_lay.addWidget(div)
        h_lay.addWidget(make_label('Settings', size=14, weight=QFont.DemiBold,
                                   color=C['slate_900']))
        h_lay.addStretch()
        root.addWidget(header)

        # ── Scrollable content ─────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(SCROLLBAR_STYLE)

        content = QWidget()
        content.setStyleSheet(f'background: {C["slate_50"]};')
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        inner = QWidget()
        inner.setStyleSheet('background: transparent;')
        inner.setMaximumWidth(860)
        il = QVBoxLayout(inner)
        il.setContentsMargins(40, 32, 40, 48)
        il.setSpacing(28)

        il.addWidget(self._build_profile_section())
        il.addWidget(self._build_theme_section())
        il.addWidget(self._build_security_section())
        il.addWidget(self._build_danger_section())

        h_wrap = QHBoxLayout()
        h_wrap.addStretch()
        h_wrap.addWidget(inner, 2)
        h_wrap.addStretch()
        cl.addLayout(h_wrap)
        cl.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll, 1)

    # ── Profile ─────────────────────────────────────────────────────
    def _build_profile_section(self):
        card = Card(radius=16)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        lay.addWidget(self._section_header('◉', 'Profile'))

        body = QWidget()
        body.setStyleSheet('background: transparent;')
        b_lay = QVBoxLayout(body)
        b_lay.setContentsMargins(32, 24, 32, 28)
        b_lay.setSpacing(20)

        # Avatar row
        av_row = QHBoxLayout()
        av_row.setSpacing(20)
        avatar = AvatarLabel('JS', size=80,
                             bg=C['indigo_100'], fg=C['indigo_700'],
                             border=C['indigo_200'])
        av_info = QVBoxLayout()
        av_info.setSpacing(6)
        btn_photo = QPushButton('Change Photo')
        btn_photo.setStyleSheet(BTN_OUTLINE_SM)
        btn_photo.setFixedHeight(32)
        btn_photo.setFixedWidth(130)
        av_info.addWidget(btn_photo)
        av_info.addWidget(make_label('JPG, PNG or GIF. Max size 2 MB.',
                                     size=12, color=C['slate_500']))
        av_row.addWidget(avatar)
        av_row.addLayout(av_info)
        av_row.addStretch()
        b_lay.addLayout(av_row)
        b_lay.addWidget(Separator())

        # 2-col: Name / Email
        grid = QHBoxLayout()
        grid.setSpacing(20)
        name_col = QVBoxLayout()
        name_col.setSpacing(8)
        name_col.addWidget(make_label('Full Name', size=14, weight=QFont.Medium,
                                      color=C['slate_700']))
        self.name_input = QLineEdit('Jane Smith')
        self.name_input.setStyleSheet(INPUT_STYLE)
        self.name_input.setFixedHeight(44)
        name_col.addWidget(self.name_input)

        email_col = QVBoxLayout()
        email_col.setSpacing(8)
        email_col.addWidget(make_label('Email', size=14, weight=QFont.Medium,
                                       color=C['slate_700']))
        self.email_input = QLineEdit('jane@company.com')
        self.email_input.setStyleSheet(INPUT_STYLE)
        self.email_input.setFixedHeight(44)
        email_col.addWidget(self.email_input)

        grid.addLayout(name_col)
        grid.addLayout(email_col)
        b_lay.addLayout(grid)

        # Bio
        b_lay.addWidget(make_label('Bio', size=14, weight=QFont.Medium,
                                   color=C['slate_700']))
        self.bio_input = QTextEdit(
            'Marketing Director focused on improving presentation skills'
        )
        self.bio_input.setStyleSheet(TEXTAREA_STYLE)
        self.bio_input.setFixedHeight(88)
        b_lay.addWidget(self.bio_input)

        # Timezone
        b_lay.addWidget(make_label('Timezone', size=14, weight=QFont.Medium,
                                   color=C['slate_700']))
        self.tz_combo = QComboBox()
        for tz in ['Eastern Time (ET)', 'Central Time (CT)', 'Mountain Time (MT)',
                   'Pacific Time (PT)', 'London (GMT)', 'Paris (CET)']:
            self.tz_combo.addItem(tz)
        self.tz_combo.setStyleSheet(COMBOBOX_STYLE)
        b_lay.addWidget(self.tz_combo)

        # Save button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_save_profile = QPushButton('💾  Save Changes')
        self.btn_save_profile.setStyleSheet(BTN_PRIMARY)
        self.btn_save_profile.setFixedHeight(40)
        self.btn_save_profile.setCursor(Qt.PointingHandCursor)
        self.btn_save_profile.clicked.connect(self._save_profile)
        btn_row.addWidget(self.btn_save_profile)
        b_lay.addLayout(btn_row)

        lay.addWidget(body)
        return card

    # Theme
    def _build_theme_section(self):
        card = Card(radius=16)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._section_header('◐', 'Light/Dark Theme'))

        body = QWidget()
        body.setStyleSheet('background: transparent;')
        b_lay = QVBoxLayout(body)
        b_lay.setContentsMargins(32, 24, 32, 28)
        b_lay.setSpacing(16)

        row = QHBoxLayout()
        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        text_col.addWidget(make_label('Dark Theme', size=14, weight=QFont.Medium,
                                      color=C['slate_900']))
        text_col.addWidget(make_label(
            'Switches the app appearance between light and dark modes.',
            size=13, color=C['slate_500'], wrap=True
        ))
        self.theme_switch = Switch(checked=self._theme_dark)
        self.theme_switch.toggled.connect(self._on_theme_toggled)
        row.addLayout(text_col)
        row.addStretch()
        row.addWidget(self.theme_switch, 0, Qt.AlignVCenter)
        b_lay.addLayout(row)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_apply = QPushButton('Apply Theme')
        btn_apply.setStyleSheet(BTN_PRIMARY)
        btn_apply.setFixedHeight(40)
        btn_apply.setCursor(Qt.PointingHandCursor)
        btn_apply.clicked.connect(self._apply_theme)
        btn_row.addWidget(btn_apply)
        b_lay.addLayout(btn_row)

        lay.addWidget(body)
        return card

    # ── Notifications ───────────────────────────────────────────────
    def _build_notifications_section(self):
        card = Card(radius=16)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._section_header('🔔', 'Notifications'))

        body = QWidget()
        body.setStyleSheet('background: transparent;')
        b_lay = QVBoxLayout(body)
        b_lay.setContentsMargins(32, 24, 32, 28)
        b_lay.setSpacing(0)

        notif_items = [
            ('emailReports', 'Email Reports',
             'Receive your analysis reports via email after each rehearsal'),
            ('weeklyDigest', 'Weekly Digest',
             'Get a summary of your progress and insights every week'),
            ('practiceReminders', 'Practice Reminders',
             'Receive reminders to practice your presentations regularly'),
            ('productUpdates', 'Product Updates',
             'Stay informed about new features and improvements'),
        ]

        self._switches = {}
        for i, (key, title, desc) in enumerate(notif_items):
            if i > 0:
                b_lay.addWidget(Separator())
                b_lay.addSpacing(16)
            row = QHBoxLayout()
            text_col = QVBoxLayout()
            text_col.setSpacing(4)
            text_col.addWidget(make_label(title, size=14, weight=QFont.Medium,
                                          color=C['slate_900']))
            text_col.addWidget(make_label(desc, size=13, color=C['slate_500'], wrap=True))
            sw = Switch(checked=self._notif[key])
            self._switches[key] = sw
            sw.toggled.connect(lambda v, k=key: self._notif.update({k: v}))
            row.addLayout(text_col)
            row.addStretch()
            row.addWidget(sw, 0, Qt.AlignVCenter)
            b_lay.addLayout(row)
            b_lay.addSpacing(16)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_save_n = QPushButton('💾  Save Changes')
        btn_save_n.setStyleSheet(BTN_PRIMARY)
        btn_save_n.setFixedHeight(40)
        btn_save_n.setCursor(Qt.PointingHandCursor)
        btn_save_n.clicked.connect(self._save_notifications)
        btn_row.addWidget(btn_save_n)
        b_lay.addLayout(btn_row)

        lay.addWidget(body)
        return card

    # ── Security ─────────────────────────────────────────────────────
    def _build_security_section(self):
        card = Card(radius=16)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._section_header('🔒', 'Security'))

        body = QWidget()
        body.setStyleSheet('background: transparent;')
        b_lay = QVBoxLayout(body)
        b_lay.setContentsMargins(32, 24, 32, 28)
        b_lay.setSpacing(0)

        # Password row
        pw_row = QHBoxLayout()
        pw_text = QVBoxLayout()
        pw_text.setSpacing(4)
        pw_text.addWidget(make_label('Password', size=14, weight=QFont.Medium,
                                     color=C['slate_900']))
        pw_text.addWidget(make_label('Last changed 3 months ago', size=13,
                                     color=C['slate_500']))
        btn_pw = QPushButton('Change Password')
        btn_pw.setStyleSheet(BTN_OUTLINE)
        btn_pw.setFixedHeight(38)
        pw_row.addLayout(pw_text)
        pw_row.addStretch()
        pw_row.addWidget(btn_pw)
        b_lay.addLayout(pw_row)
        b_lay.addSpacing(16)
        b_lay.addWidget(Separator())
        b_lay.addSpacing(16)

        # 2FA row
        tfa_row = QHBoxLayout()
        tfa_text = QVBoxLayout()
        tfa_text.setSpacing(4)
        tfa_text.addWidget(make_label('Two-Factor Authentication', size=14,
                                      weight=QFont.Medium, color=C['slate_900']))
        tfa_text.addWidget(make_label('Add an extra layer of security to your account',
                                      size=13, color=C['slate_500']))
        btn_tfa = QPushButton('Enable 2FA')
        btn_tfa.setStyleSheet(BTN_OUTLINE)
        btn_tfa.setFixedHeight(38)
        tfa_row.addLayout(tfa_text)
        tfa_row.addStretch()
        tfa_row.addWidget(btn_tfa)
        b_lay.addLayout(tfa_row)

        lay.addWidget(body)
        return card

    # ── Billing ──────────────────────────────────────────────────────
    def _build_billing_section(self):
        card = Card(radius=16)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._section_header('💳', 'Billing & Plan'))

        body = QWidget()
        body.setStyleSheet('background: transparent;')
        b_lay = QVBoxLayout(body)
        b_lay.setContentsMargins(32, 24, 32, 28)
        b_lay.setSpacing(0)

        # Current plan box
        plan_box = QFrame()
        plan_box.setObjectName('PlanBox')
        plan_box.setStyleSheet(f"""
            QFrame#PlanBox {{
                background: {C['indigo_50']};
                border: 1px solid {C['indigo_200']};
                border-radius: 12px;
            }}
        """)
        pb_lay = QHBoxLayout(plan_box)
        pb_lay.setContentsMargins(16, 14, 16, 14)
        plan_text = QVBoxLayout()
        plan_text.setSpacing(4)
        plan_text.addWidget(make_label('Current Plan', size=14, weight=QFont.Medium,
                                       color=C['slate_900']))
        plan_text.addWidget(make_label('Professional Plan — $29/month', size=13,
                                       color=C['slate_600']))
        btn_upgrade = QPushButton('Upgrade Plan')
        btn_upgrade.setStyleSheet(BTN_OUTLINE_SM)
        btn_upgrade.setFixedHeight(34)
        pb_lay.addLayout(plan_text)
        pb_lay.addStretch()
        pb_lay.addWidget(btn_upgrade)
        b_lay.addWidget(plan_box)
        b_lay.addSpacing(16)
        b_lay.addWidget(Separator())
        b_lay.addSpacing(16)

        # Payment method
        pm_row = QHBoxLayout()
        pm_text = QVBoxLayout()
        pm_text.setSpacing(4)
        pm_text.addWidget(make_label('Payment Method', size=14, weight=QFont.Medium,
                                     color=C['slate_900']))
        pm_text.addWidget(make_label('Visa ending in 4242', size=13, color=C['slate_500']))
        btn_pm = QPushButton('Update Payment')
        btn_pm.setStyleSheet(BTN_OUTLINE)
        btn_pm.setFixedHeight(38)
        pm_row.addLayout(pm_text)
        pm_row.addStretch()
        pm_row.addWidget(btn_pm)
        b_lay.addLayout(pm_row)
        b_lay.addSpacing(16)
        b_lay.addWidget(Separator())
        b_lay.addSpacing(16)

        # Billing history
        bh_row = QHBoxLayout()
        bh_text = QVBoxLayout()
        bh_text.setSpacing(4)
        bh_text.addWidget(make_label('Billing History', size=14, weight=QFont.Medium,
                                     color=C['slate_900']))
        bh_text.addWidget(make_label('View and download past invoices', size=13,
                                     color=C['slate_500']))
        btn_bh = QPushButton('View Invoices')
        btn_bh.setStyleSheet(BTN_OUTLINE)
        btn_bh.setFixedHeight(38)
        bh_row.addLayout(bh_text)
        bh_row.addStretch()
        bh_row.addWidget(btn_bh)
        b_lay.addLayout(bh_row)

        lay.addWidget(body)
        return card

    # ── Danger zone ──────────────────────────────────────────────────
    def _build_danger_section(self):
        card = QFrame()
        card.setObjectName('DangerCard')
        card.setStyleSheet(f"""
            QFrame#DangerCard {{
                background: {C['white']};
                border: 1px solid {C['red_200']};
                border-radius: 16px;
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Section header (red tint)
        sec_header = QWidget()
        sec_header.setObjectName('DangerHeader')
        sec_header.setStyleSheet(f"""
            QWidget#DangerHeader {{
                background: {C['red_50']};
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
                border-bottom: 1px solid {C['red_200']};
            }}
        """)
        sh_lay = QHBoxLayout(sec_header)
        sh_lay.setContentsMargins(28, 18, 28, 18)
        sh_lay.setSpacing(10)
        icon = QLabel('🗑')
        icon.setStyleSheet('font-size: 16px; background: transparent; border: none;')
        title = make_label('Danger Zone', size=17, weight=QFont.DemiBold,
                           color=C['red_900'])
        sh_lay.addWidget(icon)
        sh_lay.addWidget(title)
        sh_lay.addStretch()
        lay.addWidget(sec_header)

        body = QWidget()
        body.setStyleSheet('background: transparent;')
        b_lay = QHBoxLayout(body)
        b_lay.setContentsMargins(28, 22, 28, 22)

        text_col = QVBoxLayout()
        text_col.setSpacing(6)
        text_col.addWidget(make_label('Delete Account', size=14, weight=QFont.Medium,
                                      color=C['slate_900']))
        text_col.addWidget(make_label(
            'Permanently delete your account and all your data. This action cannot be undone.',
            size=13, color=C['slate_600'], wrap=True
        ))

        btn_del = QPushButton('Delete Account')
        btn_del.setStyleSheet(BTN_DANGER_OUTLINE)
        btn_del.setFixedHeight(38)
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.clicked.connect(self._on_delete_account)

        b_lay.addLayout(text_col)
        b_lay.addStretch()
        b_lay.addWidget(btn_del, 0, Qt.AlignVCenter)
        lay.addWidget(body)
        return card

    # ── Section header helper ────────────────────────────────────────
    def _section_header(self, icon_char, title_text):
        if title_text == 'Profile':
            title_text = 'User Data'
        header = QWidget()
        header.setObjectName('SectionHeader')
        header.setStyleSheet(f"""
            QWidget#SectionHeader {{
                background: {C['white']};
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
                border-bottom: 1px solid {C['slate_200']};
            }}
        """)
        lay = QHBoxLayout(header)
        lay.setContentsMargins(28, 18, 28, 18)
        lay.setSpacing(10)
        icon = QLabel(icon_char)
        icon.setStyleSheet(f'font-size: 16px; color: {C["indigo_600"]}; '
                           f'background: transparent; border: none;')
        title = make_label(title_text, size=17, weight=QFont.DemiBold,
                           color=C['slate_900'])
        lay.addWidget(icon)
        lay.addWidget(title)
        lay.addStretch()
        return header

    # ── Actions ──────────────────────────────────────────────────────
    def _save_profile(self):
        self.btn_save_profile.setText('Saving...')
        self.btn_save_profile.setEnabled(False)
        QTimer.singleShot(1000, lambda: (
            self.btn_save_profile.setText('💾  Save Changes'),
            self.btn_save_profile.setEnabled(True),
            show_toast(self, 'User data updated successfully', 'success'),
        ))

    def _save_notifications(self):
        show_toast(self, 'Notification settings saved successfully', 'success')

    def _on_theme_toggled(self, value: bool):
        self._theme_dark = bool(value)

    def _apply_theme(self):
        target_theme = 'dark' if self._theme_dark else 'light'
        self.navigate.emit('apply_theme', {
            'theme': target_theme,
            'returnPage': 'settings',
        })

    def _on_delete_account(self):
        dialog = ConfirmDeleteDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            show_toast(self, 'Account deletion request submitted', 'success')
            QTimer.singleShot(1500, lambda: self.navigate.emit('welcome', None))
