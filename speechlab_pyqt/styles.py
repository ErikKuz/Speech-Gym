# styles.py — Color palette and QSS style strings for SpeechLab

C = {
    # Indigo
    'indigo_50':  '#EEF2FF',
    'indigo_100': '#E0E7FF',
    'indigo_200': '#C7D2FE',
    'indigo_300': '#A5B4FC',
    'indigo_400': '#818CF8',
    'indigo_600': '#4F46E5',
    'indigo_700': '#4338CA',
    'indigo_900': '#312E81',
    # Blue
    'blue_50':  '#EFF6FF',
    'blue_100': '#DBEAFE',
    'blue_600': '#2563EB',
    # Violet
    'violet_100': '#EDE9FE',
    'violet_600': '#7C3AED',
    # Slate
    'slate_50':  '#F8FAFC',
    'slate_100': '#F1F5F9',
    'slate_200': '#E2E8F0',
    'slate_300': '#CBD5E1',
    'slate_400': '#94A3B8',
    'slate_500': '#64748B',
    'slate_600': '#475569',
    'slate_700': '#334155',
    'slate_800': '#1E293B',
    'slate_900': '#0F172A',
    # Green
    'green_50':  '#F0FDF4',
    'green_100': '#DCFCE7',
    'green_200': '#BBF7D0',
    'green_600': '#16A34A',
    # Amber
    'amber_50':  '#FFFBEB',
    'amber_100': '#FEF3C7',
    'amber_200': '#FDE68A',
    'amber_600': '#D97706',
    # Red
    'red_50':  '#FEF2F2',
    'red_100': '#FEE2E2',
    'red_200': '#FECACA',
    'red_600': '#DC2626',
    'red_700': '#B91C1C',
    'red_900': '#7F1D1D',
    # Misc
    'white': '#FFFFFF',
    # Gradient stops for auth/welcome pages
    'bg_grad_0': '#F8FAFC',
    'bg_grad_1': '#EFF6FF',
    'bg_grad_2': '#EEF2FF',
}

BTN_PRIMARY = """
    QPushButton {
        background-color: #4F46E5;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 14px;
        font-weight: 600;
    }
    QPushButton:hover { background-color: #4338CA; }
    QPushButton:pressed { background-color: #3730A3; }
    QPushButton:disabled { background-color: #A5B4FC; color: white; }
"""

BTN_PRIMARY_LG = """
    QPushButton {
        background-color: #4F46E5;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 28px;
        font-size: 15px;
        font-weight: 600;
    }
    QPushButton:hover { background-color: #4338CA; }
    QPushButton:pressed { background-color: #3730A3; }
    QPushButton:disabled { background-color: #A5B4FC; }
"""

BTN_OUTLINE = """
    QPushButton {
        background-color: transparent;
        color: #334155;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 14px;
        font-weight: 500;
    }
    QPushButton:hover { background-color: #F8FAFC; border-color: #94A3B8; }
    QPushButton:pressed { background-color: #F1F5F9; }
"""

BTN_OUTLINE_LG = """
    QPushButton {
        background-color: transparent;
        color: #334155;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        padding: 12px 28px;
        font-size: 15px;
        font-weight: 500;
    }
    QPushButton:hover { background-color: #F8FAFC; border-color: #94A3B8; }
"""

BTN_OUTLINE_SM = """
    QPushButton {
        background-color: transparent;
        color: #334155;
        border: 1px solid #CBD5E1;
        border-radius: 6px;
        padding: 5px 12px;
        font-size: 13px;
        font-weight: 500;
    }
    QPushButton:hover { background-color: #F8FAFC; }
"""

BTN_GHOST = """
    QPushButton {
        background-color: transparent;
        color: #475569;
        border: none;
        border-radius: 8px;
        padding: 8px 14px;
        font-size: 14px;
        font-weight: 500;
        text-align: left;
    }
    QPushButton:hover { background-color: #F1F5F9; color: #0F172A; }
"""

BTN_GHOST_SM = """
    QPushButton {
        background-color: transparent;
        color: #475569;
        border: none;
        border-radius: 6px;
        padding: 5px 10px;
        font-size: 13px;
        font-weight: 500;
        text-align: left;
    }
    QPushButton:hover { background-color: #F1F5F9; color: #0F172A; }
"""

BTN_DANGER_OUTLINE = """
    QPushButton {
        background-color: transparent;
        color: #B91C1C;
        border: 1px solid #FECACA;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: 500;
    }
    QPushButton:hover { background-color: #FEF2F2; }
"""

BTN_DANGER = """
    QPushButton {
        background-color: #DC2626;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: 600;
    }
    QPushButton:hover { background-color: #B91C1C; }
"""

