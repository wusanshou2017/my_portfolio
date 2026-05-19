---
title: hello-agent 学习第4天：工具系统与 ToolExecutor
date: 2026-05-08
tags: [AI, LLM, Python, Agent, Tool, SerpApi]
description: 学习了 tools.py 中的搜索工具和 ToolExecutor 工具注册框架，理解了 Agent 工具调用的完整原理：LLM 是决策者，本地解释器是执行者。
---
## 工具调用的核心问题：谁在调用工具？

今天看了 [tools.py](file:///f:\workspace\my_portfolio\practice\chapter4\tools.py)，搞清楚了一个关键问题：**工具是谁在调用的？**

答案是：**本地 Python 解释器在调用，LLM 只负责决定调什么。**

LLM（运行在云端）自己不能执行任何代码，它只输出文本。整个工具调用的流程：

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  LLM (云端)  │         │ 本地 Python   │         │  SerpApi     │
│              │         │  解释器       │         │  (云端)      │
└──────┬───────┘         └──────┬───────┘         └──────┬──────┘
       │                        │                        │
       │  "Action: Search       │                        │
       │   ['英伟达GPU']"       │                        │
       │───────────────────────→│  ① 本地解析文本         │
       │                        │                        │
       │                        │  ② getTool("Search")   │
       │                        │  → 拿到 search() 函数  │
       │                        │                        │
       │                        │  ③ search("英伟达GPU") │
       │                        │───────────────────────→│
       │                        │                        │
       │                        │  ← 返回搜索结果         │
       │                        │                        │
       │  "Observation: xxx"    │  ④ 拼成观察文本         │
       │←───────────────────────│     再发给 LLM          │
       │                        │                        │
       │  LLM 继续思考...       │                        │
```

一句话总结：**LLM 出脑，本地代码出手。**

## tools.py 的结构

这个文件包含两个部分：

```
tools.py
├── search()          ← SerpApi 搜索工具（第7-44行）
└── ToolExecutor      ← 工具注册框架（第53-95行）
    ├── registerTool(name, description, func)
    ├── getTool(name)
    └── getAvailableTools()
```

## 搜索工具：search()

基于 SerpApi 的 Google 搜索封装。它的**智能解析**按优先级提取最有价值的信息：

```
SerpApi 返回原始 JSON
        │
        ▼ 按优先级解析：
   ┌─────────────────────────┐
   │ 1. answer_box_list      │  ← Google 直接答案列表（最高优先）
   │ 2. answer_box["answer"] │  ← Google 精选摘要
   │ 3. knowledge_graph      │  ← 知识图谱描述
   │ 4. organic_results[:3]  │  ← 前3条搜索结果摘要
   │ 5. "没找到"              │  ← 兜底返回
   └─────────────────────────┘
```

这种分层解析的设计很实用——不是简单返回原始 JSON，而是**尽量给 LLM 最精炼的信息**，减少无用的 token 消耗。

## ToolExecutor：工具注册框架

一个迷你版的工具管理系统，核心就是一个 dict：

```python
self.tools = {
    "Search": {
        "description": "一个网页搜索引擎...",
        "func": <search 函数对象>
    }
}
```

三个方法：

| 方法 | 作用 | 返回值 |
|---|---|---|
| `registerTool(name, desc, func)` | 注册工具到 dict | None |
| `getTool(name)` | 按 name 取函数对象 | callable 或 None |
| `getAvailableTools()` | 格式化输出工具列表 | 字符串（给 LLM 看的） |

## 工具在 Agent 中的角色

以 ReAct 为例，完整的调用链：

```
① Agent 把工具描述放进 Prompt
   system_prompt = f"你可以使用以下工具：\n{toolExecutor.getAvailableTools()}"
                                         ↓
   "你可以使用以下工具：
    - Search: 一个网页搜索引擎..."

② LLM 返回 Action
   "Thought: 我需要搜索英伟达最新GPU
    Action: Search['英伟达最新GPU型号']"

③ 本地代码解析 Action
   tool_name = "Search"    ← 正则提取
   tool_args = "英伟达最新GPU型号"

④ 本地代码执行工具
   func = toolExecutor.getTool("Search")  # 拿到 search 函数
   result = func("英伟达最新GPU型号")      # 本地 Python 调用

⑤ 把结果拼成 Observation 发给 LLM
   messages.append("Observation: RTX 5090是英伟达最新旗舰...")

⑥ LLM 继续，给出 Final Answer
```

## 与 LangChain 工具系统对比

| | tools.py（Hello-Agents） | LangChain |
|---|---|---|
| 定义工具 | `registerTool(name, desc, func)` | `@tool` 装饰器 + Pydantic 模型 |
| 工具描述给 LLM | `getAvailableTools()` 拼字符串 | `llm.bind_tools()` 生成 JSON Schema |
| 参数传递 | 字符串，手动正则解析 | OpenAI function calling 协议，结构化参数 |
| 类型安全 | 无（都是字符串） | 有（Pydantic 自动校验类型） |
| 执行工具 | `func(args)` 直接调用 | `ToolNode` 自动路由 + 执行 |
| 多工具 | 手动 `if/elif` 判断名字 | 自动匹配 |

本质区别：tools.py 是 **Prompt 驱动**（LLM 输出文本，本地解析），LangChain 是 **API 驱动**（LLM 输出结构化的 function_call，框架自动执行）。

## 关键收获

1. **LLM 不能执行代码**——它只是"决定"要调什么，真正的执行在本地
2. **工具描述是给 LLM 看的**——`getAvailableTools()` 的输出会被塞进 Prompt，LLM 根据描述选择合适的工具
3. **智能解析减少 token 浪费**——search() 不是返回原始 JSON，而是提取最精炼的答案
4. **ToolExecutor 是最小可用的工具框架**——注册、查找、格式化，三个方法覆盖了核心需求
5. **从手动到自动的演进**：tools.py 的手动解析 → LangChain 的 function calling，是从学习到生产的升级路径
