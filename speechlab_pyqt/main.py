# main.py — SpeechLab PyQt5 application entry point

import sys
import os
import site
import importlib
from pathlib import Path


os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = 'C:\\Users\\Наталья Борисовна\\Desktop\\SpeechGym\\speechlab_pyqt\\.venv\\Lib\\site-packages\\PyQt5\\Qt5\\plugins\\platforms'


# Ensure the speechlab_pyqt folder is importable when run from any directory
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

BASE_SCREEN_WIDTH = 1920
BASE_SCREEN_HEIGHT = 1080
MAX_UI_SCALE = 1.6


def _windows_screen_size():
    if sys.platform != 'win32':
        return None
    try:
        import ctypes
        from ctypes import wintypes

        ENUM_CURRENT_SETTINGS = -1
        CCHDEVICENAME = 32
        CCHFORMNAME = 32

        class DEVMODE(ctypes.Structure):
            _fields_ = [
                ('dmDeviceName', wintypes.WCHAR * CCHDEVICENAME),
                ('dmSpecVersion', wintypes.WORD),
                ('dmDriverVersion', wintypes.WORD),
                ('dmSize', wintypes.WORD),
                ('dmDriverExtra', wintypes.WORD),
                ('dmFields', wintypes.DWORD),
                ('dmOrientation', wintypes.SHORT),
                ('dmPaperSize', wintypes.SHORT),
                ('dmPaperLength', wintypes.SHORT),
                ('dmPaperWidth', wintypes.SHORT),
                ('dmScale', wintypes.SHORT),
                ('dmCopies', wintypes.SHORT),
                ('dmDefaultSource', wintypes.SHORT),
                ('dmPrintQuality', wintypes.SHORT),
                ('dmColor', wintypes.SHORT),
                ('dmDuplex', wintypes.SHORT),
                ('dmYResolution', wintypes.SHORT),
                ('dmTTOption', wintypes.SHORT),
                ('dmCollate', wintypes.SHORT),
                ('dmFormName', wintypes.WCHAR * CCHFORMNAME),
                ('dmLogPixels', wintypes.WORD),
                ('dmBitsPerPel', wintypes.DWORD),
                ('dmPelsWidth', wintypes.DWORD),
                ('dmPelsHeight', wintypes.DWORD),
                ('dmDisplayFlags', wintypes.DWORD),
                ('dmDisplayFrequency', wintypes.DWORD),
                ('dmICMMethod', wintypes.DWORD),
                ('dmICMIntent', wintypes.DWORD),
                ('dmMediaType', wintypes.DWORD),
                ('dmDitherType', wintypes.DWORD),
                ('dmReserved1', wintypes.DWORD),
                ('dmReserved2', wintypes.DWORD),
                ('dmPanningWidth', wintypes.DWORD),
                ('dmPanningHeight', wintypes.DWORD),
            ]

        devmode = DEVMODE()
        devmode.dmSize = ctypes.sizeof(DEVMODE)
        if ctypes.windll.user32.EnumDisplaySettingsW(None, ENUM_CURRENT_SETTINGS, ctypes.byref(devmode)):
            width = int(devmode.dmPelsWidth)
            height = int(devmode.dmPelsHeight)
            if width > 0 and height > 0:
                return width, height

        user32 = ctypes.windll.user32
        width = int(user32.GetSystemMetrics(0))
        height = int(user32.GetSystemMetrics(1))
        if width > 0 and height > 0:
            return width, height
    except (AttributeError, OSError, ValueError):
        return None
    return None


def _compute_ui_scale(screen_size) -> float:
    if not screen_size:
        return 1.0
    width, height = screen_size
    raw_scale = min(width / BASE_SCREEN_WIDTH, height / BASE_SCREEN_HEIGHT)
    if raw_scale <= 1.05:
        return 1.0
    return round(min(raw_scale, MAX_UI_SCALE), 2)


