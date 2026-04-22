# main.py — SpeechLab PyQt5 application entry point

import sys
import os
import site
from pathlib import Path

# Ensure the speechlab_pyqt folder is importable when run from any directory
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))


def _configure_qt_plugins():
    candidates = [
        Path(site.getusersitepackages()) / 'PyQt5' / 'Qt5' / 'plugins' / 'platforms',
        Path(sys.prefix) / 'Lib' / 'site-packages' / 'PyQt5' / 'Qt5' / 'plugins' / 'platforms',
        APP_DIR.parent / '.venv' / 'Lib' / 'site-packages' / 'PyQt5' / 'Qt5' / 'plugins' / 'platforms',
    ]
    for plugin_dir in candidates:
        plugin_path = str(plugin_dir)
        if plugin_path.isascii() and (plugin_dir / 'qwindows.dll').exists():
            qt_bin = plugin_dir.parent.parent / 'bin'
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
            if qt_bin.exists():
                os.environ['PATH'] = str(qt_bin) + os.pathsep + os.environ.get('PATH', '')
                if hasattr(os, 'add_dll_directory'):
                    os.add_dll_directory(str(qt_bin))
            break


_configure_qt_plugins()

from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont

from styles import SCROLLBAR_STYLE


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('SpeechLab — AI Speech Rehearsal')
        self.resize(1400, 900)
        self.setMinimumSize(1100, 700)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self._init_pages()

    def _init_pages(self):
        from pages.welcome import WelcomePage
        from pages.signup import SignUpPage
        from pages.login import LoginPage
        from pages.dashboard import DashboardPage
        from pages.rehearsal_chat import RehearsalChatPage
        from pages.settings_page import SettingsPage

        self.p_welcome  = WelcomePage()
        self.p_signup   = SignUpPage()
        self.p_login    = LoginPage()
        self.p_dashboard = DashboardPage()
        self.p_rehearsal = RehearsalChatPage()
        self.p_settings  = SettingsPage()

        for p in [self.p_welcome, self.p_signup, self.p_login,
                  self.p_dashboard, self.p_rehearsal, self.p_settings]:
            self.stack.addWidget(p)

        # Connect navigation signals from every page
        for p in [self.p_welcome, self.p_signup, self.p_login,
                  self.p_dashboard, self.p_rehearsal, self.p_settings]:
            p.navigate.connect(self._navigate)

        self.stack.setCurrentWidget(self.p_welcome)

    def _navigate(self, page: str, data):
        mapping = {
            'welcome':   self.p_welcome,
            'signup':    self.p_signup,
            'login':     self.p_login,
            'dashboard': self.p_dashboard,
            'rehearsal': self.p_rehearsal,
            'settings':  self.p_settings,
        }
        target = mapping.get(page)
        if target is None:
            return

        # Pass data to the target page before switching
        if data is not None and hasattr(target, 'load_data'):
            target.load_data(data)

        self.stack.setCurrentWidget(target)

    # Keep toast widgets inside the window after resize
    def resizeEvent(self, event):
        super().resizeEvent(event)


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Default font
    font = QFont('Segoe UI', 10)
    app.setFont(font)

    # Global stylesheet: scrollbars for the whole app
    app.setStyleSheet(SCROLLBAR_STYLE + """
        QToolTip {
            background: #1E293B;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 12px;
        }
    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
