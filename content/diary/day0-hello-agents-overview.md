---
title: hello-agent 学习第0天：Hello-Agents 教程概览与学习规划
date: 2026-05-08
tags: [AI, LLM, Python, Agent, HelloAgents, LangChain]
description: 了解 Datawhale Hello-Agents 教程的整体结构，明确第4章（经典范式）、第7章（自建框架）、第9章（上下文工程）的学习重点，并与 LangChain 框架对比。
---
## 了解 Hello-Agents 教程

今天是学习第0天，先了解我们要学什么。

Hello-Agents 是 Datawhale 社区出品的**系统性智能体学习教程**，从零开始一步步构建 AI Native Agent。教程共 16 章，分五个部分：

```
第一部分：基础篇（1-3章）    智能体概念、发展史、LLM 基础
第二部分：单体篇（4-7章）    经典范式、低代码平台、框架实践、自建框架
第三部分：高级篇（8-12章）   记忆与检索、上下文工程、通信协议、RL、评估
第四部分：实战篇（13-15章）  智能旅行助手、深度研究、赛博小镇
第五部分：展望篇（16章）     毕业设计
```

我们的学习重点在 **第4章、第7章、第9章**。

---

## 第4章：智能体经典范式构建

这一章从零开始实现了三种经典的智能体范式，没有使用任何框架，直接用 OpenAI SDK + Prompt 工程构建。

### 三种范式

```
ReAct：         思考 → 行动 → 观察 → 思考 → 行动 → 观察 → ...
Plan-and-Solve：先规划（一次性）→ 逐步执行
Reflection：    生成 → 自我反思 → 修正 → 再反思 → ...
```

### 4.1 ReAct（Reasoning and Acting）

核心思想：将**推理**与**行动**显式结合，形成"思考-行动-观察"循环。

```
用户："旧金山的天气怎么样？"

Thought: 用户想知道旧金山的天气，我需要查询天气工具。
Action: get_weather(city="San Francisco")
Observation: "It's always sunny in San Francisco!"
Thought: 我得到了查询结果，可以回答用户了。
Final: 旧金山的天气是晴朗的！
```

关键实现要点：
- 通过 Prompt 约束 LLM 输出格式（`Thought: ...`、`Action: ...`、`Observation: ...`、`Final: ...`）
- 循环解析 LLM 输出，遇到 `Action:` 就执行工具，遇到 `Final:` 就结束
- 每步把结果追加到消息历史中，形成不断增长的上下文

代码结构（基于 OpenAI SDK，无框架）：
```python
while True:
    response = llm_client.think(messages)
    if "Final:" in response:
        print(parse_final(response))
        break
    elif "Action:" in response:
        action, args = parse_action(response)
        result = execute_tool(action, args)
        messages.append({"role": "user", "content": f"Observation: {result}"})
```

### 4.2 Plan-and-Solve

"三思而后行" —— 先全部规划好，再逐步执行。

```
Planner（规划器）:
  问题 → 先拆成步骤列表 ["算周一", "算周二", "算周三", "算总和"]

Executor（执行器）:
  步骤1: 算周一 → 15个（结果累加进 history）
  步骤2: 算周二 → 30个（看到上一步结果）
  步骤3: 算周三 → 25个（看到前两步结果）
  步骤4: 算总和 → 70个（最终答案）
```

代码同样是纯 Prompt + 循环，不依赖任何框架。

### 4.3 Reflection

赋予智能体"自我反思"能力。

```
生成阶段: AI 生成代码
反思阶段: AI 检查代码问题 → 给出改进建议
修正阶段: AI 根据建议修改代码
重复: 反思 → 修正 → 反思 → 修正 → 直到满意
```

通过双系统 Prompt（生成器 + 评判者）实现。

### 本章的定位

**"为什么不用框架？"**——市面上的框架（LangChain 等）把很多东西封装了，你用了框架就看不到底层的实现细节。这一章的目的就是让你亲手实现这些范式，真正理解其设计原理，从框架的"使用者"变成"构建者"。

---

## 第7章：构建你的 Agent 框架

第4章写的是一个个独立的脚本，第7章则把这些范式**系统化为一个可复用的框架**——HelloAgents。

### 为什么需要自建框架？

| 已有框架的问题 | HelloAgents 的定位 |
|---|---|
| 过度抽象，学习曲线陡峭 | 轻量级，核心代码按章节组织，易于理解 |
| API 变更频繁，维护成本高 | 基于 OpenAI 标准 API，稳定可靠 |
| 黑盒化，难以深度定制 | 完全开源，每行代码都可控 |
| 携带大量依赖，体积庞大 | 极简依赖，只依赖必要库 |

### 框架架构

