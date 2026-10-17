import uuid
import asyncio
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
    QPlainTextEdit, QProgressBar, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from loguru import logger

from core.models.job import PublishJob, JobStatus
from core.models.account import Account
from core.models.content import Content
from core.rules.engine import rule_engine
from tasks.dispatcher import task_dispatcher

class MonitorView(QWidget):
    """一键矩阵分发控制台与实时任务日志流监控"""

    def __init__(self, get_content_callback, get_accounts_callback, parent=None):
        super().__init__(parent)
        self.get_content_callback = get_content_callback
        self.get_accounts_callback = get_accounts_callback
        self.jobs: list[PublishJob] = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # 头部控制栏
        top_layout = QHBoxLayout()
        title = QLabel("🚀 一键多平台矩阵分发与状态追溯中枢")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFFFFF;")

        self.btn_dispatch = QPushButton("⚡ 一键矩阵分发 (4个平台并行)")
        self.btn_dispatch.setObjectName("primary-btn")
        self.btn_dispatch.setFixedHeight(36)
        self.btn_dispatch.clicked.connect(self._start_batch_dispatch)

        top_layout.addWidget(title)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_dispatch)

        # 任务表格
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "任务 ID", "目标平台", "执行账号", "任务状态", "发布链接", "异常状态/确认原因", "时间"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)

        # 底部日志终端
        log_lbl = QLabel("💻 实时底层调度终端流 (Pure Black Console):")
        log_lbl.setStyleSheet("color: #94A3B8; font-weight: bold; margin-top: 8px;")
        self.log_console = QPlainTextEdit()
        self.log_console.setReadOnly(True)
        self.log_console.setMaximumHeight(180)
        self.log_console.setStyleSheet(
            "background-color: #000000; color: #00F5A0; font-family: 'Consolas', monospace; font-size: 12px; border: 1px solid rgba(255,255,255,0.1);"
        )

        layout.addLayout(top_layout)
        layout.addWidget(self.table)
        layout.addWidget(log_lbl)
        layout.addWidget(self.log_console)

        self._log("OmniPost 矩阵调度监控中心初始化完成，五维物理隔离与双后端就绪。")

    def _log(self, text: str):
        time_str = datetime.now().strftime("%H:%M:%S")
        self.log_console.appendPlainText(f"[{time_str}] {text}")

    def _start_batch_dispatch(self):
        content: Content = self.get_content_callback()
        accounts: list[Account] = self.get_accounts_callback()

        if not accounts:
            QMessageBox.warning(self, "提示", "请先在账号管理中心添加至少一个账号！")
            return

        self._log(f"开始准备分发内容: [{content.title[:25]}...] 到 {len(accounts)} 个平台账号")

        # 批量创建任务
        new_jobs = []
        for acc in accounts:
            try:
                # 规则引擎套用改写
                rendered = rule_engine.render(content, acc.platform)
            except Exception as e:
                self._log(f"❌ 平台 [{acc.platform}] 规则套用失败: {e}")
                continue

            job = PublishJob(
                id=f"job_{uuid.uuid4().hex[:8]}",
                content_id=content.id,
                platform=acc.platform,
                account_id=acc.id,
                rendered=rendered,
                status=JobStatus.PENDING
            )
            new_jobs.append((job, acc))
            self.jobs.append(job)

        self._refresh_table()

        # 异步分发任务
        for job, acc in new_jobs:
            self._dispatch_single(job, acc)

    def _dispatch_single(self, job: PublishJob, acc: Account):
        self._log(f"正在拉起沙盒调度: 平台={job.platform}, 账号={acc.id}, 目录={acc.profile_dir}")
        job.status = JobStatus.RUNNING
        self._refresh_table()

        # 使用定时器异步模拟/执行
        async def run():
            result = await task_dispatcher.execute_job_now(job, acc)
            self._log(f"任务 {job.id} 执行完毕: 状态={job.status.value}, 原因={result.error_msg or 'OK'}")
            self._refresh_table()

        # 在异步事件循环中运行
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            asyncio.create_task(run())
        else:
            loop.run_until_complete(run())

    def _refresh_table(self):
        self.table.setRowCount(len(self.jobs))
        for row, job in enumerate(self.jobs):
            self.table.setItem(row, 0, QTableWidgetItem(job.id))
            self.table.setItem(row, 1, QTableWidgetItem(job.platform))
            self.table.setItem(row, 2, QTableWidgetItem(job.account_id))

            status_item = QTableWidgetItem(job.status.value.upper())
            if job.status == JobStatus.SUCCESS:
                status_item.setForeground(Qt.green)
            elif job.status == JobStatus.RUNNING:
                status_item.setForeground(Qt.yellow)
            elif job.status == JobStatus.NEED_CONFIRM:
                status_item.setForeground(Qt.cyan)
            else:
                status_item.setForeground(Qt.red)
            self.table.setItem(row, 3, status_item)

            self.table.setItem(row, 4, QTableWidgetItem(job.result_url or "--"))
            self.table.setItem(row, 5, QTableWidgetItem(job.error_msg or "无异常"))
            time_str = job.created_at.strftime("%H:%M:%S")
            self.table.setItem(row, 6, QTableWidgetItem(time_str))
