import uuid
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QLineEdit, QTextEdit, QPushButton,
    QFileDialog, QListWidget, QCheckBox, QComboBox,
    QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt

from core.models.content import Content, ContentType, MediaAsset
from core.rules.engine import rule_engine

class EditorView(QWidget):
    """内容创作与平台实时规则自适应预览视图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.media_assets: list[MediaAsset] = []
        self._init_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)

        # ---------------- 左侧：通用创作区 ----------------
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        title_lbl = QLabel("✍️ 内容统一创作成品库")
        title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFFFFF;")

        # 内容类型
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("内容类型:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["image_text", "video", "article", "text"])
        type_layout.addWidget(self.type_combo)

        self.cb_ai = QCheckBox("勾选平台合规「AI 生成内容标识」")
        self.cb_ai.setChecked(True)
        type_layout.addWidget(self.cb_ai)
        type_layout.addStretch()

        # 标题输入
        self.txt_title = QLineEdit()
        self.txt_title.setPlaceholderText("请输入通用大标题（如：2026全平台分发系统自动化最佳实践）")
        self.txt_title.setText("2026自托管全平台内容分发系统：一次编写，全矩阵一键极速分发实测")
        self.txt_title.textChanged.connect(self._update_preview)

        # 正文输入
        self.txt_body = QTextEdit()
        self.txt_body.setPlaceholderText("正文内容（支持 Markdown 排版）...")
        self.txt_body.setPlainText(
            "今天为大家深度评测一款全新的自托管全平台分发系统 OmniPost！\n\n"
            "它采用物理级独立沙盒架构，彻底解决多账号跨平台环境污染难题。\n"
            "支持抖音、小红书、B站、百家号等主流平台，适配规则自动改写。\n\n"
            "欢迎在评论区探讨自动化与风控对抗经验！"
        )
        self.txt_body.textChanged.connect(self._update_preview)

        # 话题标签
        self.txt_tags = QLineEdit()
        self.txt_tags.setPlaceholderText("话题标签，以英文逗号分隔 (例如: 内容分发, 自动化, 效率神器, 独立开发)")
        self.txt_tags.setText("全平台分发, 自动化工具, 效率神器, 独立开发, 科技新趋势, 创作者经济, 玩转数码")
        self.txt_tags.textChanged.connect(self._update_preview)

        # 媒体文件列表
        media_group = QGroupBox("媒体资产（图片或视频）")
        media_layout = QVBoxLayout(media_group)
        self.media_list = QListWidget()

        btn_media_layout = QHBoxLayout()
        self.btn_add_media = QPushButton("📎 添加图片/视频")
        self.btn_add_media.clicked.connect(self._add_media_files)
        self.btn_clear_media = QPushButton("清空素材")
        self.btn_clear_media.clicked.connect(self._clear_media)
        btn_media_layout.addWidget(self.btn_add_media)
        btn_media_layout.addWidget(self.btn_clear_media)

        media_layout.addWidget(self.media_list)
        media_layout.addLayout(btn_media_layout)

        left_layout.addWidget(title_lbl)
        left_layout.addLayout(type_layout)
        left_layout.addWidget(QLabel("通用主标题:"))
        left_layout.addWidget(self.txt_title)
        left_layout.addWidget(QLabel("正文正文 (Markdown):"))
        left_layout.addWidget(self.txt_body)
        left_layout.addWidget(QLabel("话题标签 (Tags):"))
        left_layout.addWidget(self.txt_tags)
        left_layout.addWidget(media_group)

        # ---------------- 右侧：平台改写实时预览区 ----------------
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        preview_lbl = QLabel("⚡ 平台规则自适应渲染预览 (Rule Engine)")
        preview_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #00F5A0;")

        platform_select_layout = QHBoxLayout()
        platform_select_layout.addWidget(QLabel("切换预览目标平台:"))
        self.preview_platform_combo = QComboBox()
        self.preview_platform_combo.addItems(["xiaohongshu", "douyin", "bilibili", "baijiahao", "kuaishou"])
        self.preview_platform_combo.currentTextChanged.connect(self._update_preview)
        platform_select_layout.addWidget(self.preview_platform_combo)
        platform_select_layout.addStretch()

        self.preview_warnings = QLabel("暂无规则改写告警")
        self.preview_warnings.setStyleSheet("color: #FF4D5E; background-color: rgba(255, 77, 94, 0.1); border: 1px solid rgba(255,77,94,0.3); padding: 8px; border-radius: 4px;")
        self.preview_warnings.setWordWrap(True)

        self.preview_title = QLineEdit()
        self.preview_title.setReadOnly(True)
        self.preview_title.setStyleSheet("color: #00F5A0; font-weight: bold;")

        self.preview_body = QTextEdit()
        self.preview_body.setReadOnly(True)

        self.preview_tags = QLabel("渲染标签:")
        self.preview_tags.setStyleSheet("color: #CBD5E1;")

        right_layout.addWidget(preview_lbl)
        right_layout.addLayout(platform_select_layout)
        right_layout.addWidget(QLabel("规则引擎改写提示 / 违规警告:"))
        right_layout.addWidget(self.preview_warnings)
        right_layout.addWidget(QLabel("平台适配后标题:"))
        right_layout.addWidget(self.preview_title)
        right_layout.addWidget(QLabel("平台适配后正文:"))
        right_layout.addWidget(self.preview_body)
        right_layout.addWidget(self.preview_tags)
        right_layout.addStretch()

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 5)
        splitter.setStretchFactor(1, 5)
        main_layout.addWidget(splitter)

        self._update_preview()

    def _add_media_files(self):
        files, _ = QFileDialog.getOpenFileNames(self, "选择素材", "", "Media Files (*.png *.jpg *.jpeg *.mp4 *.mov)")
        for f in files:
            asset = MediaAsset(
                id=uuid.uuid4().hex[:8],
                path=f,
                type="video" if f.endswith((".mp4", ".mov")) else "image"
            )
            self.media_assets.append(asset)
            self.media_list.addItem(f"[{asset.type.upper()}] {f}")
        self._update_preview()

    def _clear_media(self):
        self.media_assets.clear()
        self.media_list.clear()
        self._update_preview()

    def get_current_content(self) -> Content:
        """组装标准内容模型对象"""
        tag_list = [t.strip() for t in self.txt_tags.text().split(",") if t.strip()]
        return Content(
            id=f"cnt_{uuid.uuid4().hex[:10]}",
            type=ContentType(self.type_combo.currentText()),
            title=self.txt_title.text().strip(),
            body=self.txt_body.toPlainText(),
            tags=tag_list,
            media=self.media_assets,
            ai_generated=self.cb_ai.isChecked()
        )

    def _update_preview(self):
        target_platform = self.preview_platform_combo.currentText()
        content = self.get_current_content()

        try:
            rendered = rule_engine.render(content, target_platform)
            self.preview_title.setText(f"{rendered['title']}  ({len(rendered['title'])} 字)")
            self.preview_body.setPlainText(rendered["body"])
            self.preview_tags.setText(f"话题标签 ({len(rendered['tags'])}个): " + "  ".join([f"#{t}" for t in rendered["tags"]]))

            warnings = rendered.get("warnings", [])
            if warnings:
                self.preview_warnings.setText("⚠️ 改写告警提示:\n" + "\n".join([f"• {w}" for w in warnings]))
                self.preview_warnings.show()
            else:
                self.preview_warnings.setText("✅ 完全符合平台规范，无需裁剪")
                self.preview_warnings.setStyleSheet("color: #00F5A0; background-color: rgba(0, 245, 160, 0.1); border: 1px solid rgba(0,245,160,0.3); padding: 8px; border-radius: 4px;")
                self.preview_warnings.show()

        except Exception as e:
            self.preview_warnings.setText(f"❌ 规则校验失败: {str(e)}")
            self.preview_warnings.setStyleSheet("color: #FF4D5E; background-color: rgba(255, 77, 94, 0.1); border: 1px solid rgba(255,77,94,0.3); padding: 8px; border-radius: 4px;")
            self.preview_warnings.show()
