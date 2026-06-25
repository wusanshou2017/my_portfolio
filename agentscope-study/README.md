# AgentScope 框架完全指南

> 调研时间：2026-06-03  
> 版本：AgentScope 2.0（2026-05 发布）  
> 官方文档：https://doc.agentscope.io/  
> GitHub：https://github.com/agentscope-ai/agentscope

---

## 一、框架简介

**AgentScope** 是阿里巴巴通义实验室开源的面向生产级的多智能体（Multi-Agent）应用开发框架。最新 2.0 版本于 2026 年 5 月发布，与 1.0 相比在核心抽象、API 和架构上均有**破坏性变更**，属于一次彻底的重构。

### 设计哲学

AgentScope 2.0 的设计理念是：**充分发挥模型的推理与工具调用能力，而不是用严格的提示词和固化的编排方式来束缚它们。**

### 三大核心优势

| 优势 | 说明 |
|------|------|
| **Simple（简单易用）** | 内置 ReAct Agent、工具集、人工介入、记忆、规划、实时语音、评估和模型微调，5 分钟即可上手 |
| **Extensible（高度可扩展）** | 丰富的生态集成（工具、记忆、可观测性）；内置 MCP 和 A2A 支持；MsgHub 实现灵活的多智能体编排 |
| **Production-ready（生产就绪）** | 支持本地、Serverless 云端、K8s 集群部署，内置 OpenTelemetry 可观测性支持 |

---

## 二、2.0 的重大改进（对比 1.0）

AgentScope 2.0 是一次彻底的重写，以下是关键变化：

| 特性 | 2.0 改进 |
|------|---------|
| **事件系统（Event System）** | 智能体每一步操作（文本、思考、工具调用、结果）都以类型化流式事件暴露，可渲染丰富 UI，直接接入 AG-UI 或 A2A |
| **执行安全（Execution Security）** | 危险工具调用可被拦截或暂缓审查，不受信任代码可在沙箱中运行 |
| **人工介入（Human-in-the-loop）** | 用户可在运行中途确认或修改工具参数，敏感操作可转交自定义后端处理，Agent 精确恢复执行 |
| **更高效率** | 多工具并发执行、长对话自动保持在上下文窗口内、超大工具输出自动截断、模型故障优雅回退 |
| **Workspace 系统** | 修改一行代码即可将 Agent 从本地迁移到 Docker 或 E2B 沙箱，工作目录、MCP 客户端按用户/Agent/会话隔离 |
| **Agent Service** | 通过 REST + SSE 托管任意 Agent，支持多租户、多 Session 并发、持久化会话、定时任务 |

> ⚠️ **注意**：1.0 的 `agentscope.init()`、`DialogAgent`、`SequentialPipeline` 等 API 在 2.0 中已**完全移除**，需要使用新 API。

---

## 三、环境准备与安装

### 3.1 系统要求

- **Python 3.11 或更高版本**（3.9/3.10 已不支持 2.0）

### 3.2 安装方式

```bash
# 方式一：从 PyPI 安装（推荐）
pip install agentscope

# 或使用 uv
uv pip install agentscope

# 方式二：从源码安装（适合深入学习）
git clone -b main https://github.com/agentscope-ai/agentscope.git
cd agentscope
pip install -e .
```

### 3.3 可选依赖

```bash
# Docker 沙箱支持
pip install docker

# E2B 云沙箱支持
pip install e2b

# Redis 持久化（Agent Service）
pip install redis
```

---

## 四、核心概念详解

### 4.1 Agent（智能体）

Agent 是框架的基本执行单元。2.0 的核心 Agent 类包括：

- **`Agent`**：基础智能体，可直接使用工具
- **`ReActAgent`**：支持推理-行动循环的智能体

```python
from agentscope.agent import Agent, ReActAgent
from agentscope.model import DashScopeChatModel
from agentscope.tool import Toolkit, Bash, Grep, Glob, Read, Write, Edit

agent = Agent(
    name="Friday",
    system_prompt="You're a helpful assistant named Friday.",
    model=DashScopeChatModel(
        credential=DashScopeCredential(api_key=os.environ["DASHSCOPE_API_KEY"]),
        model="qwen3.6-plus",
    ),
    toolkit=Toolkit(
        tools=[Bash(), Grep(), Glob(), Read(), Write(), Edit()]
    ),
)
```

### 4.2 Model（模型接口）

2.0 通过 `Formatter` 统一适配不同 LLM 提供商的 API 格式：

