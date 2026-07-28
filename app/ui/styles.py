"""全局深色主题 QSS 样式"""

ACCENT = "#4f8cff"
ACCENT_HOVER = "#6da2ff"
BG = "#12141a"
BG_PANEL = "#1a1d26"
BG_CARD = "#222633"
BORDER = "#2e3342"
TEXT = "#e6e9f0"
TEXT_DIM = "#9aa3b5"

DARK_QSS = f"""
* {{
    font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
    font-size: 13px;
}}
QMainWindow, QDialog {{
    background: {BG};
    color: {TEXT};
}}
QWidget {{
    color: {TEXT};
}}
#Sidebar {{
    background: {BG_PANEL};
    border-right: 1px solid {BORDER};
}}
#LogoLabel {{
    font-size: 17px;
    font-weight: bold;
    color: {TEXT};
    padding: 4px 0;
}}
#SubtitleLabel {{
    color: {TEXT_DIM};
    font-size: 11px;
}}
QLabel[cls="sectionTitle"] {{
    color: {TEXT_DIM};
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
    padding-top: 8px;
}}
QComboBox, QLineEdit, QSpinBox, QDoubleSpinBox {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    color: {TEXT};
    selection-background-color: {ACCENT};
}}
QComboBox:hover, QLineEdit:focus {{
    border-color: {ACCENT};
}}
QComboBox::drop-down {{
    border: none; width: 22px;
}}
QComboBox QAbstractItemView {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT};
    color: {TEXT};
}}
QPushButton {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 7px 14px;
    color: {TEXT};
}}
QPushButton:hover {{
    border-color: {ACCENT};
    background: #262b3a;
}}
QPushButton:disabled {{
    color: {TEXT_DIM};
    background: {BG_PANEL};
}}
QPushButton[cls="primary"] {{
    background: {ACCENT};
    border: none;
    color: white;
    font-weight: bold;
}}
QPushButton[cls="primary"]:hover {{
    background: {ACCENT_HOVER};
}}
QPushButton[cls="primary"]:disabled {{
    background: #33517e;
}}
QTextEdit, QPlainTextEdit {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px;
    color: {TEXT};
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollBar:vertical {{
    background: transparent; width: 8px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER}; border-radius: 4px; min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QTabWidget::pane {{
    border: 1px solid {BORDER};
    border-radius: 6px;
    top: -1px;
}}
QTabBar::tab {{
    background: transparent;
    color: {TEXT_DIM};
    padding: 8px 18px;
    border-bottom: 2px solid transparent;
}}
QTabBar::tab:selected {{
    color: {TEXT};
    border-bottom: 2px solid {ACCENT};
}}
QStatusBar {{
    background: {BG_PANEL};
    color: {TEXT_DIM};
    border-top: 1px solid {BORDER};
}}
QFrame[cls="userBubble"] {{
    background: {ACCENT};
    border-radius: 10px;
}}
QFrame[cls="aiBubble"] {{
    background: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 10px;
}}
QFrame[cls="toolCard"] {{
    background: #1d2430;
    border: 1px solid #31405a;
    border-radius: 8px;
}}
QLabel[cls="bubbleText"] {{
    background: transparent;
}}
QLabel[cls="toolTitle"] {{
    color: #7ec8ff;
    font-weight: bold;
    background: transparent;
}}
QLabel[cls="toolBody"] {{
    color: {TEXT_DIM};
    font-family: Consolas, monospace;
    font-size: 12px;
    background: transparent;
}}
QGroupBox {{
    border: 1px solid {BORDER};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 8px;
    color: {TEXT};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    color: {TEXT_DIM};
}}
QCheckBox {{ color: {TEXT}; }}
"""
