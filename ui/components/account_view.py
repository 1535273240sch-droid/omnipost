import os
import subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
    QMessageBox, QInputDialog, QLineEdit
)
from PySide6.QtCore import Qt
from loguru import logger

from core.models.account import Account
from core.profiles.manager import profile_manager
from adapters.registry import adapter_registry

class AccountView(QWidget):
    """多账号五维物理隔离沙盒管理面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.accounts: list[Account] = []
        self._init_ui()
        self._load_sample_accounts()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # 头部说明
        header_layout = QHBoxLayout()
        title = QLabel("🛡️ 账号独立物理环境沙盒中心")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")
        subtitle = QLabel("每个账号拥有绝对独立的磁盘 Profile、静态锚定指纹与排他独占锁，杜绝跨账号关联")
        subtitle.setStyleSheet("color: #94A3B8; font-size: 12px;")
        header_layout.addWidget(title)
        header_layout.addSpacing(15)
        header_layout.addWidget(subtitle)
        header_layout.addStretch()

        # 顶部操作栏
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ 新建隔离账号")
        self.btn_add.setObjectName("primary-btn")
        self.btn_add.clicked.connect(self._add_account_dialog)

        self.btn_login = QPushButton("🔑 启动独立窗口扫码登录")
        self.btn_login.clicked.connect(self._trigger_login)

        self.btn_open_dir = QPushButton("📁 打开物理沙盒目录")
        self.btn_open_dir.clicked.connect(self._open_profile_dir)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_login)
        btn_layout.addWidget(self.btn_open_dir)
        btn_layout.addStretch()

        # 账号表格
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "账号 ID", "发布平台", "物理沙盒目录", "绑定专属代理", "硬件指纹状态", "登录态"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        layout.addLayout(header_layout)
        layout.addLayout(btn_layout)
        layout.addWidget(self.table)

    def _load_sample_accounts(self):
        """预置首批平台的隔离账号"""
        preset_accounts = [
            ("douyin_main", "douyin", "抖音主账号"),
            ("xhs_official", "xiaohongshu", "小红书官方号"),
            ("bili_channel", "bilibili", "B站发布号"),
            ("baijia_news", "baijiahao", "百家号聚合"),
        ]
        for acc_id, platform, nickname in preset_accounts:
            env = profile_manager.get_environment(acc_id, platform)
            account = Account(
                id=acc_id,
                platform=platform,
                nickname=nickname,
                profile_dir=env.profile_dir,
                is_logged_in=False
            )
            self.accounts.append(account)
        self._refresh_table()

    def _refresh_table(self):
        self.table.setRowCount(len(self.accounts))
        for row, acc in enumerate(self.accounts):
            env = profile_manager.get_environment(acc.id, acc.platform, acc.proxy_url)
            fp_info = f"UA: ...{env.fingerprint.user_agent[-20:]} | 1920x1080"

            self.table.setItem(row, 0, QTableWidgetItem(acc.id))
            self.table.setItem(row, 1, QTableWidgetItem(acc.platform))
            self.table.setItem(row, 2, QTableWidgetItem(acc.profile_dir))
            self.table.setItem(row, 3, QTableWidgetItem(acc.proxy_url or "直连 (无代理)"))
            self.table.setItem(row, 4, QTableWidgetItem(fp_info))

            status_item = QTableWidgetItem("🟢 已就绪" if acc.is_logged_in else "⚪ 待登录")
            status_item.setForeground(Qt.green if acc.is_logged_in else Qt.lightGray)
            self.table.setItem(row, 5, status_item)

    def _add_account_dialog(self):
        acc_id, ok = QInputDialog.getText(self, "新建账号", "请输入唯一账号 ID (如 douyin_sub_01):")
        if not ok or not acc_id:
            return

        platforms = adapter_registry.list_supported_platforms()
        platform, ok = QInputDialog.getItem(self, "选择平台", "目标平台:", platforms, 0, False)
        if not ok or not platform:
            return

        env = profile_manager.get_environment(acc_id.strip(), platform)
        account = Account(
            id=acc_id.strip(),
            platform=platform,
            nickname=acc_id.strip(),
            profile_dir=env.profile_dir,
            is_logged_in=False
        )
        self.accounts.append(account)
        self._refresh_table()
        QMessageBox.information(self, "成功", f"账号 [{acc_id}] 物理隔离沙盒已创建！\n目录: {env.profile_dir}")

    def _open_profile_dir(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.accounts):
            QMessageBox.warning(self, "提示", "请先选择一个账号")
            return
        acc = self.accounts[row]
        if os.path.exists(acc.profile_dir):
            subprocess.Popen(f'explorer "{acc.profile_dir}"')
        else:
            QMessageBox.warning(self, "错误", "沙盒目录不存在")

    def _trigger_login(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self.accounts):
            QMessageBox.warning(self, "提示", "请先在表格中选择一个需要登录的账号")
            return
        acc = self.accounts[row]
        QMessageBox.information(
            self,
            "引导扫码登录",
            f"系统即将为账号 [{acc.id}] 在其专属独立沙盒中拉起浏览器窗口。\n\n"
            f"平台: {acc.platform}\n"
            f"物理目录: {acc.profile_dir}\n\n"
            "登录成功后关闭窗口，Cookie 与登录态将自动固化在专属目录中。"
        )