| 模型类 | 说明 |
|--------|------|
| `DashScopeChatModel` | 阿里云 DashScope（通义千问系列）|
| `OpenAIChatModel` | OpenAI 及兼容 API |
| `AnthropicChatModel` | Claude 系列 |
| `GeminiChatModel` | Google Gemini |
| `OllamaChatModel` | Ollama 本地模型 |
| `DeepSeekChatModel` | DeepSeek |
| `GLMChatModel` | 智谱 GLM |

对应的 `Formatter` 会自动根据 Model 类型选择，通常无需手动配置。

### 4.3 Tool & Toolkit（工具系统）

工具是 Agent 与外部世界交互的方式：

```python
from agentscope.tool import Toolkit, execute_python_code

# 内置工具
from agentscope.tool import Bash, Grep, Glob, Read, Write, Edit

# 自定义工具（函数式注册）
def search_web(query: str) -> str:
    """搜索网络信息"""
    # 实现搜索逻辑
    return result

toolkit = Toolkit()
toolkit.register_tool_function(execute_python_code)
toolkit.register_tool_function(search_web)
```

2.0 支持：
- 工具分组管理
- 元工具动态调度
- **并发执行**（多工具同时调用）
- **权限控制**（危险操作可拦截或要求确认）

### 4.4 Memory（记忆系统）

| 类型 | 类名 | 说明 |
|------|------|------|
| 短期记忆 | `InMemoryMemory` | 内存存储，默认使用，跨 Session 丢失 |
| 长期记忆 | `Mem0LongTermMemory` | 基于 Mem0 的长期记忆（需适配 2.0 API）|
| 持久化 | `RedisSession` | 通过 Redis 实现 Session 状态持久化 |

`ReActAgent` 自动管理记忆：
- 自动添加用户消息到记忆
- 自动添加工具调用和结果到记忆
- 自动添加 Agent 响应到记忆
- 推理时自动读取记忆作为上下文

### 4.5 Event（事件系统）

2.0 最核心的新特性，所有 Agent 行为都以类型化事件流暴露：

```python
from agentscope.event import EventType

async for evt in agent.reply_stream(UserMsg("Tony", "Hi, Friday!")):
    match evt.type:
        case EventType.REPLY_START:
            print("开始回复...")
        case EventType.MODEL_CALL_START:
            print("调用模型...")
        case EventType.TEXT_BLOCK_START:
            print("文本块开始")
        case EventType.TEXT_BLOCK_DELTA:
            print(evt.delta, end="")  # 流式输出
        case EventType.TEXT_BLOCK_END:
            print("文本块结束")
        case EventType.TOOL_CALL_START:
            print(f"调用工具: {evt.tool_name}")
        case EventType.TOOL_CALL_RESULT:
            print(f"工具结果: {evt.result}")
```

事件类型覆盖：回复开始/结束、模型调用、文本块、思考过程、工具调用、工具结果、错误等。

### 4.6 Workspace（工作区）

Workspace 是 2.0 引入的执行环境抽象：

| 后端 | 说明 |
|------|------|
| **本地** | 默认，直接在宿主机执行 |
| **Docker** | 容器化隔离，需构建镜像 |
| **E2B** | 云端沙箱，需配置 API Key 和模板 ID |

```python
# 只需修改一行即可切换执行环境
from agentscope.workspace import DockerWorkspace, E2BWorkspace

# 权限配置示例（JSON 配置）
permissions = {
    "file_read": {
        "allow_paths": ["/tmp/**"],
        "deny_paths": ["/etc/**", "/sys/**"]
    },
    "command_exec": {
        "allowed_commands": ["ls", "cat", "grep"],
        "risk_level": "user_confirm"
    }
}
```

---

## 五、快速上手实战

### 5.1 Hello AgentScope（基础对话）

```python
import os, asyncio
from agentscope.agent import Agent
from agentscope.model import DashScopeChatModel
from agentscope.credential import DashScopeCredential
from agentscope.message import UserMsg
from agentscope.event import EventType

async def main():
    agent = Agent(
        name="Friday",
        system_prompt="你是一个乐于助人的 AI 助手。",
        model=DashScopeChatModel(
            credential=DashScopeCredential(
                api_key=os.environ["DASHSCOPE_API_KEY"]
            ),
            model="qwen3.6-plus",
        ),
    )

    async for evt in agent.reply_stream(UserMsg("user", "你好！请介绍一下 AgentScope")):
        if evt.type == EventType.TEXT_BLOCK_DELTA:
            print(evt.delta, end="", flush=True)

asyncio.run(main())
```

