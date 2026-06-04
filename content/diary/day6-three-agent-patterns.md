---
title: hello-agents 学习第6天：四种 Agent 模式基类分析 + 实验对比
date: 2026-06-04
tags: [AI, LLM, Python, Agent, Simple, ReAct, Plan-and-Solve, Reflection]
description: 深入分析 SimpleAgent、ReAct、Plan-and-Solve、Reflection 四种 Agent 模式的基类实现，运行实验对比各模式的循环机制和输出效果。
---

## 四种模式概览

hello_agents 框架在 `agents/` 目录下实现了四种 Agent 模式，都继承自同一个抽象基类 `Agent`：

```python
# hello_agents/core/agent.py
class Agent(ABC):
    def __init__(self, name, llm, system_prompt=None, config=None):
        self.name = name
        self.llm = llm
        self.system_prompt = system_prompt
        self.config = config or Config()
        self._history: List[Message] = []

    @abstractmethod
    def run(self, input_text: str, **kwargs) -> str:
        """唯一的抽象方法——每种模式的核心逻辑都在这里"""
        pass

    def add_message(self, message: Message) -> None:  # 追加消息到历史
    def get_history(self) -> List[Message]:            # 获取对话历史
    def clear_history(self) -> None:                   # 清空历史
```

基类设计很克制：只定义 `run()` 为抽象方法，`add_message/get_history/clear_history` 作为通用能力放在基类。四种 Agent 各自的循环逻辑全部在子类的 `run()` 中实现。

四种模式的核心区别在于 `run()` 内部的循环策略：

| 模式 | 核心思想 | 循环驱动 | 是否需要工具 | LLM 调用次数 |
|---|---|---|---|---|
| Simple | 单轮对话 | 无循环 | 可选 | 1次（或多轮工具迭代） |
| ReAct | 想一步做一步 | LLM 决策 | 需要 ToolRegistry | 不确定 |
| Plan-and-Solve | 先规划再执行 | 代码驱动 | 不需要 | N+2（固定） |
| Reflection | 写完自己改 | 代码驱动 | 不需要 | 1+2×轮数（固定） |

## SimpleAgent 基类分析

SimpleAgent 是最基础的 Agent，**无循环**，一次调用直接返回：

```python
# hello_agents/agents/simple_agent.py
class SimpleAgent(Agent):

    def run(self, input_text: str, **kwargs) -> str:
        messages = []
        # 1. 拼接 system 消息
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        # 2. 拼接历史消息（支持多轮对话上下文）
        for msg in self._history:
            messages.append({"role": msg.role, "content": msg.content})
        # 3. 追加当前用户消息
        messages.append({"role": "user", "content": input_text})

        # 4. 调用 LLM（静默模式，无 print 副作用）
        response = self.llm.invoke(messages, **kwargs)

        # 5. 存入历史
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(response, "assistant"))
        return response
```

消息拼接顺序：`system → 历史消息 → 当前用户消息`。没有循环、没有工具调用、没有正则解析。这是所有 Agent 模式中最简单的——一次 `invoke()` 拿到结果直接返回。

### MySimpleAgent 扩展

子类 `MySimpleAgent` 在基类上增加了三个能力：

**能力1：可选的工具调用**

```python
# my_simple_agent.py
class MySimpleAgent(SimpleAgent):
    def __init__(self, name, llm, ..., tool_registry=None, enable_tool_calling=True):
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry = tool_registry
        # 只有两个条件同时满足才启用工具
        self.enable_tool_calling = enable_tool_calling and tool_registry is not None
```

`run()` 方法根据 `enable_tool_calling` 走不同分支：

```python
def run(self, input_text, max_tool_iterations=3, **kwargs):
    if not self.enable_tool_calling:
        # 简单对话：直接调 LLM 返回
        response = self.llm.invoke(messages, **kwargs)
        return response
    else:
        # 工具增强：走 _run_with_tools 循环
        return self._run_with_tools(messages, input_text, max_tool_iterations, **kwargs)
```

`_run_with_tools()` 的核心逻辑——LLM 输出文本后，用正则检测 `[TOOL_CALL:tool_name:parameters]` 标记：

