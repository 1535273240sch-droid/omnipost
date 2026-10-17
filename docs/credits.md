# 开放源代码引用声明与致谢 (Credits & Licenses)

本项目严格遵守知识产权与开源许可证合规要求，以下为参考与集成的相关开源项目声明：

---

### 1. [social-auto-upload](https://github.com/dreammis/social-auto-upload)
- **许可证**：MIT License
- **引用说明**：参考其图文上传（`upload-note`）的字段约定与浏览器自动化上传流程设计。

### 2. [CreatorHub](https://github.com/3441293738/creatorhub)
- **许可证**：页面未声明明确开源许可证。
- **引用说明**：仅借鉴其“独立 Profile 隔离、代理池绑定与任务风控调度”的设计思想。本项目所有代码均为全新独立自主编写（Clean-room Reimplementation），不复制其任何源代码。

### 3. [MatrixMedia](https://github.com/hanliang97/MatrixMedia)
- **许可证**：GPL-2.0 License
- **引用说明**：本项目不包含 MatrixMedia 的源码。对于 B站、百家号等平台的发布支持，本项目通过**外部独立命令行子进程（CLI Subprocess）**的标准输入输出（stdin/stdout/exit code）进行松耦合调用，确保 GPL 许可证不与本项目核心代码产生代码层面的静态合并或派生污染。
