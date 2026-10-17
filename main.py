import sys
import os
import asyncio
from pathlib import Path

# 将项目根目录加入模块搜索路径
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtWidgets import QApplication
from loguru import logger

from config.settings import settings
from database.session import init_db
from ui.main_window import MainWindow

def setup_logging():
    log_file = settings.LOGS_DIR / "omnipost_{time}.log"
    logger.add(str(log_file), rotation="50 MB", retention="10 days", level="DEBUG")
    logger.info("OmniPost 全平台内容分发系统正在启动...")

def main():
    setup_logging()

    # 异步预热并初始化数据库结构 (支持自动降级至 SQLite)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(init_db())
    except Exception as e:
        logger.warning(f"异步数据库预热提示 (不影响主程序拉起): {e}")

    app = QApplication(sys.argv)
    app.setApplicationName("OmniPost")

    window = MainWindow()
    window.show()

    logger.info("桌面客户端视窗已成功展现")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
