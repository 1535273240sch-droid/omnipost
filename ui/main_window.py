import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QPushButton
)
from PySide6.QtCore import Qt

from ui.styles import DARK_LIQUID_GLASS_QSS
from ui.components.account_view import AccountView
from ui.components.editor_view import EditorView
from ui.components.monitor_view import MonitorView

class MainWindow(QMainWindow):
    """OmniPost 全平台内容分发系统主桌面视窗"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("OmniPost - 全平台内容分发系统 (五维物理隔离引擎)")
        self.resize(1280, 840)
        self.setStyleSheet(DARK_LIQUID_GLASS_QSS)

        central_widget = QWidget()
        central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 12, 16, 16)
        main_layout.setSpacing(10)

        # 顶部品牌导航高光条 (Pure Black & Liquid Glass Header)
        brand_layout = QHBoxLayout()
        logo_label = QLabel("⚡ OmniPost Matrix Hub")
        logo_label.setStyleSheet("font-size: 18px; font-weight: 800; color: #FFFFFF; letter-spacing: 1px;")

        badge = QLabel("• 物理环境隔离已激活")
        badge.setStyleSheet("color: #00F5A0; background-color: rgba(0, 245, 160, 0.12); border: 1px solid rgba(0, 245, 160, 0.3); border-radius: 12px; padding: 2px 10px; font-weight: 600; font-size: 11px;")

        version_label = QLabel("v1.0.0 · Core / Celery / Patchright")
        version_label.setStyleSheet("color: #64748B; font-size: 11px;")

        brand_layout.addWidget(logo_label)
        brand_layout.addSpacing(8)
        brand_layout.addWidget(badge)
        brand_layout.addStretch()
        brand_layout.addWidget(version_label)

        # 核心功能选项卡
        self.tabs = QTabWidget()

        self.account_view = AccountView()
        self.editor_view = EditorView()
        self.monitor_view = MonitorView(
            get_content_callback=self.editor_view.get_current_content,
            get_accounts_callback=lambda: self.account_view.accounts
        )

        self.tabs.addTab(self.account_view, "🛡️ 多账号隔离沙盒")
        self.tabs.addTab(self.editor_view, "✍️ 内容创作与改写预览")
        self.tabs.addTab(self.monitor_view, "🚀 矩阵分发与监控中枢")

        main_layout.addLayout(brand_layout)
        main_layout.addWidget(self.tabs)

        self.statusBar().showMessage("系统就绪：已挂载 4 个主流平台适配器，每个账号独立运行在专用 Profile 沙盒中。")
        self.statusBar().setStyleSheet("color: #94A3B8; background-color: #000000; border-top: 1px solid rgba(255,255,255,0.06);")