```python
def _run_with_tools(self, messages, input_text, max_tool_iterations, **kwargs):
    while current_iteration < max_tool_iterations:
        response = self.llm.invoke(messages, **kwargs)

        # 正则检测工具调用标记
        tool_calls = self._parse_tool_calls(response)

        if tool_calls:
            # 执行工具，把结果追加到消息列表，再次调 LLM
            for call in tool_calls:
                result = self._execute_tool_call(call['tool_name'], call['parameters'])
                tool_results.append(result)
            messages.append({"role": "user", "content": f"工具执行结果：\n{tool_results_text}"})
            current_iteration += 1
            continue

        # 没有 TOOL_CALL 标记 → 这是最终回答
        final_response = response
        break
    return final_response
```

工具调用的正则解析：

```python
def _parse_tool_calls(self, text):
    pattern = r'\[TOOL_CALL:([^:]+):([^\]]+)\]'
    matches = re.findall(pattern, text)
    # "[TOOL_CALL:calculator:15 * 8 + 32]" → [("calculator", "15 * 8 + 32")]
```

**能力2：流式响应**

```python
def stream_run(self, input_text, **kwargs) -> Iterator[str]:
    """自定义流式运行方法——边生成边输出"""
    full_response = ""
    print("📝 实时响应: ", end="")
    for chunk in self.llm.stream_invoke(messages, **kwargs):
        full_response += chunk
        print(chunk, end="", flush=True)  # 每到一个 token 就打印
        yield chunk                         # 同时作为生成器返回给调用方
    print()  # 换行
    # 保存完整对话到历史
    self.add_message(Message(input_text, "user"))
    self.add_message(Message(full_response, "assistant"))
```

**能力3：动态工具管理**

```python
def add_tool(self, tool) -> None:
    """添加工具（如果没有 ToolRegistry 会自动创建）"""
    if not self.tool_registry:
        from hello_agents import ToolRegistry
        self.tool_registry = ToolRegistry()
        self.enable_tool_calling = True
    self.tool_registry.register_tool(tool)

def has_tools(self) -> bool:      # 检查是否有可用工具
def remove_tool(self, name) -> bool:  # 移除工具
def list_tools(self) -> list:      # 列出所有工具名
```

### SimpleAgent 实验输出

测试代码创建了两个 Agent：一个不带工具，一个带计算器工具：

```python
# 基础对话 Agent（无工具）
basic_agent = MySimpleAgent(name="基础助手", llm=llm,
    system_prompt="你是一个友好的AI助手，请用简洁明了的方式回答问题。")

# 工具增强 Agent
tool_registry = ToolRegistry()
tool_registry.register_tool(CalculatorTool())
enhanced_agent = MySimpleAgent(name="增强助手", llm=llm,
    tool_registry=tool_registry, enable_tool_calling=True)
```

运行结果：

```
=== 测试1：基础对话 ===
✅ 基础助手 初始化完成，工具调用: 禁用
🤖 基础助手 正在处理: 你好，请介绍一下自己
✅ 基础助手 响应完成
基础对话响应: 你好！我是你的AI助手，可以帮你解答问题、提供信息、聊天或者完成一些任务。

=== 测试2：工具增强对话 ===
✅ 增强助手 初始化完成，工具调用: 启用
🤖 增强助手 正在处理: 请帮我计算 15 * 8 + 32
✅ 增强助手 响应完成
工具增强响应: 好的，我来帮你计算这个表达式。
首先计算乘法：15 * 8 = 120
然后加上 32：120 + 32 = 152
所以结果是 **152**。

=== 测试3：流式响应 ===
🌊 基础助手 开始流式处理: 请解释什么是人工智能
📝 实时响应: 人工智能（AI）就是让机器模拟人类的智能行为...
✅ 基础助手 流式响应完成

=== 测试4：动态工具管理 ===
添加工具前: False
🔧 工具 'calculator' 已添加
添加工具后: True
可用工具: ['calculator']
```

注意：工具增强模式下，LLM 自己决定是否调用工具。测试2中 LLM 看到数学问题后输出了 `[TOOL_CALL:calculator:15 * 8 + 32]`，被正则解析后执行了 `calculate("15 * 8 + 32")`。

## ReActAgent 基类分析

```python
# hello_agents/agents/react_agent.py
class ReActAgent(Agent):
    def __init__(self, name, llm, ..., config=None):
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry: Optional[ToolRegistry] = None  # 子类设置
        self.max_steps = 5

    def run(self, input_text, **kwargs):
        raise NotImplementedError("ReActAgent.run 需要由子类实现")
```

