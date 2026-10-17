from pydantic import BaseModel, Field

class AccountFingerprint(BaseModel):
    """账号专属且永久绑定的硬件与浏览器指纹配置 (一次生成，终身锚定)"""
    user_agent: str
    viewport: dict[str, int] = Field(default_factory=lambda: {"width": 1920, "height": 1080})
    device_scale_factor: float = 1.0
    locale: str = "zh-CN"
    timezone_id: str = "Asia/Shanghai"
    webgl_vendor: str = "Google Inc. (NVIDIA)"
    webgl_renderer: str = "ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0, D3D11)"
    canvas_noise_salt: str = "salt_seed_0"

class AccountEnvironment(BaseModel):
    """账号独立运行环境元数据"""
    account_id: str
    platform: str
    profile_dir: str
    proxy_url: str | None = None
    fingerprint: AccountFingerprint
