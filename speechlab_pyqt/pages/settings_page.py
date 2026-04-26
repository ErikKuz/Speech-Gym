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
                    INPUT_STYLE, TEXTAREA_STYLE, COMBOBOX_STYLE, apply_scroll_area_theme)
from widgets import Card, AvatarLabel, Separator, Switch, make_label, show_toast


class ConfirmDeleteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Подтверждение удаления')
        self.setFixedWidth(440)
        self.setModal(True)
        self.setStyleSheet(f"background: {C['white']};")

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
        btn_back.clicked.connect(lambda: self.navigate.emit('dashboard', None))

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

        # Timezone
        b_lay.addWidget(make_label('Часовой пояс', size=14, weight=QFont.Medium,
                                   color=C['slate_700']))
        self.tz_combo = QComboBox()
        for tz in ['Восточное время (ET)', 'Центральное время (CT)', 'Горное время (MT)',
                   'Тихоокеанское время (PT)', 'Лондон (GMT)', 'Париж (CET)']:
            self.tz_combo.addItem(tz)
        self.tz_combo.setStyleSheet(COMBOBOX_STYLE)
        b_lay.addWidget(self.tz_combo)

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
        btn_pw = QPushButton('Изменить пароль')
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
        tfa_text.addWidget(make_label('Двухфакторная аутентификация', size=14,
                                      weight=QFont.Medium, color=C['slate_900']))
        tfa_text.addWidget(make_label('Добавьте дополнительный уровень защиты аккаунта',
                                      size=13, color=C['slate_500']))
        btn_tfa = QPushButton('Включить 2FA')
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

        btn_del = QPushButton('Удалить аккаунт')
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

    # ── Actions ──────────────────────────────────────────────────────
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
            show_toast(self, 'Запрос на удаление аккаунта отправлен', 'success')
            QTimer.singleShot(1500, lambda: self.navigate.emit('welcome', None))