基类**不实现 `run()`**，只提供三个正则解析方法：

```python
def _parse_output(self, text) -> Tuple[str, Optional[str]]:
    """从 LLM 完整回复中提取 Thought 和 Action"""
    thought_match = re.search(r"Thought:\s*(.+?)(?=\n(?:Thought|Action|$))", text, re.DOTALL)
    action_match = re.search(r"Action:\s*(.+?)(?:\n|$)", text, re.DOTALL)
    thought = thought_match.group(1).strip() if thought_match else ""
    action = action_match.group(1).strip() if action_match else None
    return thought, action

def _parse_action(self, action) -> Tuple[str, str]:
    """从 Action 字符串提取工具名和参数"""
    match = re.match(r"(\w+)\[(.+)\]", action.strip())
    if match:
        return match.group(1), match.group(2)  # ("calculate", "30 * 0.6")
    return action, ""

def _parse_action_input(self, action) -> str:
    """从 Finish[答案] 中提取最终答案"""
    match = re.match(r"Finish\[(.+)\]", action.strip())
    if match:
        return match.group(1)
```

Prompt 模板定义了 LLM 的输出格式约束：

```python
REACT_PROMPT = """你是一个具备推理和行动能力的AI助手。

## 可用工具
{tools}              ← ToolRegistry.get_tools_description() 生成的字符串

## 工作流程
Thought: 你的思考过程
Action: tool_name[参数] 或 Finish[最终答案]

## 当前任务
**Question:** {question}

## 执行历史
{history}            ← 前几轮的 Action/Observation 记录
"""
```

这是 **Prompt-driven** 模式——工具调用不是 OpenAI API 的 `function_call`，而是 LLM 输出纯文本后用正则解析。

子类 `MyReActAgent.run()` 实现的循环：

```python
while current_step < self.max_steps:
    # 1. 拼接 Prompt（工具描述 + 问题 + 历史记录）
    prompt = REACT_PROMPT.format(tools=..., question=..., history=...)
    messages = [{"role": "user", "content": prompt}]
    # 2. 调用 LLM
    response = llm.invoke(messages)
    # 3. 解析 Thought + Action
    thought, action = self._parse_output(response)
    # 4. 如果 Action 以 "Finish" 开头 → 返回答案
    if action and action.startswith("Finish"):
        return self._parse_action_input(action)
    # 5. 否则提取工具名和参数，执行工具
    tool_name, tool_input = self._parse_action(action)
    observation = tool_registry.execute_tool(tool_name, tool_input)
    # 6. 把 Action/Observation 追加到 current_history（下轮会拼进 Prompt）
    current_history.append(f"Action: {action}\nObservation: {observation}")
```

### ReAct 实验输出

```
🤖 我的推理行动助手 开始处理问题: (25 + 15) * 3 - 8 的结果是多少？

--- 第 1 步 ---
  💭 Thought: 这是一个简单的数学计算问题，我需要计算 (25 + 15) * 3 - 8 的结果。
  ⚡ Action: calculate[(25 + 15) * 3 - 8]
  👁️ Observation: 112

--- 第 2 步 ---
  💭 Thought: 我已经通过计算工具得到了结果112，信息足够回答用户的问题。
  ⚡ Action: Finish[计算结果为：112]

🎯 测试1结果: 计算结果为：112

---

🤖 处理: 如果一个班级有30个学生，其中60%是女生，男生有多少人？

--- 第 1 步 ---
  💭 Thought: 我需要先计算女生人数。班级总人数是30，女生占60%，所以女生人数 = 30 * 0.6。
  ⚡ Action: calculate[30 * 0.6]
  👁️ Observation: 18.0

--- 第 2 步 ---
  💭 Thought: 根据计算，女生人数是18人。接下来计算男生人数 = 总人数 - 女生人数 = 30 - 18。
  ⚡ Action: calculate[30 - 18]
  👁️ Observation: 12

--- 第 3 步 ---
  💭 Thought: 我已经通过计算得出女生人数为18人，男生人数为12人。可以给出最终答案。
  ⚡ Action: Finish[女生有18人，男生有12人。]

🎯 测试3结果: 女生有18人，男生有12人。
```