BTN_WHITE_TRANSPARENT = """
    QPushButton {
        background-color: rgba(255,255,255,0.2);
        color: white;
        border: 1px solid rgba(255,255,255,0.35);
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 14px;
        font-weight: 500;
    }
    QPushButton:hover { background-color: rgba(255,255,255,0.3); }
"""

INPUT_STYLE = """
    QLineEdit {
        background-color: white;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 0 12px;
        font-size: 14px;
        color: #0F172A;
        selection-background-color: #E0E7FF;
        min-height: 44px;
    }
    QLineEdit:focus {
        border: 2px solid #4F46E5;
        padding: 0 11px;
    }
    QLineEdit:disabled { background: #F1F5F9; color: #94A3B8; }
"""

TEXTAREA_STYLE = """
    QTextEdit {
        background-color: white;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 14px;
        color: #0F172A;
        selection-background-color: #E0E7FF;
    }
    QTextEdit:focus {
        border: 2px solid #4F46E5;
        padding: 7px 11px;
    }
"""

COMBOBOX_STYLE = """
    QComboBox {
        background-color: white;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 0 12px;
        font-size: 14px;
        color: #0F172A;
        min-height: 44px;
    }
    QComboBox:focus { border: 2px solid #4F46E5; padding: 0 11px; }
    QComboBox::drop-down { border: none; width: 32px; }
    QComboBox::down-arrow {
        width: 0; height: 0;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid #64748B;
        margin-right: 10px;
    }
    QComboBox QAbstractItemView {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        selection-background-color: #EEF2FF;
        selection-color: #312E81;
        font-size: 14px;
        outline: none;
    }
    QComboBox QAbstractItemView::item {
        padding: 8px 12px;
        min-height: 32px;
    }
"""

PROGRESS_STYLE = """
    QProgressBar {
        background-color: #F1F5F9;
        border-radius: 4px;
        border: none;
        font-size: 0px;
    }
    QProgressBar::chunk {
        background-color: #4F46E5;
        border-radius: 4px;
    }
"""

CHECKBOX_STYLE = """
    QCheckBox {
        font-size: 14px;
        color: #475569;
        spacing: 8px;
        background: transparent;
    }
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
        border: 1px solid #CBD5E1;
        border-radius: 4px;
        background: white;
    }
    QCheckBox::indicator:checked {
        background-color: #4F46E5;
        border-color: #4F46E5;
    }
    QCheckBox::indicator:hover { border-color: #4F46E5; }
"""

SCROLLBAR_STYLE = """
    QScrollBar:vertical {
        border: none;
        background: transparent;
        width: 8px;
        margin: 0;
    }
    QScrollBar::handle:vertical {
        background: #CBD5E1;
        border-radius: 4px;
        min-height: 20px;
    }
    QScrollBar::handle:vertical:hover { background: #94A3B8; }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
    QScrollBar:horizontal {
        border: none;
        background: transparent;
        height: 8px;
    }
    QScrollBar::handle:horizontal {
        background: #CBD5E1;
        border-radius: 4px;
        min-width: 20px;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
"""


# Runtime theming -------------------------------------------------------------
import json
from pathlib import Path

THEME_FILE = Path(__file__).resolve().parent / ".speechlab_theme.json"
CURRENT_THEME = "light"

LIGHT_THEME = dict(C)
LIGHT_THEME.update({
    "bg_grad_0": "#F8FAFC",
    "bg_grad_1": "#EFF6FF",
    "bg_grad_2": "#EEF2FF",
})

DARK_THEME = {
    # Indigo
    "indigo_50": "#1E1B4B",
    "indigo_100": "#312E81",
    "indigo_200": "#4338CA",
    "indigo_300": "#6366F1",
    "indigo_400": "#818CF8",
    "indigo_600": "#6366F1",
    "indigo_700": "#818CF8",
    "indigo_900": "#E0E7FF",
    # Blue
    "blue_50": "#0B253A",
    "blue_100": "#103B59",
    "blue_600": "#60A5FA",
    # Violet
    "violet_100": "#312E81",
    "violet_600": "#A78BFA",
    # Slate
    "slate_50": "#0B1220",
    "slate_100": "#0F172A",
    "slate_200": "#1E293B",
    "slate_300": "#334155",
    "slate_400": "#475569",
    "slate_500": "#94A3B8",
    "slate_600": "#CBD5E1",
    "slate_700": "#E2E8F0",
    "slate_800": "#F1F5F9",
    "slate_900": "#F8FAFC",
    # Green
    "green_50": "#052E16",
    "green_100": "#14532D",
    "green_200": "#166534",
    "green_600": "#4ADE80",
    # Amber
    "amber_50": "#451A03",
    "amber_100": "#78350F",
    "amber_200": "#92400E",
    "amber_600": "#F59E0B",
    # Red
    "red_50": "#450A0A",
    "red_100": "#7F1D1D",
    "red_200": "#991B1B",
    "red_600": "#F87171",
    "red_700": "#EF4444",
    "red_900": "#FECACA",
    # Misc
    "white": "#111827",
    # Gradients
    "bg_grad_0": "#0B1220",
    "bg_grad_1": "#0F172A",
    "bg_grad_2": "#111827",
}


