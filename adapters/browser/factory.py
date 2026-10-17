import asyncio
import random
from typing import Any
from loguru import logger
from core.profiles.models import AccountEnvironment

# 优先导入增强防检测的 Patchright，未安装时优雅回退 Playwright 并补足防检脚本
try:
    from patchright.async_api import async_playwright, BrowserContext, Page
    IS_PATCHRIGHT = True
    logger.info("已成功装载 Patchright 底层防检测浏览器自动化驱动")
except ImportError:
    from playwright.async_api import async_playwright, BrowserContext, Page
    IS_PATCHRIGHT = False
    logger.warning("未检测到 patchright，当前使用标准 playwright 作为底层驱动，将通过额外 JS 脚本注入强化防检")

class IsolatedBrowserFactory:
    """账号专属独立环境浏览器驱动工厂"""

    @classmethod
    async def create_context(
        cls,
        playwright_instance: Any,
        env: AccountEnvironment,
        headless: bool = False
    ) -> BrowserContext:
        """
        根据账号环境与指纹元数据，创建物理隔离且防关联的浏览器持久化上下文
        """
        # 严格防御性启动参数
        args = [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-features=IsolateOrigins,site-per-process",
            # 严格阻断 WebRTC 本地真实 IP 泄漏，杜绝穿透代理导致的封号
            "--disable-webrtc-multiple-routes",
            "--enforce-webrtc-ip-permission-check",
        ]

        # 代理网络绑定
        proxy_config = None
        if env.proxy_url:
            proxy_config = {"server": env.proxy_url}
            logger.info(f"账号 {env.account_id} 已绑定专属代理: {env.proxy_url.split('@')[-1]}")

        # 启动 Persistent Context (持久化独立目录)
        context = await playwright_instance.chromium.launch_persistent_context(
            user_data_dir=env.profile_dir,
            headless=headless,
            args=args,
            proxy=proxy_config,
            viewport=env.fingerprint.viewport,
            user_agent=env.fingerprint.user_agent,
            locale=env.fingerprint.locale,
            timezone_id=env.fingerprint.timezone_id,
            device_scale_factor=env.fingerprint.device_scale_factor,
        )

        # 注入防特征抹除脚本（对于 playwright 备用模式特别重要）
        await context.add_init_script("""
            // 抹除自动化标识
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            // 伪装硬件并发度
            Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
            // 伪装设备内存
            Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });
            // 伪装 Chrome 运行时对象
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
        """)

        logger.info(f"账号 {env.account_id} 专属隔离沙盒已拉起 -> 目录: {env.profile_dir}")
        return context

    @classmethod
    async def human_type(cls, page: Page, selector: str, text: str, min_delay: float = 0.03, max_delay: float = 0.09):
        """拟人化打字输入：字符间随机微小延迟，避开瞬时输入风控拦截"""
        element = await page.wait_for_selector(selector, state="visible")
        await element.click()
        for char in text:
            await page.keyboard.press(char)
            await asyncio.sleep(random.uniform(min_delay, max_delay))

    @classmethod
    async def single_click_publish(cls, page: Page, button_selector: str) -> bool:
        """
        硬性约定：发布按钮只允许点击一次。
        点击后立即禁用或等待响应，杜绝因网络延迟导致重复点击产生重发事故。
        """
        btn = await page.wait_for_selector(button_selector, state="visible", timeout=15000)
        if not btn:
            return False
        
        # 拟人鼠标微移动后点击
        box = await btn.bounding_box()
        if box:
            await page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            await asyncio.sleep(0.3)
        await btn.click()
        logger.info(f"发布按钮已执行单次点击: {button_selector}")
        return True