关键观察：表达式 `(25 + 15) * 3 - 8` 不是代码拼的，是 **LLM 看到用户问题后自己写出来的**。本地代码只负责用正则提取表达式字符串，传给 `calculate()` 用 ast 求值。每步的 Action 是 LLM 自己决定的——LLM 看到 Observation 后自主判断下一步该做什么。

自定义 Prompt 也能正常工作（测试4）：

```python
custom_prompt = """你是一个数学专家AI助手。
可用工具：{tools}
请按以下格式回应：
Thought: [你的思考]
Action: [tool_name[input] 或 Finish[答案]]
问题：{question}  历史：{history}  开始："""
```

```
🤖 数学专家助手 开始处理问题: 计算 15 × 8 + 32 ÷ 4 的结果
  💭 Thought: 根据运算优先级，先乘除后加减
  ⚡ Action: calculate[15*8+32/4]
  👁️ Observation: 128.0
  💭 Thought: 已经得到结果
  ⚡ Action: Finish[128]
🎯 自定义提示词测试结果: 128
```

## PlanAndSolveAgent 基类分析

```python
# hello_agents/agents/plan_solve_agent.py
class PlanAndSolveAgent(Agent):
    def __init__(self, name, llm, ..., max_steps=5):
        super().__init__(name, llm, system_prompt, config)
        self.max_steps = max_steps

    def run(self, input_text: str, **kwargs) -> str:
        # 阶段1：规划器——让 LLM 生成步骤列表
        plan = self._plan(input_text, **kwargs)
        steps = self._parse_steps(plan)  # 正则提取编号步骤

        if not steps:
            return plan  # LLM 没生成编号列表，直接返回原文

        # 阶段2：执行器——逐步执行每个子任务
        results = []
        for i, step in enumerate(steps[: self.max_steps]):
            completed = "\n".join(f"步骤{j+1}: {results[j]}" for j in range(i))
            answer = self._execute_step(input_text, completed, step, **kwargs)
            results.append(answer)

        # 阶段3：汇总——把所有步骤结果交给 LLM 生成最终答案
        final = "\n".join(f"步骤{i+1}: {r}" for i, r in enumerate(results))
        summary_prompt = f"原始问题：{input_text}\n\n以下是各步骤的执行结果：\n{final}\n\n请综合以上结果，给出最终答案。"
        final_answer = self.llm.invoke([{"role": "user", "content": summary_prompt}], **kwargs)

        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_answer, "assistant"))
        return final_answer
```

三阶段分离设计：**规划器 → 执行器 → 汇总**。LLM 调用次数固定为 N+2（1次规划 + N次执行 + 1次汇总）。

`_parse_steps()` 的正则支持多种编号格式：

```python
def _parse_steps(self, plan: str) -> List[str]:
    lines = plan.strip().split("\n")
    steps = []
    for line in lines:
        line = line.strip()
        match = re.match(r"^\d+[\.\)、]\s*(.+)", line)
        if match:
            steps.append(match.group(1).strip())
    return steps
    # "1. 计算周二销量" → "计算周二销量"
    # "1、计算周三销量" → "计算周三销量"
    # "1) 计算总销量"   → "计算总销量"
```

`_execute_step()` 的 Prompt 传入三个上下文变量：

```python
EXECUTOR_PROMPT = """你是一个任务执行者。
## 原始问题
{question}        ← 原始问题（提供上下文）
## 已完成的步骤
{completed}       ← 之前步骤的结果（渐进积累）
## 当前子任务
{current_step}    ← 当前需要执行的子任务
"""
```

### 基类缺陷与优化

基类的 `run()` 在构建 `completed` 时只传了之前步骤的结果，**没传原始问题的已知条件**。比如步骤3执行"周一+周二+周三"时，executor 只看到 `"步骤1结果: 30"` 和 `"步骤2结果: 25"`，不知道"周一=15"，容易算错。

`MyPlanAndSolveAgent` 的优化：