### 5.2 ReAct Agent（工具调用）

```python
import os, asyncio
from agentscope.agent import ReActAgent
from agentscope.model import DashScopeChatModel
from agentscope.credential import DashScopeCredential
from agentscope.tool import Toolkit, Bash, Read, Write
from agentscope.message import UserMsg
from agentscope.event import EventType

async def main():
    agent = ReActAgent(
        name="编程助手",
        system_prompt="你是一个编程专家，可以帮助用户编写和调试代码。",
        model=DashScopeChatModel(
            credential=DashScopeCredential(
                api_key=os.environ["DASHSCOPE_API_KEY"]
            ),
            model="qwen3.6-plus",
        ),
        toolkit=Toolkit(tools=[Bash(), Read(), Write()]),
    )

    async for evt in agent.reply_stream(
        UserMsg("user", "写一个 Python 脚本计算斐波那契数列前 20 项，并保存到 fib.py")
    ):
        match evt.type:
            case EventType.TEXT_BLOCK_DELTA:
                print(evt.delta, end="")
            case EventType.TOOL_CALL_START:
                print(f"\n[工具调用: {evt.tool_name}]")
            case EventType.TOOL_CALL_RESULT:
                print(f"[工具结果: {evt.result[:200]}...]")

asyncio.run(main())
```

### 5.3 Agent Service（服务化部署）

```python
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from agentscope.app import create_app
from agentscope.app.storage import RedisStorage

# 生产环境使用 Redis
storage = RedisStorage(host="localhost", port=6379, db=0)
app = create_app(storage=storage)

# 启动服务
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

2.0 Agent Service 的 REST API 结构：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/agent/` | GET | 列出所有 Agent |
| `/agent/` | POST | 创建 Agent |
| `/sessions/` | POST | 创建 Session |
| `/chat/` | POST | 流式对话（SSE）|

---

## 六、与其他框架对比

| 对比维度 | AgentScope 2.0 | LangGraph | AutoGen | CrewAI |
|---------|---------------|-----------|---------|--------|
| 编程模型 | 纯 Python，简洁直观 | 图结构，需理解节点边 | 对话驱动，配置较复杂 | 角色分工，简单任务分发 |
| 事件流 | ✅ 原生类型化事件流 | ❌ 需自定义 | ⚠️ 有限支持 | ❌ |
| 实时介入 | ✅ 原生支持中断+恢复 | ❌ 需自定义 | ⚠️ 有限支持 | ❌ |
| 工具并发 | ✅ 内置并发执行 | 基础工具调用 | 代码生成一体化 | 基础函数调用 |
| 执行安全 | ✅ 沙箱+权限控制 | ❌ | 基础隔离 | ❌ |
| 服务化部署 | ✅ REST+SSE 原生 | ❌ | 复杂配置 | ❌ |
| 分布式 | ✅ Actor 模型 | ❌ | 需手动配置 | ❌ |
| MCP/A2A | ✅ 内置支持 | ❌ | ⚠️ 需扩展 | ❌ |
| 多模态 | ✅ 原生支持 | 需扩展 | 仅文本 | 不支持 |

---

## 七、相关资源

| 资源 | 链接 |
|------|------|
| 官方文档 | https://doc.agentscope.io/ |
| 2.0 文档（英文）| https://docs.agentscope.io/v2 |
| 2.0 文档（中文）| https://docs.agentscope.io/zh/v2 |
| GitHub（Python）| https://github.com/agentscope-ai/agentscope |
| GitHub（Java）| https://github.com/agentscope-ai/agentscope-java |
| GitHub（Runtime）| https://github.com/agentscope-ai/agentscope-runtime |
| 文档索引（llms.txt）| https://docs.agentscope.io/llms.txt |

---

## 八、常见问题

**Q: AgentScope 1.0 和 2.0 能共存吗？**
A: 不能。2.0 是破坏性变更，API 完全不兼容。1.0 项目需要重写迁移。

**Q: 必须使用 DashScope（通义千问）吗？**
A: 不是。2.0 支持 OpenAI、Claude、Gemini、DeepSeek、GLM、Ollama 等 17+ 提供商，只需更换对应的 Model 类。

**Q: Web UI 支持 2.0 吗？**
A: 目前 `starter_webui` 只支持 1.0 的 `/process` 端点，不兼容 2.0 的 `/chat` 等端点。需要等待官方更新或自行适配。

**Q: 沙箱是必需的吗？**
A: 不是。本地执行是默认模式。沙箱只在需要隔离不可信代码时使用。