def _write_theme(theme_name: str) -> None:
    try:
        THEME_FILE.write_text(json.dumps({"theme": theme_name}), encoding="utf-8")
    except OSError:
        pass


def load_theme() -> str:
    try:
        payload = json.loads(THEME_FILE.read_text(encoding="utf-8"))
        theme = str(payload.get("theme", "light")).lower().strip()
        return "dark" if theme == "dark" else "light"
    except (OSError, ValueError, TypeError):
        return "light"


def refresh_styles() -> None:
    global BTN_PRIMARY, BTN_PRIMARY_LG, BTN_OUTLINE, BTN_OUTLINE_LG
    global BTN_OUTLINE_SM, BTN_GHOST, BTN_GHOST_SM, BTN_DANGER_OUTLINE
    global BTN_DANGER, BTN_WHITE_TRANSPARENT, INPUT_STYLE, TEXTAREA_STYLE
    global COMBOBOX_STYLE, PROGRESS_STYLE, CHECKBOX_STYLE, SCROLLBAR_STYLE

    BTN_PRIMARY = f"""
        QPushButton {{
            background-color: {C['indigo_600']};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 600;
        }}
        QPushButton:hover {{ background-color: {C['indigo_700']}; }}
        QPushButton:pressed {{ background-color: {C['indigo_900']}; }}
        QPushButton:disabled {{ background-color: {C['indigo_300']}; color: white; }}
    """

    BTN_PRIMARY_LG = f"""
        QPushButton {{
            background-color: {C['indigo_600']};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 12px 28px;
            font-size: 15px;
            font-weight: 600;
        }}
        QPushButton:hover {{ background-color: {C['indigo_700']}; }}
        QPushButton:pressed {{ background-color: {C['indigo_900']}; }}
        QPushButton:disabled {{ background-color: {C['indigo_300']}; }}
    """

    BTN_OUTLINE = f"""
        QPushButton {{
            background-color: transparent;
            color: {C['slate_700']};
            border: 1px solid {C['slate_300']};
            border-radius: 8px;
            padding: 10px 20px;
            font-size: 14px;
            font-weight: 500;
        }}
        QPushButton:hover {{ background-color: {C['slate_100']}; border-color: {C['slate_400']}; }}
        QPushButton:pressed {{ background-color: {C['slate_200']}; }}
    """

    BTN_OUTLINE_LG = f"""
        QPushButton {{
            background-color: transparent;
            color: {C['slate_700']};
            border: 1px solid {C['slate_300']};
            border-radius: 8px;
            padding: 12px 28px;
            font-size: 15px;
            font-weight: 500;
        }}
        QPushButton:hover {{ background-color: {C['slate_100']}; border-color: {C['slate_400']}; }}
    """

    BTN_OUTLINE_SM = f"""
        QPushButton {{
            background-color: transparent;
            color: {C['slate_700']};
            border: 1px solid {C['slate_300']};
            border-radius: 6px;
            padding: 5px 12px;
            font-size: 13px;
            font-weight: 500;
        }}
        QPushButton:hover {{ background-color: {C['slate_100']}; }}
    """

    BTN_GHOST = f"""
        QPushButton {{
            background-color: transparent;
            color: {C['slate_600']};
            border: none;
            border-radius: 8px;
            padding: 8px 14px;
            font-size: 14px;
            font-weight: 500;
            text-align: left;
        }}
        QPushButton:hover {{ background-color: {C['slate_100']}; color: {C['slate_900']}; }}
    """

    BTN_GHOST_SM = f"""
        QPushButton {{
            background-color: transparent;
            color: {C['slate_600']};
            border: none;
            border-radius: 6px;
            padding: 5px 10px;
            font-size: 13px;
            font-weight: 500;
            text-align: left;
        }}
        QPushButton:hover {{ background-color: {C['slate_100']}; color: {C['slate_900']}; }}
    """

    BTN_DANGER_OUTLINE = f"""
        QPushButton {{
            background-color: transparent;
            color: {C['red_700']};
            border: 1px solid {C['red_200']};
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 500;
        }}
        QPushButton:hover {{ background-color: {C['red_50']}; }}
    """

    BTN_DANGER = f"""
        QPushButton {{
            background-color: {C['red_600']};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 600;
        }}
        QPushButton:hover {{ background-color: {C['red_700']}; }}
    """

    BTN_WHITE_TRANSPARENT = """
        QPushButton {
            background-color: rgba(255,255,255,0.2);
            color: white;
            border: 1px solid rgba(255,255,255,0.35);
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 500;
        }
        QPushButton:hover { background-color: rgba(255,255,255,0.3); }
    """

    INPUT_STYLE = f"""
        QLineEdit {{
            background-color: {C['white']};
            border: 1px solid {C['slate_200']};
            border-radius: 8px;
            padding: 0 12px;
            font-size: 14px;
            color: {C['slate_900']};
            selection-background-color: {C['indigo_100']};
            min-height: 44px;
        }}
        QLineEdit:focus {{
            border: 2px solid {C['indigo_600']};
            padding: 0 11px;
        }}
        QLineEdit:disabled {{ background: {C['slate_100']}; color: {C['slate_500']}; }}
    """

    TEXTAREA_STYLE = f"""
        QTextEdit {{
            background-color: {C['white']};
            border: 1px solid {C['slate_200']};
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 14px;
            color: {C['slate_900']};
            selection-background-color: {C['indigo_100']};
        }}
        QTextEdit:focus {{
            border: 2px solid {C['indigo_600']};
            padding: 7px 11px;
        }}
    """

    COMBOBOX_STYLE = f"""
        QComboBox {{
            background-color: {C['white']};
            border: 1px solid {C['slate_200']};
            border-radius: 8px;
            padding: 0 12px;
            font-size: 14px;
            color: {C['slate_900']};
            min-height: 44px;
        }}
        QComboBox:focus {{ border: 2px solid {C['indigo_600']}; padding: 0 11px; }}
        QComboBox::drop-down {{ border: none; width: 32px; }}
        QComboBox::down-arrow {{
            width: 0; height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {C['slate_500']};
            margin-right: 10px;
        }}
        QComboBox QAbstractItemView {{
            background: {C['white']};
            border: 1px solid {C['slate_200']};
            border-radius: 8px;
            selection-background-color: {C['indigo_100']};
            selection-color: {C['indigo_900']};
            font-size: 14px;
            outline: none;
        }}
        QComboBox QAbstractItemView::item {{
            padding: 8px 12px;
            min-height: 32px;
        }}
    """

    PROGRESS_STYLE = f"""
        QProgressBar {{
            background-color: {C['slate_100']};
            border-radius: 4px;
            border: none;
            font-size: 0px;
        }}
        QProgressBar::chunk {{
            background-color: {C['indigo_600']};
            border-radius: 4px;
        }}
    """

    CHECKBOX_STYLE = f"""
        QCheckBox {{
            font-size: 14px;
            color: {C['slate_600']};
            spacing: 8px;
            background: transparent;
        }}
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid {C['slate_300']};
            border-radius: 4px;
            background: {C['white']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {C['indigo_600']};
            border-color: {C['indigo_600']};
        }}
        QCheckBox::indicator:hover {{ border-color: {C['indigo_600']}; }}
    """

    SCROLLBAR_STYLE = f"""
        QScrollBar:vertical {{
            border: none;
            background: transparent;
            width: 8px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {C['slate_300']};
            border-radius: 4px;
            min-height: 20px;
        }}
        QScrollBar::handle:vertical:hover {{ background: {C['slate_400']}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}
        QScrollBar:horizontal {{
            border: none;
            background: transparent;
            height: 8px;
        }}
        QScrollBar::handle:horizontal {{
            background: {C['slate_300']};
            border-radius: 4px;
            min-width: 20px;
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
    """


def apply_theme(theme_name: str, persist: bool = True) -> str:
    global CURRENT_THEME
    normalized = "dark" if str(theme_name).lower().strip() == "dark" else "light"
    palette = DARK_THEME if normalized == "dark" else LIGHT_THEME
    C.clear()
    C.update(palette)
    CURRENT_THEME = normalized
    refresh_styles()
    if persist:
        _write_theme(normalized)
    return CURRENT_THEME


def get_global_stylesheet() -> str:
    return SCROLLBAR_STYLE + f"""
        QToolTip {{
            background: {C['slate_800']};
            color: {C['white'] if CURRENT_THEME == 'light' else C['slate_900']};
            border: none;
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 12px;
        }}
    """


refresh_styles()
