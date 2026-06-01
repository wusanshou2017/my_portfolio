---
title: hello-agent 学习第5天：手写 hello_agents 框架 + ReAct Agent 实验验证
date: 2026-06-01
tags: [AI, LLM, Python, Agent, ReAct, Framework]
description: 从零手写 hello_agents Agent 框架，实现 core/agents/tools 三层架构，运行 ReAct Agent 实验验证 Thought→Action→Observation 循环。
---

## hello_agents 框架架构

第7章教程要求基于 `hello_agents` 框架写扩展代码（`my_simple_agent.py`、`my_react_agent.py` 等），但框架本身不是 pip 安装的第三方包，需要从零手写实现。

通过分析所有 `my_*.py` 和 `test_*.py` 中的 import 语句，提取出框架需要暴露的完整 API 接口，然后分层实现。

```
hello_agents/
├── __init__.py                  ← 统一导出所有公共接口
├── core/                        ← 核心层：LLM客户端 + Agent抽象基类
│   ├── llm.py                   ← HelloAgentsLLM
│   ├── agent.py                 ← Agent (ABC)
│   ├── message.py               ← Message (dataclass)
│   └── config.py                ← Config (dataclass)
├── agents/                      ← Agent模式实现层
│   ├── simple_agent.py          ← SimpleAgent
│   ├── react_agent.py          ← ReActAgent
│   ├── reflection_agent.py      ← ReflectionAgent
│   └── plan_solve_agent.py     ← PlanAndSolveAgent
└── tools/                       ← 工具层
    ├── base.py                  ← BaseTool (ABC)
    ├── registry.py              ← ToolRegistry
    └── builtin/
        ├── calculator.py        ← calculate() + CalculatorTool
        └── search.py            ← search() + SearchTool
```

## 核心层代码分析

### HelloAgentsLLM

所有 Agent 共享的 LLM 客户端，封装 OpenAI 兼容接口，通过 `PROVIDER_PATTERNS` 字典支持多个 LLM 提供商的自动检测：

```python
PROVIDER_PATTERNS = {
    "deepseek": {"base_url": "https://api.deepseek.com/v1", "env_key": "DEEPSEEK_API_KEY"},
    "openai":   {"base_url": "https://api.openai.com/v1",       "env_key": "OPENAI_API_KEY"},
    "qwen":     {"base_url": "https://dashscope.aliyuncs.com/...", "env_key": "QWEN_API_KEY"},
    # ...
}
```

初始化时根据 `provider` 参数决定取哪个环境变量：`"auto"` 走通用变量 `LLM_API_KEY/LLM_BASE_URL`，具体名称走对应提供商的专用变量。

三种调用方式的设计意图不同：

| 方法 | stream | 返回值 | 用途 |
|---|---|---|---|
| `think()` | `stream=True` | `str`（拼接后） | 第4章风格，边生成边打印，有 print 副作用 |
| `invoke()` | `stream=False` | `str` | Agent 循环内部调用，静默返回，无副作用 |
| `stream_invoke()` | `stream=True` | `Iterator[str]` | 流式 Agent，yield 逐块，由调用方决定如何展示 |

`invoke()` 是 Agent 框架内部最常用的方法——ReAct 循环每步都调用它拿到 LLM 的完整回复，然后解析 Thought/Action。

### Agent 抽象基类

```python
class Agent(ABC):
    def __init__(self, name, llm, system_prompt=None, config=None)
    def run(self, input_text, **kwargs) -> str    # 唯一的抽象方法
    def add_message(self, message)
    def get_history(self) -> List[Message]
    def clear_history(self)
```

设计很克制——只定义 `run()` 为抽象方法，`add_message/get_history` 作为通用能力放在基类。四种 Agent 模式（Simple、ReAct、Reflection、PlanAndSolve）各自的循环逻辑全部在子类的 `run()` 中实现。

## 工具层代码分析

### ToolRegistry

核心数据结构是一个嵌套字典：

```python
self._tools = {
    "calculate": {"description": "数学计算工具", "func": <function calculate>},
    "search":    {"description": "搜索互联网信息", "func": <function search>},
}
```

`register_function()` 的参数设计比较灵活，需要兼容两种调用风格：

```python
# test_react_agent.py 中的写法
registry.register_function("calculate", "数学计算描述", calculate)

# test_simple_agent.py 中的写法
registry.register_tool(CalculatorTool())
```

第一种是注册裸函数，第二种是注册 BaseTool 实例。`execute_tool()` 是实际调用工具的方法，接收 `tool_name` 和 `tool_input`（字符串），从字典中取出函数后直接调用。

`get_tools_description()` 返回格式化字符串，这个字符串会被**拼进 Prompt** 塞给 LLM，让 LLM 知道有哪些工具可用：

```
- calculate: 数学计算工具，支持基本的四则运算
- search: 搜索互联网信息
```

### calculate()：ast 安全求值

```python
def calculate(expression: str) -> str:
    node = ast.parse(expression, mode="eval")
    result = _eval(node.body, ops, funcs)
    return str(result)
```

用 `ast` 模块将字符串解析成 AST，然后递归遍历节点求值。关键安全设计：

- `ops` 字典只注册了 `Add/Sub/Mult/Div` 四种运算符
- `funcs` 字典只注册了 `sqrt` 和 `pi`
- `_eval()` 遇到不认识的节点类型直接 `raise ValueError`
- 不支持 `eval()`、`exec()`、`import` 等危险操作