```python
# 优化1：每步都传入原始问题作为已知条件
known = f"原始问题: {input_text}\n"
if results:
    known += "\n".join(f"步骤{j+1}结果: {results[j]}" for j in range(i))

# 优化2：executor prompt 要求只返回纯数值
MY_EXECUTOR_PROMPT = """...
## 输出要求
只输出一个精确的数值结果，不要输出计算过程、等式或解释。
例如：直接输出 30，不要输出 "15 * 2 = 30"。

# 优化3：使用 stream_invoke 实现流式输出
def _execute_step(self, question, completed, current_step, **kwargs):
    collected = []
    for chunk in self.llm.stream_invoke([{"role": "user", "content": prompt}], **kwargs):
        print(chunk, end="", flush=True)  # 每个 token 到达就打印
        collected.append(chunk)
    print()
    return "".join(collected)
```

### Plan-and-Solve 实验输出

```
🤖 我的规划执行助手 开始处理: 一个水果店周一卖出了15个苹果。周二卖出的苹果数量是周一的两倍。
周三卖出的数量比周二少了5个。请问这三天总共卖出了多少个苹果？

📋 阶段1：生成执行计划...
  计划: 1. 计算周二卖出的苹果数量：将周一卖出的15个苹果乘以2。
  2. 计算周三卖出的苹果数量：将周二卖出的苹果数量减去5个。
  3. 计算三天总共卖出的苹果数量：将周一、周二和周三卖出的苹果数量相加。

🔧 阶段2：逐步执行（共 3 步）

  --- 执行步骤 1: 计算周二卖出的苹果数量：将周一卖出的15个苹果乘以2。 ---
30                                      ← 流式逐字输出
  📌 结果: 30

  --- 执行步骤 2: 计算周三卖出的苹果数量：将周二卖出的数量减去5个。 ---
25
  📌 结果: 25

  --- 执行步骤 3: 计算三天总共卖出的苹果数量：将周一、周二和周三卖出的数量相加。 ---
70
  📌 结果: 70

📊 阶段3：汇总结果...
  🎯 最终答案: 70

最终结果: 70
```

注意步骤3的 `70` 是 LLM 自己算出来的——它看到了原始问题（周一=15）和步骤1结果（周二=30）、步骤2结果（周三=25），所以正确算出 15+30+25=70。

## ReflectionAgent 基类分析

```python
# hello_agents/agents/reflection_agent.py
DEFAULT_PROMPTS = {
    "initial": "请完成以下任务：{task}",
    "reflect": "请审查以下内容，指出不足之处：\n任务：{task}\n内容：{content}",
    "refine":  "请根据反馈优化内容：\n任务：{task}\n反馈：{feedback}",
}

class ReflectionAgent(Agent):
    def __init__(self, name, llm, ..., custom_prompts=None, max_reflections=2):
        super().__init__(name, llm, system_prompt, config)
        self.prompts = custom_prompts or DEFAULT_PROMPTS
        self.max_reflections = max_reflections

    def _do_reflection(self, task: str, kwargs: dict) -> None:
        # 阶段1：生成初稿
        prompt = self.prompts["initial"].format(task=task)
        initial = self.llm.invoke([{"role": "user", "content": prompt}], **kwargs)
        self._history.append(Message(prompt, "user"))
        self._history.append(Message(initial, "assistant"))

        # 阶段2：循环反思（默认2轮）
        for _ in range(self.max_reflections):
            # 2a: 审查初稿，指出不足
            reflect_prompt = self.prompts["reflect"].format(task=task, content=initial)
            feedback = self.llm.invoke([{"role": "user", "content": reflect_prompt}], **kwargs)

            # 2b: 根据反馈优化
            refine_prompt = self.prompts["refine"].format(task=task, feedback=feedback)
            refined = self.llm.invoke([{"role": "user", "content": refine_prompt}], **kwargs)

            # 存入历史
            self._history.append(Message(reflect_prompt, "user"))
            self._history.append(Message(feedback, "assistant"))
            self._history.append(Message(refine_prompt, "user"))
            self._history.append(Message(refined, "assistant"))

            initial = refined  # 用优化结果作为下一轮的输入
```

三阶段循环：**生成 → 审查 → 优化**，循环 `max_reflections` 轮。每次循环包含**两次 LLM 调用**（reflect + refine），`max_reflections=2` 时总共调用 5 次 LLM（1 initial + 2×2 reflection）。

Prompt 模板支持自定义，通过 `custom_prompts` 参数替换为领域专用模板：

