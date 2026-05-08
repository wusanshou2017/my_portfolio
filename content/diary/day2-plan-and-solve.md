---
title: hello-agent 学习第2天：Plan-and-Solve 规划与求解模式
date: 2026-05-08
tags: [AI, LLM, Python, Agent, Prompt]
description: 学习了 Plan-and-Solve Agent 设计模式，用纯 Prompt 工程 + 循环实现轻量级 Agent，理解了规划器与执行器的协作机制。
---
## 理解 Plan-and-Solve 模式

今天看了 `Plan_and_solve.py`，这是一个用纯 Prompt 工程 + Python 循环实现的轻量级 Agent。没有用任何 Agent 框架，核心思想就是：**遇到复杂问题，先想清楚要做什么，再一步步做**。

## 完整代码（Plan_and_solve.py）

注意：Planner 的 Prompt 模板中包含 ` ```python ` 标记，这里用 4 个反引号包裹外层代码块避免 markdown 嵌套冲突。

````python
import os
import ast
from llm_client import HelloAgentsLLM
from dotenv import load_dotenv
from typing import List, Dict

try:
    load_dotenv()
except FileNotFoundError:
    print("警告：未找到 .env 文件，将使用系统环境变量。")
except Exception as e:
    print(f"警告：加载 .env 文件时出错: {e}")

# --- 2. 规划器 (Planner) 定义 ---
PLANNER_PROMPT_TEMPLATE = """
你是一个顶级的AI规划专家。你的任务是将用户提出的复杂问题分解成一个由多个简单步骤组成的行动计划。
请确保计划中的每个步骤都是一个独立的、可执行的子任务，并且严格按照逻辑顺序排列。
你的输出必须是一个Python列表，其中每个元素都是一个描述子任务的字符串。

问题: {question}

请严格按照以下格式输出你的计划，```python与```作为前后缀是必要的:
```python
["步骤1", "步骤2", "步骤3", ...]
```
"""

class Planner:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client

    def plan(self, question: str) -> list[str]:
        prompt = PLANNER_PROMPT_TEMPLATE.format(question=question)
        messages = [{"role": "user", "content": prompt}]

        print("--- 正在生成计划 ---")
        response_text = self.llm_client.think(messages=messages) or ""
        print(f"✅ 计划已生成:\n{response_text}")

        try:
            plan_str = response_text.split("```python")[1].split("```")[0].strip()
            plan = ast.literal_eval(plan_str)
            return plan if isinstance(plan, list) else []
        except (ValueError, SyntaxError, IndexError) as e:
            print(f"❌ 解析计划时出错: {e}")
            print(f"原始响应: {response_text}")
            return []
        except Exception as e:
            print(f"❌ 解析计划时发生未知错误: {e}")
            return []

# --- 3. 执行器 (Executor) 定义 ---
EXECUTOR_PROMPT_TEMPLATE = """
你是一位顶级的AI执行专家。你的任务是严格按照给定的计划，一步步地解决问题。
你将收到原始问题、完整的计划、以及到目前为止已经完成的步骤和结果。
请你专注于解决"当前步骤"，并仅输出该步骤的最终答案，不要输出任何额外的解释或对话。

# 原始问题:
{question}

# 完整计划:
{plan}

# 历史步骤与结果:
{history}

# 当前步骤:
{current_step}

请仅输出针对"当前步骤"的回答:
"""

class Executor:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client

    def execute(self, question: str, plan: list[str]) -> str:
        history = ""
        final_answer = ""

        print("\n--- 正在执行计划 ---")
        for i, step in enumerate(plan, 1):
            print(f"\n-> 正在执行步骤 {i}/{len(plan)}: {step}")
            prompt = EXECUTOR_PROMPT_TEMPLATE.format(
                question=question, plan=plan,
                history=history if history else "无", current_step=step
            )
            messages = [{"role": "user", "content": prompt}]

            response_text = self.llm_client.think(messages=messages) or ""

            history += f"步骤 {i}: {step}\n结果: {response_text}\n\n"
            final_answer = response_text
            print(f"✅ 步骤 {i} 已完成，结果: {final_answer}")

        return final_answer

# --- 4. 智能体 (Agent) 整合 ---
class PlanAndSolveAgent:
    def __init__(self, llm_client: HelloAgentsLLM):
        self.llm_client = llm_client
        self.planner = Planner(self.llm_client)
        self.executor = Executor(self.llm_client)

    def run(self, question: str):
        print(f"\n--- 开始处理问题 ---\n问题: {question}")
        plan = self.planner.plan(question)
        if not plan:
            print("\n--- 任务终止 --- \n无法生成有效的行动计划。")
            return
        final_answer = self.executor.execute(question, plan)
        print(f"\n--- 任务完成 ---\n最终答案: {final_answer}")

# --- 5. 主函数入口 ---
if __name__ == '__main__':
    try:
        llm_client = HelloAgentsLLM()
        agent = PlanAndSolveAgent(llm_client)
        question = "一个水果店周一卖出了15个苹果。周二卖出的苹果数量是周一的两倍。周三卖出的数量比周二少了5个。请问这三天总共卖出了多少个苹果？"
        agent.run(question)
    except ValueError as e:
        print(e)
````

## 整体架构

```
用户提出问题: "水果店三天卖了多少苹果？"
        │
        ▼
