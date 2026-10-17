from pathlib import Path
from typing import Any
import yaml
from loguru import logger

from config.settings import settings
from core.models.content import Content, ContentType

class RuleEngine:
    """各平台内容自适应改写与规则校验引擎"""

    def __init__(self, rules_path: Path | None = None):
        self.rules_path = rules_path or settings.RULES_FILE
        self.rules: dict[str, Any] = self._load_rules()

    def _load_rules(self) -> dict[str, Any]:
        if not self.rules_path.is_file():
            logger.warning(f"规则配置文件不存在: {self.rules_path}，使用空规则库")
            return {}
        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"加载规则文件失败: {e}")
            return {}

    def get_platform_rule(self, platform: str) -> dict[str, Any]:
        rule = self.rules.get(platform)
        if not rule:
            logger.warning(f"未找到平台 {platform} 的专属规则，使用默认宽容规则")
            return {
                "name": platform,
                "max_title_len": 100,
                "max_body_len": 5000,
                "max_tags": 10,
                "supports": ["text", "image_text", "video", "article"]
            }
        return rule

    def render(self, content: Content, platform: str) -> dict[str, Any]:
        """
        按平台规则改写内容。
        原则：截断、拆分、标签裁剪，超出限制给出明确 warning。
        """
        rule = self.get_platform_rule(platform)
        warnings: list[str] = []

        # 1. 支持性校验
        supported_types = rule.get("supports", [])
        if content.type.value not in supported_types:
            raise ValueError(f"平台 [{rule.get('name', platform)}] 不支持内容类型: {content.type.value}，支持列表: {supported_types}")

        # 2. 标题改写与校验
        max_title_len = rule.get("max_title_len", 100)
        rendered_title = content.title.strip()
        if len(rendered_title) > max_title_len:
            warnings.append(f"原标题长 {len(rendered_title)} 字，超过平台上限 {max_title_len} 字，已执行安全裁剪")
            rendered_title = rendered_title[:max_title_len]

        # 3. 正文改写与校验
        max_body_len = rule.get("max_body_len", 5000)
        rendered_body = content.body.strip()
        if len(rendered_body) > max_body_len:
            warnings.append(f"原正文长 {len(rendered_body)} 字，超过平台上限 {max_body_len} 字，已截断保留前 {max_body_len} 字")
            rendered_body = rendered_body[:max_body_len]

        # 4. 话题标签数量裁剪
        max_tags = rule.get("max_tags", 10)
        cleaned_tags = [t.lstrip("#").strip() for t in content.tags if t.strip()]
        if len(cleaned_tags) > max_tags:
            warnings.append(f"话题标签原有 {len(cleaned_tags)} 个，超过上限 {max_tags} 个，已保留前 {max_tags} 个")
            cleaned_tags = cleaned_tags[:max_tags]

        # 5. 媒体资产与封面检查
        media_paths = [m.path for m in content.media if m.exists()]
        if len(media_paths) < len(content.media):
            missing_count = len(content.media) - len(media_paths)
            warnings.append(f"检测到 {missing_count} 个媒体文件在本地不存在，已剔除")

        cover_path = content.cover.path if (content.cover and content.cover.exists()) else None

        # 6. 视频时长检查
        if content.type == ContentType.VIDEO and rule.get("video_max_seconds"):
            max_seconds = rule["video_max_seconds"]
            for m in content.media:
                if m.duration_seconds and m.duration_seconds > max_seconds:
                    warnings.append(f"视频时长 {m.duration_seconds} 秒超过平台限制 {max_seconds} 秒")

        rendered_result = {
            "platform": platform,
            "title": rendered_title,
            "body": rendered_body,
            "tags": cleaned_tags,
            "media_paths": media_paths,
            "cover_path": cover_path,
            "ai_generated": content.ai_generated,
            "schedule_at": content.schedule_at.isoformat() if content.schedule_at else None,
            "warnings": warnings,
        }

        if warnings:
            logger.warning(f"内容发布至 [{platform}] 改写提示:\n - " + "\n - ".join(warnings))
        else:
            logger.info(f"内容发布至 [{platform}] 规则套用完成，无警告")

        return rendered_result

rule_engine = RuleEngine()
