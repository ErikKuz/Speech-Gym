# widgets.py — Reusable custom widgets for SpeechLab

from PyQt5.QtWidgets import (
    QWidget, QLabel, QFrame, QVBoxLayout, QHBoxLayout,
    QGraphicsDropShadowEffect, QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt, QRect, QTimer, pyqtSignal, QPoint
from PyQt5.QtGui import QPainter, QColor, QBrush, QPen, QFont, QLinearGradient

from styles import C


# ─────────────────────────────────────────────
#  Card
# ─────────────────────────────────────────────
class Card(QFrame):
    """White card with rounded corners, border, and optional drop-shadow."""
    _uid = 0

    def __init__(self, parent=None, radius=16, shadow=True,
                 border_color=None, bg=None):
        super().__init__(parent)
        Card._uid += 1
        name = f'Card{Card._uid}'
        self.setObjectName(name)
        bc = border_color or C['slate_200']
        bg = bg or C['white']
        self.setStyleSheet(f"""
            QFrame#{name} {{
                background-color: {bg};
                border-radius: {radius}px;
                border: 1px solid {bc};
            }}
        """)
        if shadow:
            eff = QGraphicsDropShadowEffect(self)
            eff.setBlurRadius(18)
            eff.setOffset(0, 2)
            eff.setColor(QColor(0, 0, 0, 20))
            self.setGraphicsEffect(eff)


# ─────────────────────────────────────────────
#  Avatar
# ─────────────────────────────────────────────
class AvatarLabel(QWidget):
    """Circular avatar showing initials."""

    def __init__(self, initials='?', size=48,
                 bg=None, fg=None, border=None, parent=None):
        super().__init__(parent)
        self.initials = initials
        bg = bg or C['indigo_100']
        fg = fg or C['indigo_700']
        border = border or C['indigo_200']
        self._bg = QColor(bg)
        self._fg = QColor(fg)
        self._border = QColor(border)
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        m = 2
        r = QRect(m, m, self.width() - 2*m, self.height() - 2*m)
        p.setBrush(QBrush(self._bg))
        p.setPen(QPen(self._border, 2))
        p.drawEllipse(r)
        p.setPen(QPen(self._fg))
        fs = max(self.width() // 4, 8)
        p.setFont(QFont('Segoe UI', fs, QFont.Bold))
        p.drawText(self.rect(), Qt.AlignCenter, self.initials)


# ─────────────────────────────────────────────
#  IconBox
# ─────────────────────────────────────────────
class IconBox(QWidget):
    """Colored rounded square with a centred icon character."""

    def __init__(self, icon_char, size=48, bg=None,
                 fg=None, radius=12, font_size=20, parent=None):
        super().__init__(parent)
        self.icon_char = icon_char
        bg = bg or C['indigo_100']
        fg = fg or C['indigo_600']
        self._bg = QColor(bg)
        self._fg = QColor(fg)
        self._radius = radius
        self._fs = font_size
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QBrush(self._bg))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(self.rect(), self._radius, self._radius)
        p.setPen(QPen(self._fg))
        p.setFont(QFont('Segoe UI Emoji', self._fs))
        p.drawText(self.rect(), Qt.AlignCenter, self.icon_char)


# ─────────────────────────────────────────────
#  Score circles
# ─────────────────────────────────────────────
def _score_colors(score):
    if score >= 85:
        return QColor(C['green_100']), QColor(C['green_600'])
    if score >= 70:
        return QColor(C['blue_100']), QColor(C['blue_600'])
    if score >= 60:
        return QColor(C['amber_100']), QColor(C['amber_600'])
    return QColor(C['red_100']), QColor(C['red_600'])


class ScoreCircle(QWidget):
    """Large circular score badge."""

    def __init__(self, score, size=112, parent=None):
        super().__init__(parent)
        self.score = score
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        bg, fg = _score_colors(self.score)
        m = 4
        r = QRect(m, m, self.width() - 2*m, self.height() - 2*m)
        p.setBrush(QBrush(bg))
        p.setPen(Qt.NoPen)
        p.drawEllipse(r)
        p.setPen(QPen(fg))
        p.setFont(QFont('Segoe UI', max(self.width() // 4, 12), QFont.Bold))
        p.drawText(self.rect(), Qt.AlignCenter, str(self.score))


class SmallScoreCircle(QWidget):
    """Small circular score badge for metric cards."""

    def __init__(self, score, size=56, parent=None):
        super().__init__(parent)
        self.score = score
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        bg, fg = _score_colors(self.score)
        m = 2
        r = QRect(m, m, self.width() - 2*m, self.height() - 2*m)
        p.setBrush(QBrush(bg))
        p.setPen(Qt.NoPen)
        p.drawEllipse(r)
        p.setPen(QPen(fg))
        p.setFont(QFont('Segoe UI', 14, QFont.Bold))
        p.drawText(self.rect(), Qt.AlignCenter, str(self.score))


class NumberCircle(QWidget):
    """Small indigo circle with a number inside."""

    def __init__(self, number, size=24, parent=None):
        super().__init__(parent)
        self.number = str(number)
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QBrush(QColor(C['indigo_600'])))
        p.setPen(Qt.NoPen)
        p.drawEllipse(self.rect())
        p.setPen(QPen(QColor('white')))
        p.setFont(QFont('Segoe UI', 10, QFont.Bold))
        p.drawText(self.rect(), Qt.AlignCenter, self.number)


# ─────────────────────────────────────────────
#  Separator
# ─────────────────────────────────────────────
class Separator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Plain)
        self.setFixedHeight(1)
        self.setStyleSheet(f"background: {C['slate_200']}; color: {C['slate_200']};")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)


# ─────────────────────────────────────────────
#  Switch
# ─────────────────────────────────────────────
class Switch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self.setFixedSize(44, 26)
        self.setCursor(Qt.PointingHandCursor)

    def isChecked(self):
        return self._checked

    def setChecked(self, v):
        self._checked = v
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._checked = not self._checked
            self.toggled.emit(self._checked)
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        # Track
        track = QColor(C['indigo_600']) if self._checked else QColor(C['slate_300'])
        p.setBrush(QBrush(track))
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, 5, 44, 16, 8, 8)
        # Thumb
        tx = 22 if self._checked else 2
        p.setBrush(QBrush(QColor('white')))
        p.setPen(QPen(QColor(C['slate_200']), 1))
        p.drawEllipse(tx, 2, 21, 21)