┌─────────────────────────────────────────┐
│           PlanAndSolveAgent             │
│                                         │
│  ┌──────────┐      ┌─────────────────┐  │
│  │ Planner  │ ───→ │ ["算周一销量",  │  │
│  │ (规划器) │      │  "算周二销量",  │  │
│  │          │      │  "算周三销量",  │  │
│  │          │      │  "算总销量"]    │  │
│  └──────────┘      └────────┬────────┘  │
│                             │           │
│                             ▼           │
│                    ┌─────────────────┐   │
│                    │   Executor      │   │
│                    │   (执行器)       │   │
│                    │                 │   │
│                    │  步骤1 → 15个   │   │
│                    │  步骤2 → 30个   │   │
│                    │  步骤3 → 25个   │   │
│                    │  步骤4 → 70个   │   │
│                    └────────┬────────┘   │
└─────────────────────────────┼───────────┘
                              │
                              ▼
                     最终答案: 70个苹果
```

## 三个核心类的职责

| 类 | 角色 | 输入 | 输出 | 做了什么 |
|---|---|---|---|---|
| `Planner` | 规划器 | 用户问题 | 步骤列表 `list[str]` | 让 LLM 把复杂问题拆成有序步骤 |
| `Executor` | 执行器 | 问题 + 步骤列表 | 最终答案 `str` | 按计划逐步调用 LLM，累积上下文 |
| `PlanAndSolveAgent` | 调度器 | 用户问题 | 最终答案 | 先规划再执行，串联整个流程 |

## 关键技巧 1：强制 LLM 输出结构化数据

Planner 的 Prompt 要求 LLM 输出 Python 列表格式，并且用 ` ```python ``` ` 包裹。

然后代码从 LLM 的文本响应中提取出 Python 列表：

```python
plan_str = response_text.split("```python")[1].split("```")[0].strip()
plan = ast.literal_eval(plan_str)
```

拆开看这个解析过程：

```
LLM 原始输出:
"好的，我来帮你分析：\n```python\n[\"算周一\", \"算周二\", \"算周三\"]\n```"
                  │                               │
                  ▼                               ▼
split("```python")[1]:  "\n[\"算周一\", \"算周二\", \"算周三\"]\n```"
                  │
                  ▼
split("```")[0]:  "\n[\"算周一\", \"算周二\", \"算周三\"]\n"
                  │
                  ▼
strip():  "[\"算周一\", \"算周二\", \"算周三\"]"
                  │
                  ▼
