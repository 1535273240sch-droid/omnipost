import asyncio
from loguru import logger
from patchright.async_api import async_playwright

from adapters.base import PlatformAdapter, LoginResult, PublishResult, JobStatus, ErrorCode
from adapters.browser.factory import IsolatedBrowserFactory
from core.models.account import Account
from core.models.job import PublishJob
from core.profiles.manager import profile_manager

XHS_CREATOR_URL = "https://creator.xiaohongshu.com"
XHS_PUBLISH_URL = "https://creator.xiaohongshu.com/publish/publish"

class XiaohongshuAdapter:
    """小红书创作者服务平台自动化适配器 (基于物理隔离沙盒)"""

    platform = "xiaohongshu"
    backend = "browser"
    capabilities = {"image_text", "video"}

    async def check_login(self, account: Account) -> bool:
        """检查小红书账号 Profile 登录态是否有效"""
        env = profile_manager.get_environment(account.id, self.platform, account.proxy_url)
        async with profile_manager.lock_account(account.id):
            async with async_playwright() as p:
                context = await IsolatedBrowserFactory.create_context(p, env, headless=True)
                page = await context.new_page()
                try:
                    await page.goto(XHS_CREATOR_URL, timeout=30000, wait_until="domcontentloaded")
                    await asyncio.sleep(2)
                    # 小红书登录后会显示创作者头像或导航菜单
                    is_login = await page.locator(".user-avatar, .con-header, a[href*='publish']").count() > 0
                    logger.info(f"小红书账号 {account.id} 登录态检测结果: {'有效' if is_login else '已失效'}")
                    return is_login
                except Exception as e:
                    logger.error(f"检测小红书登录态异常: {e}")
                    return False
                finally:
                    await context.close()

    async def login(self, account: Account) -> LoginResult:
        """拉起小红书专属隔离窗口供用户扫码登录"""
        env = profile_manager.get_environment(account.id, self.platform, account.proxy_url)
        async with profile_manager.lock_account(account.id):
            async with async_playwright() as p:
                context = await IsolatedBrowserFactory.create_context(p, env, headless=False)
                page = await context.new_page()
                try:
                    logger.info(f"已拉起小红书专属隔离浏览器窗口，请在窗口中扫码登录...")
                    await page.goto(XHS_CREATOR_URL, timeout=60000)

                    # 等待用户扫码
                    for _ in range(36):
                        await asyncio.sleep(5)
                        if await page.locator(".user-avatar, .con-header, a[href*='publish']").count() > 0:
                            logger.info(f"检测到小红书账号 {account.id} 登录成功，Profile 自动持久化！")
                            nickname = account.nickname
                            name_el = page.locator(".user-name, .con-header-name").first
                            if await name_el.count() > 0:
                                nickname = await name_el.inner_text()
                            return LoginResult(success=True, account_id=account.id, nickname=nickname)

                    return LoginResult(
                        success=False,
                        account_id=account.id,
                        error_code=ErrorCode.LOGIN_EXPIRED,
                        error_msg="登录超时，未检测到扫码成功"
                    )
                except Exception as e:
                    return LoginResult(
                        success=False,
                        account_id=account.id,
                        error_code=ErrorCode.UNKNOWN_RESULT,
                        error_msg=f"登录过程异常: {str(e)}"
                    )
                finally:
                    await context.close()

    async def publish(self, job: PublishJob, account: Account) -> PublishResult:
        """在独立沙盒内执行小红书图文/视频发布"""
        env = profile_manager.get_environment(account.id, self.platform, account.proxy_url)
        rendered = job.rendered
        title = rendered.get("title", "")
        body = rendered.get("body", "")
        media_paths = rendered.get("media_paths", [])

        if not media_paths:
            return PublishResult(
                success=False,
                job_id=job.id,
                error_code=ErrorCode.RULE_VIOLATION,
                error_msg="小红书发布必须提供至少一张图片或一个视频文件"
            )

        async with profile_manager.lock_account(account.id):
            async with async_playwright() as p:
                context = await IsolatedBrowserFactory.create_context(p, env, headless=False)
                page = await context.new_page()
                try:
                    logger.info(f"正在进入小红书发布页面: {account.id}")
                    await page.goto(XHS_PUBLISH_URL, timeout=45000, wait_until="networkidle")

                    # 1. 登录态校验
                    if "login" in page.url:
                        return PublishResult(
                            success=False,
                            job_id=job.id,
                            error_code=ErrorCode.LOGIN_EXPIRED,
                            error_msg="小红书登录态已失效"
                        )

                    # 2. 上传素材
                    file_input = page.locator("input[type='file']").first
                    await file_input.wait_for(state="attached", timeout=15000)
                    await file_input.set_input_files(media_paths)
                    logger.info(f"小红书媒体文件已上传: {len(media_paths)} 项")
                    await asyncio.sleep(4)

                    # 3. 填写标题 (上限 20 字)
                    title_input = page.locator("input[placeholder*='填写标题']").first
                    if await title_input.count() > 0:
                        await IsolatedBrowserFactory.human_type(page, title_input, title[:20])

                    # 4. 填写正文与话题
                    desc_input = page.locator("textarea[placeholder*='填写更全面的描述'], .post-editor, [contenteditable='true']").first
                    if await desc_input.count() > 0:
                        full_body = body
                        tags = rendered.get("tags", [])
                        if tags:
                            full_body += "\n\n" + " ".join([f"#{t}" for t in tags])
                        await IsolatedBrowserFactory.human_type(page, desc_input, full_body)

                    # 5. 单次点击发布
                    publish_btn_selector = "button:has-text('发布'), .publishBtn"
                    btn_clicked = await IsolatedBrowserFactory.single_click_publish(page, publish_btn_selector)

                    if not btn_clicked:
                        return PublishResult(
                            success=False,
                            job_id=job.id,
                            error_code=ErrorCode.SELECTOR_CHANGED,
                            error_msg="未找到小红书发布按钮"
                        )

                    # 6. 等待确认结果
                    for _ in range(12):
                        await asyncio.sleep(2)
                        current_url = page.url
                        page_text = await page.content()
                        if "manage" in current_url or "发布成功" in page_text:
                            logger.info(f"小红书任务 {job.id} 发布成功！")
                            return PublishResult(success=True, job_id=job.id, result_url=current_url)
                        if "验证码" in page_text or "滑动验证" in page_text:
                            return PublishResult(
                                success=False,
                                job_id=job.id,
                                error_code=ErrorCode.NEED_VERIFY,
                                error_msg="小红书触发滑块或安全验证，请人工介入",
                                require_human_confirm=True
                            )

                    logger.warning(f"小红书任务 {job.id} 超时未确认结果，标记待确认")
                    return PublishResult(
                        success=False,
                        job_id=job.id,
                        error_code=ErrorCode.UNKNOWN_RESULT,
                        error_msg="已触发单次发布，但未能在规定时间内获取成功标识，请人工核查后台",
                        require_human_confirm=True
                    )

                except Exception as e:
                    logger.error(f"小红书发布流程异常: {e}")
                    return PublishResult(
                        success=False,
                        job_id=job.id,
                        error_code=ErrorCode.UNKNOWN_RESULT,
                        error_msg=f"发布异常: {str(e)}",
                        require_human_confirm=True
                    )
                finally:
                    await context.close()

    async def fetch_status(self, job: PublishJob, account: Account) -> JobStatus:
        return job.status

xiaohongshu_adapter = XiaohongshuAdapter()