```python
# 通用模板（默认）
DEFAULT_PROMPTS = {
    "initial": "请完成以下任务：{task}",
    "reflect": "请审查以下内容，指出不足之处：\n任务：{task}\n内容：{content}",
    "refine":  "请根据反馈优化内容：\n任务：{task}\n反馈：{feedback}",
}

# 代码生成模板（自定义）
code_prompts = {
    "initial": "你是Python专家，请编写函数：{task}",
    "reflect": "请审查代码的算法效率：\n任务：{task}\n代码：{content}",
    "refine":  "请根据反馈优化代码：\n任务：{task}\n反馈：{feedback}",
}
```

`run()` 的实现也很简单——调用 `_do_reflection()` 后取历史最后一条：

```python
def run(self, input_text, **kwargs) -> str:
    self._do_reflection(input_text, kwargs)
    final = self._history[-1].content if self._history else ""
    self.add_message(Message(input_text, "user"))
    self.add_message(Message(final, "assistant"))
    return final
```

### Reflection 实验输出

```
🤖 我的反思助手 开始处理: 写一篇关于人工智能发展历程的简短文章

✍️ 阶段1：生成初稿...
  📝 初稿: # 人工智能发展历程：从梦想到现实
  人工智能（AI）的发展历程...1950年，艾伦·图灵发表了《计算机器与智能》...
  1956年，约翰·麦卡...

🔄 反思轮次 1/2...
  🔍 审查中...
  💬 反馈: 整体结构清晰、内容准确，但以下不足需要改进：
  1. 关键事件与人物细节缺失——只提到了图灵和麦卡锡，未提及马文·明斯基、
     弗兰克·罗森布拉特（感知机发明者）等早期重要人物...
  2. 历史阶段划分不够细致...
  ✏️ 优化中...
  📝 优化后: 人工智能（AI）的演进并非一蹴而就...可划分为五个关键阶段...
  补充了关键人物、技术细节、具体案例...

🔄 反思轮次 2/2...
  🔍 审查中...
  💬 反馈: 文章整体结构清晰，内容详实，但仍有不足：
  1. 段落长度失衡，第五部分采用列表形式，与前文不统一...
  2. 结尾略显仓促...
  ✏️ 优化中...
  📝 优化后: [形成完整的五阶段AI发展史，含参考文献]
  # 主要参考文献：
  # - Krizhevsky et al. (2012) ImageNet classification with deep CNNs
  # - Vaswani et al. (2017) Attention is all you need
  # - Russell & Norvig (2020) AI: A Modern Approach 4th ed.

🎯 最终结果: [完整的五阶段AI发展史，约2000字，含参考文献]
```

从初稿到最终稿，两轮反思逐步提升了内容质量：第一轮补充了关键人物和技术细节，第二轮调整了结构和格式。

## 四种模式对比总结

从基类设计角度看四者的继承关系：

```
Agent (ABC)                          ← 核心基类
├── run()           — 抽象方法，子类必须实现
├── add_message()    — 通用能力，基类提供
├── get_history()   — 通用能力，基类提供
└── clear_history()  — 通用能力，基类提供

SimpleAgent(Agent)           ReActAgent(Agent)           PlanAndSolveAgent(Agent)    ReflectionAgent(Agent)
├── run(): 完整实现             ├── run(): NotImplementedError  ├── run(): 完整实现         ├── run(): 完整实现
└── (无额外公开方法)             ├── _parse_output()            ├── _plan()                ├── _do_reflection()
                               ├── _parse_action()            ├── _parse_steps()         └── (无额外公开方法)
                               └── _parse_action_input()      └── _execute_step()

子类: +工具调用/流式/动态管理    子类: 实现循环逻辑           子类: 优化Prompt/上下文传递   子类: 添加打印
```

四种基类中，**ReAct 是唯一把 `run()` 留给子类实现的**——因为循环策略变化太大。Simple、Plan-and-Solve、Reflection 的循环模式相对固定（Simple 甚至无循环），基类直接实现了。

从实验结果看，选择哪种模式取决于任务性质：
- 简单对话，可选工具增强 → **Simple**（1次 LLM 调用，最快）
- 需要调用外部工具，LLM 动态决策 → **ReAct**（不确定步数，最灵活）
- 纯推理，可拆解为步骤 → **Plan-and-Solve**（固定 N+2 次调用，可预测）
- 内容创作，需要迭代优化质量 → **Reflection**（1+2×轮次，最费 token）