ast.literal_eval():  ["算周一", "算周二", "算周三"]  ← 真正的 Python list
```

为什么用 `ast.literal_eval()` 而不是 `eval()`？

| | `eval()` | `ast.literal_eval()` |
|---|---|---|
| 安全性 | ❌ 可以执行任意代码（如 `__import__('os').system('rm -rf /')`） | ✅ 只能解析字面量（字符串、数字、列表、字典） |
| 用途 | 执行表达式 | 安全地解析数据结构 |

LLM 的输出不可信，用 `ast.literal_eval()` 防止注入攻击。

## 关键技巧 2：累积上下文

Executor 每执行一步，都会把结果追加到 `history` 中：

```python
history = ""
for i, step in enumerate(plan, 1):
    prompt = EXECUTOR_PROMPT_TEMPLATE.format(
        question=question,
        plan=plan,
        history=history if history else "无",  # ← 每次传入更多历史
        current_step=step,
    )
    response_text = self.llm_client.think(messages=messages) or ""
    history += f"步骤 {i}: {step}\n结果: {response_text}\n\n"  # ← 累积
```

这样每一步的 LLM 调用都能看到之前所有步骤的结果：

```
步骤1 的 Prompt:
  历史步骤与结果: 无
  当前步骤: 计算周一卖出的苹果数量

步骤2 的 Prompt:
  历史步骤与结果:
    步骤 1: 计算周一卖出的苹果数量
    结果: 15个
  当前步骤: 计算周二卖出的苹果数量

步骤3 的 Prompt:
  历史步骤与结果:
    步骤 1: 计算周一卖出的苹果数量
    结果: 15个
    步骤 2: 计算周二卖出的苹果数量
    结果: 30个
  当前步骤: 计算周三卖出的苹果数量
```

就像做数学题时，每一步都把中间结果写在纸上，下一步可以回头看。

## 这个模式的局限

**1. 计划不能动态调整**

如果步骤 1 算错了，步骤 2 会基于错误结果继续算，错误会传播。没有回退或换方案的机制。

**2. 上下文越来越长**

每步都把完整历史传给 LLM，步骤多的时候 token 消耗会很大。上面代码中 `history` 字符串是不断追加的。

**3. 没有工具调用能力**

只能靠 LLM 自己推理计算，不能查数据库、调 API、搜索网页。适合纯推理问题（如数学题），不适合需要外部信息的场景。

**4. 解析可能失败**

依赖 LLM 严格按照 `["步骤1", "步骤2"]` 格式输出，如果 LLM "发挥创意" 改了格式，`ast.literal_eval()` 就会抛异常。代码里用 try/except 处理了这种情况，但会导致整个流程终止。

## 为什么说它是"轻量级 Agent"？

Agent 的核心特征是：**感知环境 → 规划 → 行动 → 观察结果 → 调整策略**。

Plan-and-Solve 实现了其中一部分：

| Agent 特征 | Plan-and-Solve | 完整 Agent |
|---|---|---|
| 感知环境 | ✅ 接收用户问题 | ✅ |
| 规划 | ✅ Planner 生成计划 | ✅ |
| 行动 | ⚠️ 只能调用 LLM（纯文本） | ✅ 可以调用工具 |
| 观察结果 | ✅ Executor 累积历史 | ✅ |
| 调整策略 | ❌ 计划固定不变 | ✅ 可以动态调整 |

它是一个**没有工具、不能调整策略的 Agent**，但核心思想（先规划再执行）是 Agent 设计的经典模式之一。

## 总结

- **Plan-and-Solve** = 先规划，再执行，两阶段分离
- **Planner** 负责拆解问题，输出结构化的步骤列表
- **Executor** 负责逐步执行，通过累积 history 让每步都能看到前面的结果
- 用 `ast.literal_eval()` 安全解析 LLM 输出的 Python 列表
- 优势：实现简单、逻辑清晰、适合纯推理问题
- 局限：不能调用工具、计划不能动态调整、长步骤时上下文膨胀
