import asyncio
import json
import os
import shutil
from typing import Any
from loguru import logger
from config.settings import settings

class CLIExecutor:
    """MatrixMedia CLI 独立命令行子进程调用执行器 (遵循 GPL-2.0 隔离规范)"""

    def __init__(self, cli_bin: str | None = None):
        self.cli_bin = cli_bin or settings.MATRIX_MEDIA_CLI_PATH

    def is_available(self) -> bool:
        """检查 MatrixMedia 命令行工具是否已在环境变量或系统路径中"""
        return shutil.which(self.cli_bin) is not None

    async def execute_command(self, args: list[str], timeout: float = 300.0) -> tuple[int, dict[str, Any] | None, str]:
        """
        异步调用 CLI 子进程并解析 JSON 结果
        :return: (exit_code, parsed_json_or_none, raw_stdout)
        """
        cmd = [self.cli_bin] + args
        logger.info(f"正在拉起外部 CLI 进程: {' '.join(cmd)}")

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=os.environ.copy()
            )

            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            stdout_str = stdout_bytes.decode("utf-8", errors="replace").strip()
            stderr_str = stderr_bytes.decode("utf-8", errors="replace").strip()
            exit_code = process.returncode or 0

            logger.info(f"CLI 进程执行结束，退出码: {exit_code}")
            if stderr_str:
                logger.debug(f"CLI 进程 stderr: {stderr_str}")

            # 尝试从 stdout 中提取标准 JSON
            parsed_json = None
            try:
                # 寻找包含花括号的有效 JSON 片段
                for line in stdout_str.splitlines():
                    line = line.strip()
                    if line.startswith("{") and line.endswith("}"):
                        parsed_json = json.loads(line)
                        break
            except Exception:
                pass

            return exit_code, parsed_json, stdout_str

        except asyncio.TimeoutError:
            logger.error(f"CLI 进程执行超时 ({timeout}s)，已强制中断")
            try:
                process.kill()
            except Exception:
                pass
            return -1, None, "Process execution timed out"
        except FileNotFoundError:
            logger.error(f"未找到 MatrixMedia 可执行文件: {self.cli_bin}，请确保已安装并在 PATH 中")
            return 127, None, f"Command not found: {self.cli_bin}"
        except Exception as e:
            logger.error(f"调用 CLI 进程遇到未知异常: {e}")
            return -2, None, str(e)

cli_executor = CLIExecutor()
