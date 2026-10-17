import asyncio
from loguru import logger
from patchright.async_api import async_playwright

from adapters.base import PlatformAdapter, LoginResult, PublishResult, JobStatus, ErrorCode
from adapters.browser.factory import IsolatedBrowserFactory
from core.models.account import Account
from core.models.job import PublishJob
from core.profiles.manager import profile_manager

DOUYIN_CREATOR_URL = "https://creator.douyin.com"
DOUYIN_UPLOAD_URL = "https://creator.douyin.com/creator-micro/content/upload"

class DouyinAdapter:
    """抖音创作者中心自动化适配器 (基于物理隔离沙盒)"""

    platform = "douyin"
    backend = "browser"
    capabilities = {"video", "image_text"}

    async def check_login(self, account: Account) -> bool:
        """检查抖音账号 Profile 登录态是否有效"""
        env = profile_manager.get_environment(account.id, self.platform, account.proxy_url)
        async with profile_manager.lock_account(account.id):
            async with async_playwright() as p:
                context = await IsolatedBrowserFactory.create_context(p, env, headless=True)
                page = await context.new_page()
                try:
                    await page.goto(DOUYIN_CREATOR_URL, timeout=30000, wait_until="domcontentloaded")
                    await asyncio.sleep(2)
                    # 检查页面是否包含创作者中心核心已登录元素（如创作者头像、发布按钮等）
                    is_login = await page.locator(".creator-header, .header-avatar, a[href*='content/upload']").count() > 0
                    logger.info(f"抖音账号 {account.id} 登录态检测结果: {'有效' if is_login else '已失效'}")
                    return is_login
                except Exception as e:
                    logger.error(f"检测抖音登录态异常: {e}")
                    return False
                finally:
                    await context.close()

    async def login(self, account: Account) -> LoginResult:
        """拉起独立隔离窗口供用户扫码登录，完成后自动持久化 Profile"""
        env = profile_manager.get_environment(account.id, self.platform, account.proxy_url)
        async with profile_manager.lock_account(account.id):
            async with async_playwright() as p:
                # 引导登录必须为有头模式 (headless=False)
                context = await IsolatedBrowserFactory.create_context(p, env, headless=False)
                page = await context.new_page()
                try:
                    logger.info(f"已拉起抖音专属隔离浏览器窗口，请在窗口中扫码或输入手机验证码完成登录...")
                    await page.goto(DOUYIN_CREATOR_URL, timeout=60000)
                    
                    # 轮询等待登录成功（最多等待 3 分钟）
                    for _ in range(36):
                        await asyncio.sleep(5)
                        if await page.locator(".creator-header, .header-avatar, a[href*='content/upload']").count() > 0:
                            logger.info(f"检测到抖音账号 {account.id} 登录成功，Profile 自动持久化！")
                            # 尝试提取昵称
                            nickname = account.nickname
                            name_el = page.locator(".user-name, .header-user-name").first
                            if await name_el.count() > 0:
                                nickname = await name_el.inner_text()
                            return LoginResult(success=True, account_id=account.id, nickname=nickname)
                    
                    return LoginResult(
                        success=False,
                        account_id=account.id,
                        error_code=ErrorCode.LOGIN_EXPIRED,
                        error_msg="登录超时，未在指定时间内检测到扫码成功"
                    )
                except Exception as e:
                    return LoginResult(
                        success=False,
                        account_id=account.id,
                        error_code=ErrorCode.UNKNOWN_RESULT,
                        error_msg=f"登录过程发生异常: {str(e)}"
                    )
                finally:
                    await context.close()

    async def publish(self, job: PublishJob, account: Account) -> PublishResult:
        """
        在独立沙盒内执行抖音发布流程。
        严格遵守：单次点击发布按钮、不可确认状态置为 UNKNOWN_RESULT。
        """
        env = profile_manager.get_environment(account.id, self.platform, account.proxy_url)
        rendered = job.rendered
        title = rendered.get("title", "")
        media_paths = rendered.get("media_paths", [])

        if not media_paths:
            return PublishResult(
                success=False,
                job_id=job.id,
                error_code=ErrorCode.RULE_VIOLATION,
                error_msg="缺少待上传的视频或图片媒体文件"
            )

        async with profile_manager.lock_account(account.id):
            async with async_playwright() as p:
                context = await IsolatedBrowserFactory.create_context(p, env, headless=False)
                page = await context.new_page()
                try:
                    logger.info(f"正在进入抖音创作者发布中心: {account.id}")
                    await page.goto(DOUYIN_UPLOAD_URL, timeout=45000, wait_until="networkidle")

                    # 1. 检测是否需要重新登录
                    if "login" in page.url or await page.locator("text=登录").count() > 0:
                        return PublishResult(
                            success=False,
                            job_id=job.id,
                            error_code=ErrorCode.LOGIN_EXPIRED,
                            error_msg="账号登录态已失效，请重新扫码登录"
                        )

                    # 2. 上传文件 (处理 input[type=file])
                    file_input = page.locator("input[type='file']").first
                    await file_input.wait_for(state="attached", timeout=15000)
                    await file_input.set_input_files(media_paths[0])
                    logger.info(f"已提交媒体文件上传: {media_paths[0]}")

                    # 等待上传与转码完成（根据文件大小适配）
                    await asyncio.sleep(5)

                    # 3. 填写标题与话题
                    title_input = page.locator("input[placeholder*='标题'], textarea[placeholder*='输入作品简介'], [contenteditable='true']").first
                    if await title_input.count() > 0:
                        full_text = title
                        tags = rendered.get("tags", [])
                        if tags:
                            full_text += " " + " ".join([f"#{t}" for t in tags])
                        await IsolatedBrowserFactory.human_type(page, title_input, full_text)

                    # 4. 单次点击“发布”按钮
                    publish_btn_selector = "button:has-text('发布'), .publish-btn, .button--primary:has-text('发布')"
                    btn_clicked = await IsolatedBrowserFactory.single_click_publish(page, publish_btn_selector)

                    if not btn_clicked:
                        return PublishResult(
                            success=False,
                            job_id=job.id,
                            error_code=ErrorCode.SELECTOR_CHANGED,
                            error_msg="未找到发布按钮，可能是平台改版"
                        )

                    # 5. 校验发布结果
                    # 等待发布成功的特征页面或提示
                    for _ in range(12):
                        await asyncio.sleep(2)
                        current_url = page.url
                        page_content = await page.content()
                        if "manage" in current_url or "发布成功" in page_content:
                            logger.info(f"抖音任务 {job.id} 发布成功！")
                            return PublishResult(
                                success=True,
                                job_id=job.id,
                                result_url=current_url
                            )
                        if "验证码" in page_content or "安全验证" in page_content:
                            return PublishResult(
                                success=False,
                                job_id=job.id,
                                error_code=ErrorCode.NEED_VERIFY,
                                error_msg="触发平台安全验证，需人工介入处理",
                                require_human_confirm=True
                            )

                    # 达到超时但无法确切识别是否成功的兜底约定
                    logger.warning(f"抖音任务 {job.id} 已点击发布，但未能在超时时间内确认最终结果状态")
                    return PublishResult(
                        success=False,
                        job_id=job.id,
                        error_code=ErrorCode.UNKNOWN_RESULT,
                        error_msg="已点击发布，但系统无法自动核实结果，已标记为待确认，请人工到后台查看，切勿重复点击",
                        require_human_confirm=True
                    )

                except Exception as e:
                    logger.error(f"抖音发布流程执行异常: {e}")
                    return PublishResult(
                        success=False,
                        job_id=job.id,
                        error_code=ErrorCode.UNKNOWN_RESULT,
                        error_msg=f"执行发布异常: {str(e)}",
                        require_human_confirm=True
                    )
                finally:
                    await context.close()

    async def fetch_status(self, job: PublishJob, account: Account) -> JobStatus:
        return job.status

douyin_adapter = DouyinAdapter()