def _configure_ui_scale():
    os.environ.setdefault('QT_AUTO_SCREEN_SCALE_FACTOR', '1')
    manual_scale = os.environ.get('SPEECHGYM_UI_SCALE')
    if manual_scale:
        try:
            scale = max(1.0, min(float(manual_scale), MAX_UI_SCALE))
        except ValueError:
            scale = 1.0
    else:
        existing_scale = os.environ.get('QT_SCALE_FACTOR')
        if existing_scale:
            try:
                if float(existing_scale) > 1.0:
                    return
            except ValueError:
                pass
        scale = _compute_ui_scale(_windows_screen_size())
    if scale > 1.0:
        os.environ['QT_SCALE_FACTOR'] = f'{scale:.2f}'.rstrip('0').rstrip('.')


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
_configure_ui_scale()

from PyQt5.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont

import styles


class MainWindow(QMainWindow):
    PUBLIC_PAGES = {'welcome', 'signup', 'login'}

    def __init__(self):
        super().__init__()
        self.setWindowTitle('SpeechGym — ИИ для выступлений')
        self.resize(1400, 900)
        self.setMinimumSize(1100, 700)
        self.current_theme = styles.load_theme()
        self._active_theme = 'light'
        self._current_page = 'welcome'
        self._current_data = None

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self._init_pages()

    def _reload_ui_modules(self):
        module_names = [
            'widgets',
            'session_settings',
            'pages.welcome',
            'pages.signup',
            'pages.login',
            'pages.dashboard',
            'pages.rehearsal_chat',
            'pages.settings_page',
        ]
        for module_name in module_names:
            module = sys.modules.get(module_name)
            if module is not None:
                importlib.reload(module)

    def _theme_for_page(self, page_name: str) -> str:
        return 'light' if page_name in self.PUBLIC_PAGES else self.current_theme

    def _set_runtime_theme(self, theme_name: str) -> None:
        self._active_theme = styles.apply_theme(theme_name, persist=False)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(styles.get_global_stylesheet())

    def _init_pages(self, target_page: str = 'welcome', target_data=None):
        self._set_runtime_theme(self._theme_for_page(target_page))
        self._reload_ui_modules()
        from pages.welcome import WelcomePage
        from pages.signup import SignUpPage
        from pages.login import LoginPage
        from pages.dashboard import DashboardPage
        from pages.rehearsal_chat import RehearsalChatPage
        from pages.settings_page import SettingsPage

        while self.stack.count():
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)
            widget.deleteLater()

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

        self.p_settings.load_data({'theme': self.current_theme})

        mapping = {
            'welcome':   self.p_welcome,
            'signup':    self.p_signup,
            'login':     self.p_login,
            'dashboard': self.p_dashboard,
            'rehearsal': self.p_rehearsal,
            'settings':  self.p_settings,
        }
        target = mapping.get(target_page, self.p_welcome)
        if target_data is not None and hasattr(target, 'load_data'):
            target.load_data(target_data)
        self.stack.setCurrentWidget(target)
        self._current_page = target_page if target_page in mapping else 'welcome'
        self._current_data = target_data

    def _apply_theme_and_rebuild(self, theme_name: str, return_page: str = 'settings'):
        self.current_theme = 'dark' if str(theme_name).lower().strip() == 'dark' else 'light'
        styles.apply_theme(self.current_theme, persist=True)
        page_data = {'theme': self.current_theme} if return_page == 'settings' else self._current_data
        self._init_pages(target_page=return_page, target_data=page_data)

    def _navigate(self, page: str, data):
        if page == 'apply_theme':
            payload = data or {}
            desired_theme = payload.get('theme', 'light')
            return_page = payload.get('returnPage', 'settings')
            self._apply_theme_and_rebuild(desired_theme, return_page=return_page)
            return

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

        payload = data
        if page == 'dashboard' and payload is None:
            payload = {'refresh': True}
        if page == 'settings':
            payload = dict(data or {})
            payload.setdefault('theme', self.current_theme)

        if self._theme_for_page(page) != self._active_theme:
            self._init_pages(target_page=page, target_data=payload)
            return

        # Pass data to the target page before switching
        if payload is not None and hasattr(target, 'load_data'):
            target.load_data(payload)

        self.stack.setCurrentWidget(target)
        self._current_page = page
        self._current_data = payload

    # Keep toast widgets inside the window after resize
    def resizeEvent(self, event):
        super().resizeEvent(event)


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Default font
    font = QFont('Segoe UI', 10)
    app.setFont(font)

    styles.apply_theme('light', persist=False)
    app.setStyleSheet(styles.get_global_stylesheet())

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
