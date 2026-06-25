# AgentScope 学习路线图

> 版本：AgentScope 2.0  
> 目标：从零基础到能独立构建生产级多智能体应用

---

## 总览

```
阶段 0：前置知识（1-2 天）
    ↓
阶段 1：快速入门（2-3 天）
    ↓
阶段 2：核心概念深入（3-5 天）
    ↓
阶段 3：多智能体协作（3-5 天）
    ↓
阶段 4：生产级部署（3-5 天）
    ↓
阶段 5：高级特性与生态（持续）
```

---

## 阶段 0：前置知识（1-2 天）

### 必备基础

| 知识点 | 掌握程度 | 学习资源 |
|--------|---------|---------|
| **Python 3.11+ 语法** | 熟练掌握 async/await、类型注解、match-case | 官方文档 |
| **LLM 基础概念** | 理解 Prompt、System Prompt、Token、Temperature 等 | OpenAI/Claude 文档 |
| **ReAct 模式** | 理解 Thought → Action → Observation 循环 | [ReAct 论文](https://arxiv.org/abs/2210.03629) |
| **FastAPI 基础** | 了解路由、依赖注入、异步处理 | FastAPI 官方教程 |
| **Docker 基础** | 会写 Dockerfile、运行容器 | Docker 官方文档 |

### 可选但推荐

- **Redis 基础**：了解 key-value 存储、连接池（用于 Agent Service 持久化）
- **MCP（Model Context Protocol）**：理解工具暴露的标准协议
- **A2A（Agent-to-Agent）**：理解 Agent 间通信协议

---

## 阶段 1：快速入门（2-3 天）

### 目标

能运行第一个 AgentScope 程序，理解基本 API。

### 任务清单

- [ ] 安装 Python 3.11+ 环境
- [ ] `pip install agentscope`
- [ ] 获取 LLM API Key（推荐 DashScope 通义千问，也支持 OpenAI/Claude）
- [ ] 运行「Hello AgentScope」基础对话程序
- [ ] 运行「ReAct Agent + 工具调用」程序
- [ ] 理解 `Agent`、`ReActAgent`、`DashScopeChatModel`、`Toolkit` 的基本用法
- [ ] 理解事件系统 `EventType` 和 `reply_stream`

### 关键代码模板（需掌握）

```python
# 1. 基础 Agent 创建
agent = Agent(name=..., system_prompt=..., model=..., toolkit=...)

# 2. 流式对话
async for evt in agent.reply_stream(UserMsg(name, content)):
    ...

# 3. ReAct Agent（带工具）
agent = ReActAgent(name=..., system_prompt=..., model=..., toolkit=Toolkit([...]))
```

### 验证标准

能独立写出：一个可以调用 `Bash` 工具执行 `ls -la` 并返回结果的 ReAct Agent。

---

## 阶段 2：核心概念深入（3-5 天）

### 目标

深入理解 AgentScope 2.0 的每个核心模块，能灵活组合使用。

### 2.1 模型系统（1 天）

- [ ] 理解 `Formatter` 的作用（统一适配不同 LLM API 格式）
- [ ] 掌握至少 2 种模型接入：`DashScopeChatModel` + `OpenAIChatModel`
- [ ] 理解模型故障的优雅回退机制
- [ ] 尝试接入本地模型（Ollama）

### 2.2 工具系统（1-2 天）

- [ ] 熟练使用所有内置工具：`Bash`、`Grep`、`Glob`、`Read`、`Write`、`Edit`
- [ ] 编写第一个自定义工具（函数式注册）
- [ ] 理解工具的并发执行机制
- [ ] 配置工具权限规则（allow/deny paths、risk_level）
- [ ] 理解元工具（Meta-tool）动态调度

### 2.3 记忆系统（0.5 天）

- [ ] 理解 `InMemoryMemory` 的自动管理行为
- [ ] 配置 `RedisSession` 实现跨 Session 持久化
- [ ] 了解 `Mem0LongTermMemory` 长期记忆（注意 2.0 API 变更）

### 2.4 事件系统（0.5 天）

- [ ] 掌握所有 `EventType` 的含义和处理方式
- [ ] 实现一个带进度显示的 CLI 界面
- [ ] 理解如何接入 AG-UI 或自定义前端

### 验证标准

能写出：一个带文件系统权限控制（只允许读写 `/tmp`）的 ReAct Agent，并在调用工具时实时打印「正在调用 xxx 工具」的进度信息。

---

## 阶段 3：多智能体协作（3-5 天）

### 目标

掌握多个 Agent 之间的协作编排，构建复杂工作流。

### 3.1 MsgHub 消息中心（1 天）

- [ ] 理解 MsgHub 的路由机制
- [ ] 实现 Agent 之间的消息广播和定向发送
- [ ] 掌握多模态消息（文本+图片+音频）的传输

### 3.2 协作模式（1-2 天）

| 模式 | 说明 | 实践目标 |
|------|------|---------|
| **顺序协作** | Agent A → Agent B → Agent C | 实现一个「需求分析 → 编码 → 代码审查」流水线 |
| **并行协作** | 多个 Agent 同时处理不同子任务 | 实现一个「同时搜索新闻/论文/代码」的研究助手 |
| **协调者-工作者** | 一个 Coordinator 分配任务给多个 Worker | 实现一个「项目经理 + 前端/后端/测试」开发团队模拟 |
| **人机协作** | Agent 执行中途暂停，等待人类确认 | 实现一个「文件删除前要求确认」的安全 Agent |

### 3.3 实战项目（1-2 天）

选择一个项目完整实现：

**项目 A：智能旅行规划系统**
```
用户输入：计划去京都玩 5 天，预算 1 万元

Agent 协作：
- 信息收集 Agent（搜索景点、酒店、交通）
- 行程规划 Agent（制定每日日程）
- 预算审核 Agent（核算费用合理性）
- 输出：完整的旅行计划文档
```

**项目 B：智能代码审查系统**
```
输入：GitHub PR 链接或代码文件

Agent 协作：
- 语法检查 Agent
- 安全漏洞扫描 Agent
- 最佳实践审查 Agent
- 综合报告生成 Agent
```

**项目 C：多模态内容创作助手**
```
输入：一个主题（如「AI 发展趋势」）

Agent 协作：
- 研究 Agent（搜索资料）
- 文案 Agent（撰写文章）
- 配图建议 Agent（描述需要的图片）
- 排版 Agent（生成 Markdown/HTML）
```

### 验证标准

能独立设计并实现一个包含 3+ Agent 协作的完整系统，能处理工具调用、错误恢复和人类介入。

---

## 阶段 4：生产级部署（3-5 天）

### 目标

将 Agent 应用从本地脚本变为可服务化的生产系统。

### 4.1 Workspace 与安全（1 天）

- [ ] 配置本地 Workspace 的权限规则
- [ ] 使用 Docker 沙箱运行 Agent（构建 Dockerfile）
- [ ] 了解 E2B 云沙箱的使用方式
- [ ] 实现危险操作的拦截和用户确认流程

### 4.2 Agent Service（1-2 天）

- [ ] 使用 `create_app()` 创建 FastAPI 服务
- [ ] 配置 Redis 持久化存储
- [ ] 实现 REST API：`/agent`、`/sessions`、`/chat`
- [ ] 测试 SSE 流式输出
- [ ] 配置 CORS 和 API 认证

### 4.3 可观测性（0.5 天）

- [ ] 开启 OpenTelemetry 全链路追踪
- [ ] 集成 Arize-Phoenix 或 Langfuse 监控平台
- [ ] 配置日志收集和告警

### 4.4 部署方式（1 天）

| 部署方式 | 适用场景 | 学习要点 |
|---------|---------|---------|
| **本地部署** | 开发测试 | `uvicorn.run(app, host="0.0.0.0", port=8000)` |
| **Docker 部署** | 单机生产 | 编写 Dockerfile、docker-compose |
| **Serverless** | 弹性需求 | 阿里云函数计算、AWS Lambda |
| **K8s 集群** | 大规模生产 | Deployment、Service、HPA 配置 |

### 验证标准

能部署：一个运行在 Docker 容器中的 Agent Service，支持多用户 Session 隔离，带 OpenTelemetry 监控，危险操作有确认流程。

---

## 阶段 5：高级特性与生态（持续学习）

### 5.1 MCP 与 A2A 集成

- [ ] 理解 MCP（Model Context Protocol）协议
- [ ] 将现有工具封装为 MCP Server
- [ ] 理解 A2A（Agent-to-Agent）协议
- [ ] 实现跨框架的 Agent 协作（如 AgentScope ↔ AutoGen）

### 5.2 模型微调

- [ ] 了解 AgentScope 内置的模型微调支持
- [ ] 收集 Agent 执行数据作为训练数据
- [ ] 使用 SFT/RLHF 微调专用模型

### 5.3 实时语音

- [ ] 了解 AgentScope 的实时语音能力
- [ ] 集成 ASR（语音识别）和 TTS（语音合成）
- [ ] 构建语音交互 Agent

### 5.4 分布式评估

- [ ] 使用 Ray 分布式框架并行评估 Agent
- [ ] 设计自定义评估指标
- [ ] 运行 ACEBench 等标准测试集

### 5.5 社区贡献

- [ ] 阅读 AgentScope 源码（`agentscope/agent`、`agentscope/tool`、`agentscope/memory`）
- [ ] 提交 Issue 或 PR
- [ ] 在 Discord / 钉钉群参与讨论

---

## 推荐学习资源

### 官方资源

| 资源 | 链接 | 用途 |
|------|------|------|
| 官方文档（英文）| https://docs.agentscope.io/v2 | 主要参考 |
| 官方文档（中文）| https://docs.agentscope.io/zh/v2 | 中文对照 |
| 文档索引 | https://docs.agentscope.io/llms.txt | 快速发现所有页面 |
| GitHub 仓库 | https://github.com/agentscope-ai/agentscope | 源码学习 |
| Runtime 仓库 | https://github.com/agentscope-ai/agentscope-runtime | 服务化部署参考 |

### 第三方教程

| 资源 | 说明 |
|------|------|
| CSDN 系列教程 | 搜索「AgentScope 框架详解」|
| 飞书学习指南 | 搜索「AgentScope学习指南」|
| BibiGPT 视频总结 | 搜索「MultiAgent应用开发实战 AgentScope」|

### 相关论文

- ReAct: Synergizing Reasoning and Acting in Language Models
- AgentScope 框架设计论文（见 GitHub Publications）

---

## 学习检查清单

完成以下所有项目，即可认为掌握了 AgentScope 2.0：

### 基础能力
- [ ] 能独立安装和配置 AgentScope 2.0
- [ ] 能接入至少 2 种 LLM（如通义千问 + OpenAI）
- [ ] 能编写自定义工具并注册到 Toolkit
- [ ] 能理解并处理所有 EventType

### 进阶能力
- [ ] 能实现 3+ Agent 的协作系统
- [ ] 能配置工具权限和安全沙箱
- [ ] 能实现人类介入（Human-in-the-loop）
- [ ] 能使用 Redis 实现 Session 持久化

### 生产能力
- [ ] 能部署 Agent Service（REST + SSE）
- [ ] 能配置 Docker 沙箱运行环境
- [ ] 能接入 OpenTelemetry 监控
- [ ] 能在 K8s 上部署多副本 Agent Service

---

## 时间规划建议

| 学习者类型 | 总时长 | 每日投入 | 达成目标 |
|-----------|--------|---------|---------|
| **全职学习** | 2-3 周 | 6-8 小时/天 | 阶段 4 完成，能部署生产服务 |
| **兼职学习** | 1.5-2 个月 | 2-3 小时/天 | 阶段 3 完成，能构建多 Agent 协作系统 |
| **周末学习** | 3-4 个月 | 周末集中 | 阶段 2 完成，能独立使用核心 API |

---

## 版本注意

AgentScope 2.0 于 **2026 年 5 月** 发布，与 1.0 API 完全不兼容。学习时务必确认：

- ✅ 安装的是 `agentscope>=2.0`
- ✅ 参考的是 2.0 文档（URL 含 `/v2`）
- ✅ GitHub 分支是 `main`

1.0 的 `DialogAgent`、`SequentialPipeline`、`agentscope.init()` 等 API 在 2.0 中已移除，不要混淆。