# ─────────────────────────────────────────────
#  Badge Pill
# ─────────────────────────────────────────────
class BadgePill(QWidget):
    """Rounded pill badge with icon + text."""

    def __init__(self, icon, text,
                 bg=None, border=None, icon_color=None, text_color=None,
                 parent=None):
        super().__init__(parent)
        bg = bg or C['indigo_100']
        border = border or C['indigo_200']
        icon_color = icon_color or C['indigo_600']
        text_color = text_color or C['indigo_900']

        BadgePill._uid = getattr(BadgePill, '_uid', 0) + 1
        name = f'BadgePill{BadgePill._uid}'
        self.setObjectName(name)
        self.setStyleSheet(f"""
            QWidget#{name} {{
                background: {bg};
                border-radius: 16px;
                border: 1px solid {border};
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 6, 14, 6)
        lay.setSpacing(6)

        il = QLabel(icon)
        il.setStyleSheet(f"color: {icon_color}; font-size: 13px; "
                         f"background: transparent; border: none;")
        tl = QLabel(text)
        tl.setStyleSheet(f"color: {text_color}; font-size: 13px; font-weight: 600; "
                         f"background: transparent; border: none;")
        lay.addWidget(il)
        lay.addWidget(tl)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)


# ─────────────────────────────────────────────
#  Label helpers
# ─────────────────────────────────────────────
def make_label(text, size=14, weight=QFont.Normal, color=None,
               wrap=False, align=Qt.AlignLeft):
    color = color or C['slate_900']
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"font-size: {size}px; color: {color}; background: transparent; border: none;"
    )
    if weight != QFont.Normal:
        f = lbl.font()
        f.setWeight(weight)
        lbl.setFont(f)
    if wrap:
        lbl.setWordWrap(True)
    lbl.setAlignment(align | Qt.AlignVCenter)
    return lbl


# ─────────────────────────────────────────────
#  Toast notification
# ─────────────────────────────────────────────
class _Toast(QFrame):
    _uid = 0

    def __init__(self, parent, message, kind):
        super().__init__(parent)
        _Toast._uid += 1
        name = f'Toast{_Toast._uid}'
        self.setObjectName(name)
        bg = C['green_600'] if kind == 'success' else C['red_600']
        self.setStyleSheet(f"""
            QFrame#{name} {{
                background: {bg};
                border-radius: 8px;
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(8)

        icon_txt = '✓' if kind == 'success' else '✕'
        icon = QLabel(icon_txt)
        icon.setStyleSheet("color: white; font-size: 14px; font-weight: bold; "
                           "background: transparent; border: none;")
        msg = QLabel(message)
        msg.setStyleSheet("color: white; font-size: 13px; font-weight: 500; "
                          "background: transparent; border: none;")
        lay.addWidget(icon)
        lay.addWidget(msg)

        self.adjustSize()
        self._reposition()
        self.raise_()
        QTimer.singleShot(3000, self.deleteLater)

    def _reposition(self):
        if self.parent():
            pw = self.parent()
            x = pw.width() - self.width() - 20
            y = 20
            self.move(x, y)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._reposition()


def show_toast(parent_widget, message, kind='success'):
    """Display a temporary toast notification over parent_widget."""
    toast = _Toast(parent_widget, message, kind)
    toast.show()
