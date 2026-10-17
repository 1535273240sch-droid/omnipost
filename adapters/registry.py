from typing import Dict
from loguru import logger

from adapters.base import PlatformAdapter
from adapters.browser.douyin import douyin_adapter
from adapters.browser.xiaohongshu import xiaohongshu_adapter
from adapters.cli.bilibili import bilibili_adapter
from adapters.cli.baijiahao import baijiahao_adapter
from adapters.manual.fallback import ManualFallbackAdapter

class AdapterRegistry:
    """平台适配器注册与分发中心 (支持插件化热插拔扩展)"""

    def __init__(self):
        self._adapters: Dict[str, PlatformAdapter] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register(douyin_adapter)
        self.register(xiaohongshu_adapter)
        self.register(bilibili_adapter)
        self.register(baijiahao_adapter)

    def register(self, adapter: PlatformAdapter):
        """注册新平台适配器"""
        self._adapters[adapter.platform] = adapter
        logger.info(f"已装载平台适配器: [{adapter.platform}] -> 后端: {adapter.backend}, 能力: {adapter.capabilities}")

    def get(self, platform: str) -> PlatformAdapter:
        """获取平台适配器，若无自动化适配则自动降级为手动发布包"""
        if platform in self._adapters:
            return self._adapters[platform]

        logger.warning(f"未找到自动化适配器 [{platform}]，自动降级为通用手动发布兜底模式")
        fallback = ManualFallbackAdapter(platform=platform, publish_url=f"https://www.google.com/search?q={platform}+创作者中心")
        return fallback

    def list_supported_platforms(self) -> list[str]:
        return list(self._adapters.keys())

adapter_registry = AdapterRegistry()
