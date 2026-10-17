"""
顶级深邃量化终端视觉与交互设计规范 (Pure Black & Liquid Glass)
- 极致纯黑: #000000
- 液态深灰玻璃底: #0A0D12 / rgba(14, 18, 24, 0.85)
- 卡片微浮雕: rgba(22, 28, 38, 0.70)
- 白金微折射边框: 1px solid rgba(255, 255, 255, 0.10)
- 高定翡翠霓虹绿: #00F5A0 (成功/安全/在线)
- 霓虹绯红: #FF4D5E (失败/异常/警报)
- 钛金冷灰: #94A3B8 / #CBD5E1
- 钻石纯白: #FFFFFF
"""

DARK_LIQUID_GLASS_QSS = """
/* 全局基础背景 */
QMainWindow, QDialog, QWidget#CentralWidget {
    background-color: #000000;
    color: #CBD5E1;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 13px;
}

/* 导航选项卡栏 (Liquid Glass TabBar) */
QTabWidget::pane {
    border: 1px solid rgba(255, 255, 255, 0.08);
    background-color: #05070A;
    border-radius: 8px;
    margin-top: 10px;
}

QTabBar::tab {
    background-color: rgba(18, 22, 28, 0.6);
    color: #94A3B8;
    border: 1px solid rgba(255, 255, 255, 0.05);
    padding: 10px 22px;
    margin-right: 6px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background-color: #121822;
    color: #FFFFFF;
    border: 1px solid rgba(0, 245, 160, 0.4);
    border-bottom: 2px solid #00F5A0;
}

QTabBar::tab:hover:!selected {
    background-color: rgba(30, 38, 50, 0.8);
    color: #FFFFFF;
}

/* 玻璃质感面板与卡片 */
QGroupBox, QFrame.glass-card {
    background-color: rgba(14, 18, 24, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 8px;
    padding: 16px;
    margin-top: 12px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #00F5A0;
    font-weight: 700;
}

/* 输入框与编辑器 */
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
    background-color: #07090D;
    color: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 6px;
    padding: 8px 12px;
    selection-background-color: rgba(0, 245, 160, 0.3);
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border: 1px solid #00F5A0;
    background-color: #0B0E14;
}

/* 高定按钮 */
QPushButton {
    background-color: rgba(22, 28, 38, 0.9);
    color: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: rgba(35, 45, 60, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.25);
}

QPushButton:pressed {
    background-color: #0D1219;
}

/* 主要操作按钮 (高光翡翠绿) */
QPushButton#primary-btn {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00D58A, stop:1 #00F5A0);
    color: #000000;
    border: none;
    font-weight: 700;
}

QPushButton#primary-btn:hover {
    background-color: #33FFB5;
}

/* 危险/警报按钮 */
QPushButton#danger-btn {
    background-color: rgba(255, 77, 94, 0.15);
    color: #FF4D5E;
    border: 1px solid rgba(255, 77, 94, 0.4);
}

QPushButton#danger-btn:hover {
    background-color: rgba(255, 77, 94, 0.3);
}

/* 表格与树状视图 */
QTableWidget, QTableView {
    background-color: #05070A;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 6px;
    gridline-color: rgba(255, 255, 255, 0.05);
    color: #CBD5E1;
}

QHeaderView::section {
    background-color: #0E131B;
    color: #94A3B8;
    padding: 8px;
    border: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    font-weight: 600;
}

QTableWidget::item:selected {
    background-color: rgba(0, 245, 160, 0.15);
    color: #FFFFFF;
}

/* 滚动条 */
QScrollBar:vertical {
    border: none;
    background: #000000;
    width: 6px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: rgba(255, 255, 255, 0.2);
    min-height: 20px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #00F5A0;
}
"""