```
hello_agents/
├── core/           # 核心框架层
│   ├── agent.py    # Agent 抽象基类
│   ├── llm.py      # LLM 统一接口
│   ├── message.py  # 消息系统
│   └── config.py   # 配置管理
├── agents/         # Agent 实现层
│   ├── simple_agent.py
│   ├── react_agent.py
│   ├── reflection_agent.py
│   └── plan_solve_agent.py
└── tools/          # 工具系统层
    ├── base.py         # 工具基类
    ├── registry.py     # 工具注册机制
    └── builtin/        # 内置工具集
```

### 核心理念

**"万物皆为工具"**——除了核心 Agent 类，Memory、RAG、MCP 等模块都被统一抽象为"工具"。这样消除了不必要的抽象层，学习者回归到最直观的"智能体调用工具"的核心逻辑。

### 框架化的好处

第4章的实现是"硬编码"的（每个范式写一遍完整的循环），第7章的框架化之后：

- **Agent 基类**定义了通用接口（`run()`、`step()`），子类只需实现核心逻辑
- **工具系统**提供注册机制，Agent 自动发现可用工具
- 可以直接用 `pip install hello-agents` 安装体验，也可以跟着教程一步步实现

---

## 第9章：上下文工程

这一章从 **Prompt Engineering** 演进到 **Context Engineering**——不仅关注"提示怎么写的"，更关注"整个上下文窗口里该放什么信息"。

### 为什么上下文工程重要？

**上下文腐蚀（Context Rot）**：随着上下文窗口中的 tokens 增加，模型准确回忆信息的能力反而下降。

```
信息检索精度
  │
  │  ████████████████████
  │                    ████
  │                        ██████
  │                              ████████
  └─────────────────────────────────────→ 上下文长度
  短上下文（高精度）        长上下文（精度下降）
```

每新增一个 token 都消耗"注意力预算"，必须精挑细选哪些 tokens 应该进入上下文。

### GSSC 流水线

教程中实现的 **ContextBuilder** 核心流程：

```
Gather（收集）→ Select（筛选）→ Structure（结构化）→ Compress（压缩）
```

- **Gather**：从多个来源收集信息（记忆、工具返回、文件等）
- **Select**：根据当前任务筛选最相关的信息
- **Structure**：用 XML/Markdown 组织成结构化格式
- **Compress**：压缩、摘要，减少 token 占用

### 配套工具

- **NoteTool**：结构化笔记工具，支持智能体进行持久化记忆管理
- **TerminalTool**：终端工具，支持文件系统操作和即时上下文检索

### 实战案例

一个"代码库维护助手"，结合了 ContextBuilder、NoteTool、TerminalTool，展示了如何在长时程任务中持续管理上下文。

---

## 与 LangChain 对比

| 维度 | Hello-Agents（本教程） | LangChain |
|---|---|---|
| 定位 | 学习型框架，理解原理 | 生产型框架，快速开发 |
| 依赖 | 极简（只依赖 openai SDK） | 庞大（大量子包和第三方依赖） |
| 学习曲线 | 平缓，代码量少，易于阅读 | 陡峭，需要理解大量抽象概念 |
| 流式支持 | 基础（基于 OpenAI SDK 的 stream） | 完善（内置 Agent 流式、三种 stream mode） |
| 工具系统 | 统一的 Tool 基类 + 注册机制 | 丰富的内置工具 + 集成 |
| 上下文工程 | 内置 ContextBuilder（GSSC 流水线） | 需要手动管理或使用第三方 |
| 多 Agent 支持 | 基础（后续章节扩展） | 完善（LangGraph、子图等） |
| 适用场景 | **学习理解 Agent 原理** | **快速构建生产级应用** |

### 核心区别一句话

- **Hello-Agents** 教你"Agent 是什么、为什么这么设计"，代码少、看得懂
- **LangChain** 帮你"快速开发 Agent 应用"，功能多、开箱即用

### 学习路径建议

```
先学 Hello-Agents（理解原理）
    ↓
再用 LangChain（上手开发）
    ↓
两者都懂了，可以自己造轮子
```

---

## 总结

| 章节 | 核心内容 | 学完之后能做什么 |
|---|---|---|
| 第4章 | ReAct、Plan-and-Solve、Reflection 三种范式 | 理解 Agent 内部工作机制，能自己写 Agent |
| 第7章 | HelloAgents 框架设计（Agent 基类、工具系统） | 能设计自己的 Agent 框架，理解抽象与复用 |
| 第9章 | 上下文工程（GSSC 流水线、NoteTool、TerminalTool） | 能管理长时程任务的上下文，提升 Agent 稳定性 |
| LangChain 对比 | 与行业主流框架的差异化对比 | 明确什么时候该用什么工具 |