这意味着即使 LLM 生成了恶意表达式如 `__import__('os').system('rm -rf /')`，`ast` 解析后不会匹配到任何合法运算，直接报错返回"计算失败"。

## ReAct Agent 核心代码分析

### 框架层：ReActAgent 基类

基类只提供**解析能力**，不实现循环：

```python
class ReActAgent(Agent):
    def run(self, input_text, **kwargs):
        raise NotImplementedError("ReActAgent.run 需要由子类实现")

    def _parse_output(self, text) -> Tuple[str, Optional[str]]:
        # 正则提取 Thought 和 Action

    def _parse_action(self, action) -> Tuple[str, str]:
        # 正则提取 tool_name[tool_input]

    def _parse_action_input(self, action) -> str:
        # 从 Finish[答案] 中提取最终答案
```

三个正则解析方法的设计：

- `_parse_output`：`re.search(r"Thought:\s*(.+?)(?=\n(?:Thought|Action|$))", text, re.DOTALL)` — 匹配 Thought 关键字后面的所有内容，直到遇到下一个 Thought/Action 或文本结束
- `_parse_action`：`re.match(r"(\w+)\[(.+)\]", action.strip())` — 匹配 `tool_name[input]` 格式
- `_parse_action_input`：`re.match(r"Finish\[(.+)\]", action.strip())` — 提取 Finish 括号里的答案

### 应用层：MyReActAgent 循环

真正的 ReAct 循环在 `MyReActAgent.run()` 中：

```python
while current_step < self.max_steps:
    # 1. 拼接 Prompt（工具描述 + 问题 + 历史记录）
    # 2. llm.invoke() 调用 LLM
    # 3. _parse_output() 解析 Thought + Action
    # 4. 如果 Action 以 "Finish" 开头 → 返回答案
    # 5. 否则 _parse_action() 提取工具名和参数
    #    → tool_registry.execute_tool() 执行工具
    #    → 把 Action/Observation 追加到 current_history
    #    → 继续循环
```

`current_history` 和 `self._history` 是两个不同的列表：
- `current_history`：当前这一轮 ReAct 的 Action/Observation 记录，每轮 `run()` 开始时清空，会**拼进 Prompt** 给 LLM 看
- `self._history`（来自基类 Agent）：跨轮次的完整对话记录，用于持久化

## ReflectionAgent 代码分析

Reflection 模式的核心是三阶段循环：生成→反思→优化

```python
def _do_reflection(self, task, kwargs):
    # 阶段1：生成初稿
    initial = llm.invoke(initial_prompt.format(task=task))

    # 阶段2：循环反思（默认2轮）
    for _ in range(max_reflections):
        # 2a: 审查初稿，给出反馈
        feedback = llm.invoke(reflect_prompt.format(task=task, content=initial))
        # 2b: 根据反馈优化
        refined = llm.invoke(refine_prompt.format(task=task, feedback=feedback))
        initial = refined  # 用优化结果作为下一轮的输入
```

每次循环包含**两次 LLM 调用**（reflect + refine），`max_reflections=2` 时总共调用 5 次 LLM（1 initial + 2×2 reflection）。Prompt 模板支持自定义：

```python
DEFAULT_PROMPTS = {
    "initial": "请完成以下任务：{task}",
    "reflect": "请审查以下内容，指出不足之处：\n任务：{task}\n内容：{content}",
    "refine":  "请根据反馈优化内容：\n任务：{task}\n反馈：{feedback}",
}
```

## PlanAndSolveAgent 代码分析

两阶段分离：先规划再逐步执行

```python
def run(self, input_text, **kwargs):
    # 阶段1：规划器 - 生成步骤列表
    plan = self._plan(input_text)           # LLM 生成 "1. xxx \n 2. xxx \n 3. xxx"
    steps = self._parse_steps(plan)         # 正则提取编号列表

    # 阶段2：执行器 - 逐步执行每个子任务
    for i, step in enumerate(steps):
        completed = 之前步骤的结果汇总
        answer = self._execute_step(question, completed, step)

    # 阶段3：汇总 - 把所有步骤结果交给 LLM 生成最终答案
    final_answer = llm.invoke(summary_prompt)
```

`_parse_steps()` 用正则 `r"^\d+[\.\)、]\s*(.+)"` 匹配 `1.xxx`、`2、xxx`、`3)xxx` 等多种编号格式。每个步骤执行时，会把之前已完成步骤的结果作为上下文传入，实现渐进式信息积累。

## ReAct 实验验证

运行 `test_react_agent.py` 的完整输出（测试3为例）：

```
🤖 开始处理: 如果一个班级有30个学生，其中60%是女生，男生有多少人？

--- 第 1 步 ---
  💭 Thought: 先算女生人数 = 30 * 0.6
  ⚡ Action: calculate[30 * 0.6]
  👁️ Observation: 18.0

--- 第 2 步 ---
  💭 Thought: 再算男生人数 = 30 - 18
  ⚡ Action: calculate[30 - 18]
  👁️ Observation: 12

--- 第 3 步 ---
  💭 Thought: 信息足够，给出最终答案
  ⚡ Action: Finish[男生有12人]
```

表达式 `(25 + 15) * 3 - 8` 不是代码拼的，是 **LLM 看到用户问题后自己写出来的**。本地代码只负责从 LLM 文本中用正则提取表达式字符串，传给 `calculate()` 用 ast 求值。

整个 ReAct 循环的本质：LLM 出脑（决策），本地代码出手（执行）。
