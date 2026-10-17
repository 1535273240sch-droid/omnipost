import sys
from pathlib import Path

# 设置标准输出编码为 UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.models.content import Content, ContentType
from core.rules.engine import rule_engine

def test_rules():
    print("=== [测试 1] 校验小红书规则改写 (标题上限20字，标签上限10个) ===")
    long_content = Content(
        id="cnt_test_01",
        type=ContentType.IMAGE_TEXT,
        title="这是一个超过二十个字的小红书超长标题测试示例文字看看是否会被截断",
        body="这是测试小红书正文内容，分享科技好物与自媒体效率提升技巧。",
        tags=["标签1", "标签2", "标签3", "标签4", "标签5", "标签6", "标签7", "标签8", "标签9", "标签10", "多余标签11", "多余标签12"]
    )

    rendered_xhs = rule_engine.render(long_content, "xiaohongshu")
    assert len(rendered_xhs["title"]) <= 20, f"小红书标题必须截断到 20 字以内，实际: {len(rendered_xhs['title'])}"
    assert len(rendered_xhs["tags"]) <= 10, f"小红书标签必须截断到 10 个以内，实际: {len(rendered_xhs['tags'])}"
    assert len(rendered_xhs["warnings"]) > 0, "必须生成改写警告信息供用户核对"
    print(f"[OK] 渲染后标题: {rendered_xhs['title']}")
    print(f"[OK] 渲染后标签数: {len(rendered_xhs['tags'])}")
    print(f"[OK] 改写警告: {rendered_xhs['warnings']}")

    print("\n=== [测试 2] 校验不支持类型阻断 ===")
    article_content = Content(
        id="cnt_test_02",
        type=ContentType.ARTICLE,
        title="一篇纯长文章",
        body="长篇纯文本文章内容...",
    )
    try:
        rule_engine.render(article_content, "douyin")
        assert False, "抖音不支持纯长文章 (article)，预期抛出拒绝异常"
    except ValueError as e:
        print(f"[OK] 成功拦截不支持的内容类型: {e}")

    print("\n[SUCCESS] 全部规则引擎自适应测试通过！")

if __name__ == "__main__":
    test_rules()
