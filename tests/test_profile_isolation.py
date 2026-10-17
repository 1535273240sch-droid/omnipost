import asyncio
import sys
from pathlib import Path

# 设置标准输出编码为 UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 加入项目根目录
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.profiles.manager import profile_manager

async def test_account_isolation():
    print("=== [测试 1] 验证账号物理沙盒目录隔离 ===")
    env_douyin = profile_manager.get_environment("acc_douyin_test", "douyin")
    env_xhs = profile_manager.get_environment("acc_xhs_test", "xiaohongshu")

    assert env_douyin.profile_dir != env_xhs.profile_dir, "不同账号的物理沙盒目录绝对不能相同！"
    assert Path(env_douyin.profile_dir).is_dir(), "抖音沙盒目录必须真实存在于磁盘"
    assert Path(env_xhs.profile_dir).is_dir(), "小红书沙盒目录必须真实存在于磁盘"
    print(f"[OK] 账号 A 物理目录: {env_douyin.profile_dir}")
    print(f"[OK] 账号 B 物理目录: {env_xhs.profile_dir}")

    print("\n=== [测试 2] 验证硬件指纹静态锚定 (一次生成，终身固定) ===")
    fp1 = profile_manager.get_or_create_fingerprint("acc_douyin_test")
    fp2 = profile_manager.get_or_create_fingerprint("acc_douyin_test")
    assert fp1.user_agent == fp2.user_agent, "同一账号两次获取指纹，UA 必须完全一致！"
    assert fp1.canvas_noise_salt == fp2.canvas_noise_salt, "同一账号的 Canvas 盐值必须永久固化！"
    print(f"[OK] 固化 User-Agent: {fp1.user_agent}")
    print(f"[OK] 固化 Canvas 噪声盐: {fp1.canvas_noise_salt}")

    print("\n=== [测试 3] 验证排他性独占锁 (防止多进程踩踏破坏 Profile) ===")
    async with profile_manager.lock_account("acc_douyin_test") as lock_acquired:
        assert lock_acquired is True
        print("[OK] 进程 A 成功获取账号独占锁")

        # 尝试并发获取锁（预期超时拒绝）
        try:
            async with profile_manager.lock_account("acc_douyin_test", timeout=1.0):
                assert False, "正在被占用的账号绝不能被重复加锁！"
        except RuntimeError:
            print("[OK] 进程 B 尝试并发读写同一账号 Profile 被成功拦截并保护 (排他锁生效)")

        # 验证不同账号可以并行持有锁（互不阻塞）
        async with profile_manager.lock_account("acc_xhs_test", timeout=1.0) as lock_b:
            assert lock_b is True
            print("[OK] 账号 B 与账号 A 物理隔离，互不阻塞，并行成功")

    print("\n[SUCCESS] 全部账号物理隔离与风控防御测试通过！")

if __name__ == "__main__":
    asyncio.run(test_account_isolation())
