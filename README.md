# OmniPost - 全平台内容分发系统

> **内容写一次，按各平台规则自动改写，一键分发到抖音、小红书、B站、百家号等主流平台。**
> 核心采用**五维物理级账号独立环境沙盒**与**双后端驱动架构（Patchright + MatrixMedia CLI）**。

---

## 🌟 核心特性

1. **🛡️ 五维物理级账号隔离沙盒 (Anti-Ban & Zero-Leak)**
   - **物理目录硬隔离**：每个账号拥有完全独立的 `data/profiles/{account_id}/`，Cookies、Storage、IndexedDB 杜绝任何跨账号串扰。
   - **静态硬件指纹锚定**：首次初始化时固定生成 User-Agent、视口分辨率、Canvas 噪音盐、时区与语言，**一次生成，终身锁定**，杜绝频繁变动硬件指纹触发平台风控。
   - **专线代理绑定与 WebRTC 泄漏防御**：强制禁用 WebRTC 本地真实 IP 穿透，实现真单账号单 IP 出口。
   - **排他独占运行时锁**：文件级/分布式锁保障同一时刻单账号单进程独占访问，杜绝并发读写破坏 Profile。
   - **Patchright 防检测**：底层抹除 `navigator.webdriver`，拟人打字与鼠标曲线输入。

2. **⚡ 双后端驱动架构 (Dual-Backend)**
   - **Browser 后端 (Patchright)**：直驱无开放 API 平台（抖音、小红书、快手、视频号）。
   - **CLI 后端 (MatrixMedia CLI)**：独立子进程解耦调用（B站、百家号、头条），规避 GPL-2.0 许可证代码污染。
   - **Manual 兜底后端**：未适配平台自动生成预填包并打开发布页。

3. **🎨 顶级暗黑量化桌面终端 (Pure Black & Liquid Glass)**
   - 极致纯黑 `#000000` 底色搭配半透明物理毛玻璃与白金微折射高光。
   - 翡翠霓虹绿 `#00F5A0` 与霓虹绯红 `#FF4D5E` 高定状态指示。
   - 集成“账号隔离沙盒管理”、“内容创作与实时规则改写预览”、“一键矩阵分发与终端监控流”。

---

## 📁 目录结构

```text
omnipost/
├── config/
│   ├── settings.py                  # 全局系统配置 (路径、数据库连接、降级保护)
│   └── platform_rules.yaml          # 各平台标题长度/字数/标签/媒体规则表
├── core/
│   ├── models/                      # 统一数据模型 (Content, PublishJob, Account)
│   ├── rules/                       # 规则解析与内容渲染器 (render engine)
│   └── profiles/                    # 账号物理沙盒与硬件指纹管理中心
├── adapters/
│   ├── base.py                      # PlatformAdapter Protocol 基础定义与错误码
│   ├── registry.py                  # 适配器插件注册中心
│   ├── browser/                     # 浏览器自动化适配器 (抖音, 小红书)
│   ├── cli/                         # 命令行子进程适配器 (B站, 百家号)
│   └── manual/                      # 兜底手动发布包适配器
├── database/
│   ├── models.py                    # SQLAlchemy ORM 持久化表
│   └── session.py                   # 数据库异步会话与容灾自愈
├── tasks/
│   ├── celery_app.py                # Celery 分布式任务引擎
│   ├── dispatcher.py                # 核心任务调度与状态持久化管理器
│   └── publish_tasks.py             # 分布式发布 Worker
├── ui/                              # 桌面客户端界面 (PySide6)
│   ├── main_window.py               # 桌面主视窗
│   ├── styles.py                    # Pure Black & Liquid Glass QSS 样式表
│   └── components/                  # 账号/创作/监控组件
├── tests/                           # 单元测试与冒烟测试
├── docker/
│   └── docker-compose.yml           # PostgreSQL + Redis 本地编排
├── main.py                          # 桌面客户端启动入口
└── requirements.txt
```

---

## 🚀 极速启动与运行

### 1. 运行测试套件
```bash
# 测试账号物理沙盒与排他锁隔离
py tests/test_profile_isolation.py

# 测试全平台规则引擎改写
py tests/test_rule_engine.py
```

### 2. 启动桌面客户端
```bash
py main.py
```
