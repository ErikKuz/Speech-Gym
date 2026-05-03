# pages/settings_page.py — Settings page

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QFrame, QScrollArea,
    QSizePolicy, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from styles import (C, BTN_PRIMARY, BTN_OUTLINE, BTN_OUTLINE_SM,
                    BTN_DANGER_OUTLINE, BTN_DANGER,
                    INPUT_STYLE, TEXTAREA_STYLE, apply_scroll_area_theme)
from widgets import Card, AvatarLabel, Separator, Switch, make_label, show_toast
from api_client import ApiWorker, api


class ConfirmDeleteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Подтверждение удаления')
        self.setFixedWidth(440)
        self.setModal(True)
        self.setObjectName("ConfirmDeleteDialog")
        self.setStyleSheet(f"QDialog#ConfirmDeleteDialog {{ background: {C['white']}; }}")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 28, 28, 20)
        lay.setSpacing(16)

        lay.addWidget(make_label('Вы уверены?', size=17,
                                 weight=QFont.Bold, color=C['slate_900']))
        lay.addWidget(make_label(
            'Это действие нельзя отменить. Аккаунт будет удален безвозвратно вместе '
            'со всеми данными на сервере, включая записи выступлений и отчеты анализа.',
            size=14, color=C['slate_600'], wrap=True
        ))

        btn_box = QHBoxLayout()
        btn_cancel = QPushButton('Отмена')
        btn_cancel.setStyleSheet(BTN_OUTLINE)
        btn_cancel.setFixedHeight(40)
        btn_cancel.clicked.connect(self.reject)

        btn_delete = QPushButton('Да, удалить мой аккаунт')
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
        self._workers = []
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
        btn_back.clicked.connect(lambda: self.navigate.emit('dashboard', {'refresh': True}))

        div = QFrame()
        div.setFrameShape(QFrame.VLine)
        div.setStyleSheet(f'color: {C["slate_200"]}; background: {C["slate_200"]};')
        div.setFixedWidth(1)

        h_lay.addWidget(btn_back)
        h_lay.addWidget(div)
        h_lay.addWidget(make_label('Настройки', size=14, weight=QFont.DemiBold,
                                   color=C['slate_900']))
        h_lay.addStretch()
        root.addWidget(header)

        # ── Scrollable content ─────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        apply_scroll_area_theme(scroll, C['slate_50'])

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

        lay.addWidget(self._section_header('◉', 'Профиль'))

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
        btn_photo = QPushButton('Изменить фото')
        btn_photo.setStyleSheet(BTN_OUTLINE_SM)
        btn_photo.setFixedHeight(32)
        btn_photo.setFixedWidth(130)
        av_info.addWidget(btn_photo)
        av_info.addWidget(make_label('JPG, PNG или GIF. Максимальный размер 2 МБ.',
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
        name_col.addWidget(make_label('Имя и фамилия', size=14, weight=QFont.Medium,
                                      color=C['slate_700']))
        self.name_input = QLineEdit('Иван Иванов')
        self.name_input.setStyleSheet(INPUT_STYLE)
        self.name_input.setFixedHeight(44)
        name_col.addWidget(self.name_input)

        email_col = QVBoxLayout()
        email_col.setSpacing(8)
        email_col.addWidget(make_label('Электронная почта', size=14, weight=QFont.Medium,
                                       color=C['slate_700']))
        self.email_input = QLineEdit('ivan@example.ru')
        self.email_input.setStyleSheet(INPUT_STYLE)
        self.email_input.setFixedHeight(44)
        email_col.addWidget(self.email_input)

        grid.addLayout(name_col)
        grid.addLayout(email_col)
        b_lay.addLayout(grid)

        # Bio
        b_lay.addWidget(make_label('О себе', size=14, weight=QFont.Medium,
                                   color=C['slate_700']))
        self.bio_input = QTextEdit(
            'Маркетинг-директор, который развивает навыки публичных выступлений'
        )
        self.bio_input.setStyleSheet(TEXTAREA_STYLE)
        self.bio_input.setFixedHeight(88)
        b_lay.addWidget(self.bio_input)

        # Save button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_save_profile = QPushButton('💾  Сохранить изменения')
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
        lay.addWidget(self._section_header('◐', 'Светлая / темная тема'))

        body = QWidget()
        body.setStyleSheet('background: transparent;')
        b_lay = QVBoxLayout(body)
        b_lay.setContentsMargins(32, 24, 32, 28)
        b_lay.setSpacing(16)

        row = QHBoxLayout()
        text_col = QVBoxLayout()
        text_col.setSpacing(4)
        text_col.addWidget(make_label('Темная тема', size=14, weight=QFont.Medium,
                                      color=C['slate_900']))
        text_col.addWidget(make_label(
            'Переключает внешний вид приложения между светлой и темной темой.',
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
        btn_apply = QPushButton('Применить тему')
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
        lay.addWidget(self._section_header('🔔', 'Уведомления'))

        body = QWidget()
        body.setStyleSheet('background: transparent;')
        b_lay = QVBoxLayout(body)
        b_lay.setContentsMargins(32, 24, 32, 28)
        b_lay.setSpacing(0)

        notif_items = [
            ('emailReports', 'Отчеты по электронной почте',
             'Получать отчеты анализа на почту после каждого выступления'),
            ('weeklyDigest', 'Еженедельная сводка',
             'Получать еженедельную сводку прогресса и основных выводов'),
            ('practiceReminders', 'Напоминания о практике',
             'Получать напоминания о регулярной тренировке выступлений'),
            ('productUpdates', 'Обновления продукта',
             'Быть в курсе новых функций и улучшений'),
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
        btn_save_n = QPushButton('💾  Сохранить изменения')
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
        lay.addWidget(self._section_header('🔒', 'Безопасность'))

        body = QWidget()
        body.setStyleSheet('background: transparent;')
        b_lay = QVBoxLayout(body)
        b_lay.setContentsMargins(32, 24, 32, 28)
        b_lay.setSpacing(0)

        # Password row
        pw_row = QHBoxLayout()
        pw_text = QVBoxLayout()
        pw_text.setSpacing(4)
        pw_text.addWidget(make_label('Пароль', size=14, weight=QFont.Medium,
                                     color=C['slate_900']))
        pw_text.addWidget(make_label('Последнее изменение: 3 месяца назад', size=13,
                                     color=C['slate_500']))
        self.btn_toggle_password_form = QPushButton('Изменить пароль')
        self.btn_toggle_password_form.setStyleSheet(BTN_OUTLINE)
        self.btn_toggle_password_form.setFixedHeight(38)
        self.btn_toggle_password_form.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_password_form.clicked.connect(lambda: self._toggle_password_form())
        pw_row.addLayout(pw_text)
        pw_row.addStretch()
        pw_row.addWidget(self.btn_toggle_password_form)
        b_lay.addLayout(pw_row)
        b_lay.addSpacing(18)

        self.password_form = QFrame()
        self.password_form.setObjectName('PasswordForm')
        self.password_form.setStyleSheet(f"""
            QFrame#PasswordForm {{
                background: {C['slate_50']};
                border: 1px solid {C['slate_200']};
                border-radius: 12px;
            }}
        """)
        pf_lay = QVBoxLayout(self.password_form)
        pf_lay.setContentsMargins(18, 16, 18, 18)
        pf_lay.setSpacing(12)

        pf_lay.addWidget(make_label('Смена пароля', size=14, weight=QFont.DemiBold,
                                    color=C['slate_900']))
        pf_lay.addWidget(make_label(
            'Введите текущий пароль, затем новый пароль два раза. Новый пароль должен содержать от 8 до 72 символов.',
            size=13, color=C['slate_600'], wrap=True
        ))

        self.current_password_input = self._password_input(
            pf_lay,
            'Текущий пароль',
            'Введите текущий пароль',
        )
        self.new_password_input = self._password_input(
            pf_lay,
            'Новый пароль',
            'Введите новый пароль',
        )
        self.repeat_password_input = self._password_input(
            pf_lay,
            'Повторите новый пароль',
            'Введите новый пароль еще раз',
        )

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton('Отмена')
        btn_cancel.setStyleSheet(BTN_OUTLINE)
        btn_cancel.setFixedHeight(38)
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(lambda: self._toggle_password_form(False))
        self.btn_save_password = QPushButton('Сохранить пароль')
        self.btn_save_password.setStyleSheet(BTN_PRIMARY)
        self.btn_save_password.setFixedHeight(38)
        self.btn_save_password.setCursor(Qt.PointingHandCursor)
        self.btn_save_password.clicked.connect(self._change_password)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(self.btn_save_password)
        pf_lay.addLayout(btn_row)

        self.password_form.setVisible(False)
        b_lay.addWidget(self.password_form)

        lay.addWidget(body)
        return card

    # ── Billing ──────────────────────────────────────────────────────
    def _build_billing_section(self):
        card = Card(radius=16)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(self._section_header('💳', 'Тариф и оплата'))

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
        plan_text.addWidget(make_label('Текущий тариф', size=14, weight=QFont.Medium,
                                       color=C['slate_900']))
        plan_text.addWidget(make_label('Тариф «Профессиональный» — $29/месяц', size=13,
                                       color=C['slate_600']))
        btn_upgrade = QPushButton('Обновить тариф')
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
        pm_text.addWidget(make_label('Способ оплаты', size=14, weight=QFont.Medium,
                                     color=C['slate_900']))
        pm_text.addWidget(make_label('Visa, последние цифры 4242', size=13, color=C['slate_500']))
        btn_pm = QPushButton('Обновить оплату')
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
        bh_text.addWidget(make_label('История платежей', size=14, weight=QFont.Medium,
                                     color=C['slate_900']))
        bh_text.addWidget(make_label('Просматривайте и скачивайте прошлые счета', size=13,
                                     color=C['slate_500']))
        btn_bh = QPushButton('Открыть счета')
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
        title = make_label('Опасная зона', size=17, weight=QFont.DemiBold,
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
        text_col.addWidget(make_label('Удалить аккаунт', size=14, weight=QFont.Medium,
                                      color=C['slate_900']))
        text_col.addWidget(make_label(
            'Безвозвратно удалить аккаунт и все данные. Это действие нельзя отменить.',
            size=13, color=C['slate_600'], wrap=True
        ))

        self.btn_delete_account = QPushButton('Удалить аккаунт')
        self.btn_delete_account.setStyleSheet(BTN_DANGER_OUTLINE)
        self.btn_delete_account.setFixedHeight(38)
        self.btn_delete_account.setCursor(Qt.PointingHandCursor)
        self.btn_delete_account.clicked.connect(self._on_delete_account)

        b_lay.addLayout(text_col)
        b_lay.addStretch()
        b_lay.addWidget(self.btn_delete_account, 0, Qt.AlignVCenter)
        lay.addWidget(body)
        return card

    # ── Section header helper ────────────────────────────────────────
    def _section_header(self, icon_char, title_text):
        if title_text == 'Профиль':
            title_text = 'Данные пользователя'
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

    def _password_input(self, parent_layout, label_text, placeholder_text):
        parent_layout.addWidget(make_label(label_text, size=13, weight=QFont.Medium,
                                           color=C['slate_700']))
        row = QHBoxLayout()
        row.setSpacing(8)

        field = QLineEdit()
        field.setStyleSheet(INPUT_STYLE)
        field.setFixedHeight(42)
        field.setPlaceholderText(placeholder_text)
        field.setEchoMode(QLineEdit.Password)

        btn_eye = QPushButton('👁')
        btn_eye.setStyleSheet(BTN_OUTLINE_SM)
        btn_eye.setFixedSize(42, 42)
        btn_eye.setCheckable(True)
        btn_eye.setCursor(Qt.PointingHandCursor)
        btn_eye.toggled.connect(
            lambda checked, current_field=field, button=btn_eye:
                self._toggle_password_visibility(current_field, button, checked)
        )

        row.addWidget(field, 1)
        row.addWidget(btn_eye)
        parent_layout.addLayout(row)
        return field

    def _toggle_password_visibility(self, field: QLineEdit, button: QPushButton, visible: bool):
        field.setEchoMode(QLineEdit.Normal if visible else QLineEdit.Password)
        button.setText('🙈' if visible else '👁')

    # ── Actions ──────────────────────────────────────────────────────
    def _toggle_password_form(self, visible=None):
        if visible is None:
            visible = not self.password_form.isVisible()
        self.password_form.setVisible(bool(visible))
        self.btn_toggle_password_form.setText('Скрыть' if visible else 'Изменить пароль')
        if not visible:
            self.current_password_input.clear()
            self.new_password_input.clear()
            self.repeat_password_input.clear()

    def _change_password(self):
        current_password = self.current_password_input.text()
        new_password = self.new_password_input.text()
        repeat_password = self.repeat_password_input.text()

        if not current_password or not new_password or not repeat_password:
            show_toast(self, 'Заполните все поля пароля', 'error')
            return
        if len(new_password) < 8:
            show_toast(self, 'Пароль должен содержать не менее 8 символов', 'error')
            return
        if len(new_password) > 72:
            show_toast(self, 'Пароль должен содержать не более 72 символов', 'error')
            return
        if new_password != repeat_password:
            show_toast(self, 'Новые пароли не совпадают', 'error')
            return
        if new_password == current_password:
            show_toast(self, 'Новый пароль должен отличаться от текущего', 'error')
            return

        self.btn_save_password.setText('Сохранение...')
        self.btn_save_password.setEnabled(False)

        worker = ApiWorker(lambda: api.change_password(current_password, new_password), self)
        worker.succeeded.connect(self._password_changed)
        worker.failed.connect(self._password_change_failed)
        worker.finished.connect(lambda: self._forget_worker(worker))
        self._workers.append(worker)
        worker.start()

    def _password_changed(self, _result):
        self.btn_save_password.setText('Сохранить пароль')
        self.btn_save_password.setEnabled(True)
        self._toggle_password_form(False)
        show_toast(self, 'Пароль успешно изменен', 'success')

    def _password_change_failed(self, message):
        self.btn_save_password.setText('Сохранить пароль')
        self.btn_save_password.setEnabled(True)
        show_toast(self, message, 'error')

    def _save_profile(self):
        self.btn_save_profile.setText('Сохранение...')
        self.btn_save_profile.setEnabled(False)
        QTimer.singleShot(1000, lambda: (
            self.btn_save_profile.setText('💾  Сохранить изменения'),
            self.btn_save_profile.setEnabled(True),
            show_toast(self, 'Данные пользователя успешно обновлены', 'success'),
        ))

    def _save_notifications(self):
        show_toast(self, 'Настройки уведомлений успешно сохранены', 'success')

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
            self.btn_delete_account.setText('Удаление...')
            self.btn_delete_account.setEnabled(False)
            worker = ApiWorker(api.delete_account, self)
            worker.succeeded.connect(self._account_deleted)
            worker.failed.connect(self._delete_account_failed)
            worker.finished.connect(lambda: self._forget_worker(worker))
            self._workers.append(worker)
            worker.start()

    def _account_deleted(self, _result):
        self.btn_delete_account.setText('Удалить аккаунт')
        self.btn_delete_account.setEnabled(True)
        show_toast(self, 'Аккаунт удален', 'success')
        QTimer.singleShot(800, lambda: self.navigate.emit('welcome', None))

    def _delete_account_failed(self, message):
        self.btn_delete_account.setText('Удалить аккаунт')
        self.btn_delete_account.setEnabled(True)
        show_toast(self, message, 'error')

    def _forget_worker(self, worker):
        if worker in self._workers:
            self._workers.remove(worker)
