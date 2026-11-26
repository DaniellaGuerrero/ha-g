from __future__ import annotations

NAVY = "#10294D"
NAVY_HOVER = "#1A3A68"
BLUE = "#2563EB"
BLUE_HOVER = "#1D4FD0"
INDIGO = "#3659D9"
TEAL = "#0F7A94"
SKY = "#38B6E8"
LIGHT_BLUE = "#C3DAFE"
BG = "#F8FAFC"
TEXT = "#1E2A4A"
HEADING = "#2B3A67"
MUTED = "#6B7A99"
BORDER = "#D5DCE8"
SEG_BG = "#E3E4F0"

MONO = '"Cascadia Mono", "Consolas", "Menlo", "DejaVu Sans Mono", monospace'
SERIF = '"Instrument Serif", "Georgia", "Times New Roman", serif'


def build_stylesheet(assets: dict[str, str]) -> str:
    check, chevron, chevron_up = assets["check"], assets["chevron"], assets["chevron_up"]
    return f"""
QWidget {{ color: {TEXT}; }}
QMainWindow, QDialog {{ background: {BG}; }}
QLabel {{ background: transparent; }}
QScrollArea {{ border: none; background: transparent; }}
QFrame#pageRoot, QWidget#scrollBody {{ background: {BG}; }}
QToolTip {{ background: {NAVY}; color: #fff; border: none; padding: 6px 8px; }}

QLineEdit, QPlainTextEdit, QSpinBox, QComboBox, QDateTimeEdit {{
    background: #fff; border: 1px solid {BORDER}; border-radius: 10px;
    padding: 12px 14px; selection-background-color: {BLUE}; selection-color: #fff;
}}
QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus, QDateTimeEdit:focus {{
    border: 1px solid {BLUE};
}}
QLineEdit#joinLeft {{ border-top-right-radius: 0; border-bottom-right-radius: 0; }}
QComboBox#joinCombo {{ border-top-right-radius: 0; border-bottom-right-radius: 0; padding-right: 8px; min-width: 70px; }}
QLineEdit#joinRightInput {{ border-top-left-radius: 0; border-bottom-left-radius: 0; border-left: none; }}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox::down-arrow {{ image: url({chevron}); width: 14px; height: 14px; }}
QComboBox QAbstractItemView {{
    background: #fff; border: 1px solid {BORDER}; selection-background-color: #EAF1FF;
    selection-color: {TEXT}; outline: none; padding: 4px;
}}
QPlainTextEdit#messageEdit {{ padding: 14px; }}
QSpinBox {{ padding: 8px 30px 8px 12px; min-height: 22px; color: {TEXT}; background: #fff; }}
QSpinBox::up-button {{ subcontrol-origin: border; subcontrol-position: top right; width: 24px; border: none; background: transparent; margin: 3px 3px 0 0; }}
QSpinBox::down-button {{ subcontrol-origin: border; subcontrol-position: bottom right; width: 24px; border: none; background: transparent; margin: 0 3px 3px 0; }}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: #EAF1FF; border-radius: 6px; }}
QSpinBox::up-arrow {{ image: url({chevron_up}); width: 12px; height: 12px; }}
QSpinBox::down-arrow {{ image: url({chevron}); width: 12px; height: 12px; }}

QPushButton {{ border-radius: 10px; padding: 12px 18px; font-weight: 600; }}
QPushButton:disabled {{ background: #A9B4CA; color: #EEF2F8; border-color: #A9B4CA; }}
QPushButton#primary {{ background: {NAVY}; color: #fff; border: none; }}
QPushButton#primary:hover {{ background: {NAVY_HOVER}; }}
QPushButton#blue {{ background: {BLUE}; color: #fff; border: none; }}
QPushButton#blue:hover {{ background: {BLUE_HOVER}; }}
QPushButton#tonal {{ background: #EAF1FF; color: {BLUE}; border: 1px solid #BFD3FA; }}
QPushButton#tonal:hover {{ background: #DCE8FF; }}
QPushButton#outline {{ background: #fff; color: {TEXT}; border: 1px solid {BORDER}; }}
QPushButton#outline:hover {{ background: #F2F5FA; }}
QPushButton#copy {{ background: #fff; color: {MUTED}; border: 1px solid {BORDER}; padding: 10px 16px; font-size: 12px; }}
QPushButton#copy:hover {{ background: #F2F5FA; }}
QPushButton#joinRight {{
    background: {NAVY}; color: #fff; border: none; padding: 15px 24px;
    border-top-left-radius: 0; border-bottom-left-radius: 0;
}}
QPushButton#joinRight:hover {{ background: {NAVY_HOVER}; }}
QPushButton#link, QPushButton#linkBold {{
    background: transparent; border: none; padding: 4px 0; color: {MUTED}; font-weight: 600; text-align: left;
}}
QPushButton#linkBold {{ color: {NAVY}; font-weight: 700; }}
QPushButton#linkBlue {{ background: transparent; border: none; padding: 4px 0; color: {BLUE}; font-weight: 700; font-size: 12px; }}
QPushButton#link:hover, QPushButton#linkBold:hover, QPushButton#linkBlue:hover {{ color: {BLUE}; }}
QPushButton#iconSend {{ background: {BLUE}; border: none; border-radius: 10px; padding: 0; }}
QPushButton#iconSend:hover {{ background: {BLUE_HOVER}; }}
QToolButton#logout {{ background: transparent; border: none; border-radius: 8px; padding: 8px; }}
QToolButton#logout:hover {{ background: #EEF2F8; }}

QCheckBox {{ spacing: 8px; color: {MUTED}; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid #8795B0; border-radius: 4px; background: #fff; }}
QCheckBox::indicator:checked {{ background: {BLUE}; border: 1px solid {BLUE}; image: url({check}); }}

QFrame#topbar {{ background: #fff; border-bottom: 1px solid {BORDER}; }}
QFrame#segment {{ background: {SEG_BG}; border-radius: 11px; }}
QToolButton#navBtn {{
    background: transparent; border: none; border-radius: 8px; padding: 6px 12px;
    color: {MUTED}; font-weight: 600; font-size: 11px;
}}
QToolButton#navBtn:checked {{ background: #fff; color: {NAVY}; font-weight: 700; }}
QLabel#brand {{ color: {HEADING}; font-weight: 700; font-size: 13px; }}
QLabel#userName {{ color: {NAVY}; font-weight: 700; font-size: 11px; }}
QLabel#userEmail {{ color: {MUTED}; font-size: 9px; }}
QLabel#avatarUser {{ background: {BLUE}; color: #fff; border-radius: 8px; font-weight: 700; font-size: 12px; }}
QLabel#logoTile {{ background: transparent; }}

QLabel#welcome {{ color: {HEADING}; font-size: 40px; font-weight: 500; }}
QLabel#toolTitle {{ color: #fff; font-size: 24px; font-weight: 700; }}
QLabel#toolDesc {{ color: rgba(255,255,255,175); font-size: 12px; }}
QLabel#toolOpen {{ color: #fff; font-weight: 700; font-size: 12px; }}
QFrame#toolSep {{ background: rgba(255,255,255,60); }}
QLabel#toolIconTile {{ background: #fff; border-radius: 16px; }}
QLabel#headerTile {{ background: {NAVY}; border-radius: 14px; }}
QLabel#pageTitle {{ color: {NAVY}; font-size: 13px; font-weight: 700; }}
QLabel#pageTagline {{ color: {MUTED}; font-size: 16px; }}

QFrame#card {{ background: #fff; border: 1px solid {BORDER}; border-radius: 24px; }}
QFrame#chatPanel {{ background: #F0F6FF; border: 1px solid #D6E4F7; border-radius: 24px; }}
QFrame#chatBox {{ background: #fff; border: 1px solid {BORDER}; border-radius: 16px; }}
QFrame#chatHeader {{ background: transparent; border: none; border-bottom: 1px solid {BORDER}; }}
QFrame#chatFooter {{ background: transparent; border: none; border-top: 1px solid {BORDER}; }}
QWidget#chatBody {{ background: #F4F7FB; }}
QFrame#hline {{ background: {BORDER}; border: none; }}

QLabel#sectionTitle {{ color: {NAVY}; font-size: 14px; font-weight: 700; }}
QLabel#subtle {{ color: {MUTED}; font-size: 10px; }}
QLabel#fieldLabel {{ color: {NAVY}; font-size: 12px; font-weight: 700; }}
QLabel#counter {{ color: {MUTED}; font-size: 10px; }}
QLabel#statusOk {{ color: {SKY}; font-size: 10px; }}
QLabel#statusWarn {{ color: #D97706; font-size: 10px; }}
QLabel#errorLabel {{ color: #DC2626; font-size: 12px; }}
QLabel#emptyHint {{ color: {MUTED}; font-size: 12px; }}
QLabel#dayDivider {{ color: {MUTED}; font-size: 9px; }}

QWidget#mailBody {{ background: #fff; }}
QLabel#mailSubject {{ color: {NAVY}; font-size: 16px; font-weight: 700; }}
QLabel#mailAddr {{ color: {TEXT}; font-size: 11px; }}
QLabel#mailText {{ color: {TEXT}; font-size: 12px; }}
QLabel#mailSubject[empty="true"], QLabel#mailAddr[empty="true"], QLabel#mailText[empty="true"] {{ color: {MUTED}; font-weight: 400; }}

QFrame#resultBox {{ background: #EEEFF6; border: 1px dashed #B7BED6; border-radius: 14px; }}
QLabel#resultValue {{ color: {MUTED}; font-size: 15px; font-weight: 700; }}
QLabel#resultValueSet {{ color: {NAVY}; font-size: 15px; font-weight: 700; }}

QFrame#settingsPanel {{ background: #F6F8FC; border: 1px solid {BORDER}; border-radius: 14px; }}

QFrame#fieldCard {{ background: #fff; border: 1px solid {BORDER}; border-radius: 12px; }}
QFrame#fieldCard[selected="true"] {{ background: #EFF6FF; border: 1px solid #93C5FD; }}
QLabel#fieldTitle {{ color: {NAVY}; font-size: 12px; font-weight: 700; }}
QLabel#fieldHint {{ color: {MUTED}; font-size: 9px; }}

QFrame#bubbleOut {{ background: {BLUE}; border-radius: 14px; }}
QFrame#bubbleIn {{ background: #E5E9F2; border-radius: 14px; }}
QLabel#bubbleTextOut {{ color: #fff; font-size: 12px; }}
QLabel#bubbleTextIn {{ color: {TEXT}; font-size: 12px; }}
QLabel#metaOut {{ color: rgba(255,255,255,190); font-size: 9px; }}
QLabel#metaIn {{ color: {MUTED}; font-size: 9px; }}
QLabel#avatar {{ background: {INDIGO}; color: #fff; border-radius: 18px; font-weight: 700; font-size: 11px; }}

QTableWidget {{
    background: #fff; border: none; border-top: 1px solid {BORDER};
    alternate-background-color: #F6F9FD; selection-background-color: #DCE8FF; selection-color: {TEXT};
}}
QTableWidget::item {{ padding: 4px 14px; border-bottom: 1px solid #EDF1F7; }}
QHeaderView {{ background: #EAF2FD; }}
QHeaderView::section {{
    background: #EAF2FD; color: {MUTED}; border: none; padding: 12px 14px;
    font-size: 10px; font-weight: 600;
}}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #C5CEDF; border-radius: 4px; min-height: 30px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: #C5CEDF; border-radius: 4px; min-width: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QMessageBox {{ background: #fff; }}
QMessageBox QPushButton {{ background: {NAVY}; color: #fff; border: none; min-width: 84px; padding: 8px 16px; }}
QMessageBox QPushButton:hover {{ background: {NAVY_HOVER}; }}

QFrame#authCard QLineEdit {{ padding: 7px 12px; font-size: 12px; border-radius: 9px; }}
QFrame#authCard QPushButton#primary {{ padding: 8px 16px; font-size: 12px; border-radius: 9px; }}
QFrame#authCard QLabel#fieldLabel {{ font-size: 11px; }}
QFrame#rightPane {{ background: {BG}; }}
QFrame#authCard {{ background: #fff; border: 1px solid {BORDER}; border-radius: 28px; }}
QLabel#authLogo {{ background: transparent; }}
QLabel#authTitle {{ color: {HEADING}; font-size: 25px; font-weight: 500; }}
QLabel#authSub {{ color: {MUTED}; font-size: 12px; }}
QLabel#plainMuted {{ color: {MUTED}; font-size: 12px; }}

QLabel#heroBrand {{ color: #fff; font-size: 14px; font-weight: 700; }}
QLabel#heroLogo {{ background: #fff; border-radius: 10px; }}
QLabel#heroEyebrow {{ color: #9CC8FF; font-family: {MONO}; font-size: 10px; }}
QLabel#heroTitle {{ color: #fff; font-size: 44px; font-weight: 700; }}
QLabel#heroItalic {{ color: {LIGHT_BLUE}; font-family: {SERIF}; font-size: 48px; font-style: italic; }}
QLabel#heroSub {{ color: #E8EEF8; font-size: 14px; }}
QLabel#heroFoot {{ color: #B8D0F5; font-size: 11px; }}
QFrame#featStrip {{ background: transparent; border-top: 1px solid rgba(255,255,255,45); border-bottom: 1px solid rgba(255,255,255,45); }}
QFrame#vline {{ background: rgba(255,255,255,45); border: none; }}
QLabel#featTile {{ background: {LIGHT_BLUE}; border-radius: 8px; }}
QLabel#featTitle {{ color: #fff; font-size: 11px; font-weight: 700; }}
QLabel#featSub {{ color: #B8D0F5; font-size: 9px; }}
"""
