---
title: hello-agent 学习第3天：Reflection 反思模式
date: 2026-05-09
tags: [AI, LLM, Python, Agent, Prompt]
description: 学习了 Reflection Agent 设计模式，理解了"执行 → 反思 → 优化"的迭代循环机制，以及记忆模块在 Agent 中的作用。
---
## 理解 Reflection 模式

 `Reflection.py`，这是一个实现了**自我反思与迭代优化**的 Agent。核心思想很简单：**写完代码不等于完成，还要让另一个"角色"来审查，发现问题后修改，反复迭代直到满意为止**。

如果说 Plan-and-Solve（第2天）是"先想好再做"，那 Reflection 就是"做完之后回头看，发现不对就改"。

## 完整代码（Reflection.py）

注意：代码中的 Prompt 模板包含 ` ```python ` 标记，这里用 4 个反引号包裹外层代码块避免 markdown 嵌套冲突。

````python
from typing import List, Dict, Any
from llm_client import HelloAgentsLLM

# --- 模块 1: 记忆模块 ---

class Memory:
    """
    一个简单的短期记忆模块，用于存储智能体的行动与反思轨迹。
    """
    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def add_record(self, record_type: str, content: str):
        self.records.append({"type": record_type, "content": content})
        print(f"📝 记忆已更新，新增一条 '{record_type}' 记录。")

    def get_trajectory(self) -> str:
        trajectory = ""
        for record in self.records:
            if record['type'] == 'execution':
                trajectory += f"--- 上一轮尝试 (代码) ---\n{record['content']}\n\n"
            elif record['type'] == 'reflection':
                trajectory += f"--- 评审员反馈 ---\n{record['content']}\n\n"
        return trajectory.strip()

    def get_last_execution(self) -> str:
        for record in reversed(self.records):
            if record['type'] == 'execution':
                return record['content']
        return None

# --- 模块 2: Reflection 智能体 ---

# 1. 初始执行提示词
INITIAL_PROMPT_TEMPLATE = """
你是一位资深的Python程序员。请根据以下要求，编写一个Python函数。
你的代码必须包含完整的函数签名、文档字符串，并遵循PEP 8编码规范。

要求: {task}

请直接输出代码，不要包含任何额外的解释。
"""

# 2. 反思提示词
REFLECT_PROMPT_TEMPLATE = """
你是一位极其严格的代码评审专家和资深算法工程师，对代码的性能有极致的要求。
你的任务是审查以下Python代码，并专注于找出其在**算法效率**上的主要瓶颈。

# 原始任务:
{task}

# 待审查的代码:
```python
{code}
```

请分析该代码的时间复杂度，并思考是否存在一种**算法上更优**的解决方案来显著提升性能。
如果存在，请清晰地指出当前算法的不足，并提出具体的、可行的改进算法建议（例如，使用筛法替代试除法）。
如果代码在算法层面已经达到最优，才能回答"无需改进"。

请直接输出你的反馈，不要包含任何额外的解释。
"""

# 3. 优化提示词
REFINE_PROMPT_TEMPLATE = """
你是一位资深的Python程序员。你正在根据一位代码评审专家的反馈来优化你的代码。

# 原始任务:
{task}

# 你上一轮尝试的代码:
{last_code_attempt}

# 评审员的反馈:
{feedback}

请根据评审员的反馈，生成一个优化后的新版本代码。
你的代码必须包含完整的函数签名、文档字符串，并遵循PEP 8编码规范。
请直接输出优化后的代码，不要包含任何额外的解释。
"""

class ReflectionAgent:
    def __init__(self, llm_client, max_iterations=3):
        self.llm_client = llm_client
        self.memory = Memory()
        self.max_iterations = max_iterations

    def run(self, task: str):
        print(f"\n--- 开始处理任务 ---\n任务: {task}")

        # --- 1. 初始执行 ---
        print("\n--- 正在进行初始尝试 ---")
        initial_prompt = INITIAL_PROMPT_TEMPLATE.format(task=task)
        initial_code = self._get_llm_response(initial_prompt)
        self.memory.add_record("execution", initial_code)

        # --- 2. 迭代循环：反思与优化 ---
        for i in range(self.max_iterations):
            print(f"\n--- 第 {i+1}/{self.max_iterations} 轮迭代 ---")

            # a. 反思
            print("\n-> 正在进行反思...")
            last_code = self.memory.get_last_execution()
            reflect_prompt = REFLECT_PROMPT_TEMPLATE.format(task=task, code=last_code)
            feedback = self._get_llm_response(reflect_prompt)
            self.memory.add_record("reflection", feedback)

            # b. 检查是否需要停止
            if "无需改进" in feedback or "no need for improvement" in feedback.lower():
                print("\n✅ 反思认为代码已无需改进，任务完成。")
                break

            # c. 优化
            print("\n-> 正在进行优化...")
            refine_prompt = REFINE_PROMPT_TEMPLATE.format(
                task=task,
                last_code_attempt=last_code,
                feedback=feedback
            )
            refined_code = self._get_llm_response(refine_prompt)
            self.memory.add_record("execution", refined_code)

        final_code = self.memory.get_last_execution()
        print(f"\n--- 任务完成 ---\n最终生成的代码:\n{final_code}")
        return final_code

    def _get_llm_response(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        response_text = self.llm_client.think(messages=messages) or ""
        return response_text

if __name__ == '__main__':
    try:
        llm_client = HelloAgentsLLM()
    except Exception as e:
        print(f"初始化LLM客户端时出错: {e}")
        exit()

    agent = ReflectionAgent(llm_client, max_iterations=2)
    task = "编写一个Python函数，找出1到n之间所有的素数 (prime numbers)。"
    agent.run(task)
````

## 整体架构

```
用户提出任务: "编写一个找出素数的函数"
        │
        ▼
┌──────────────────────────────────────────────────────┐
│               ReflectionAgent                        │
│                                                      │
│  ┌──────────────┐                                    │
│  │   Memory     │  ← 存储所有执行和反思记录           │
│  │  (记忆模块)  │                                    │
│  └──────┬───────┘                                    │
│         │                                            │
│  Step 1: 初始执行                                    │
│  ┌──────────────┐                                    │
│  │ INITIAL_PROMPT│ → LLM → 生成 v1 代码              │
│  │ "写一个函数"  │    (如: 试除法 O(n√n))             │
│  └──────────────┘                                    │
│         │                                            │
│         ▼                                            │
│  ┌─────────────────────────────────────────┐         │
│  │     迭代循环 (最多 max_iterations 轮)     │         │
│  │                                         │         │
│  │  ┌──────────────────┐                   │         │
│  │  │ REFLECT_PROMPT   │ → LLM → 审查反馈  │         │
│  │  │ "你是评审专家"    │   "建议用筛法"    │         │
│  │  └────────┬─────────┘                   │         │
│  │           │                             │         │
│  │           ▼                             │         │
│  │    反馈含"无需改进"? ──是──→ 跳出循环    │         │
│  │           │ 否                          │         │
│  │           ▼                             │         │
│  │  ┌──────────────────┐                   │         │
│  │  │ REFINE_PROMPT    │ → LLM → 生成 v2   │         │
│  │  │ "根据反馈优化"    │   (如: 埃氏筛法)   │         │
│  │  └────────┬─────────┘                   │         │
│  │           │                             │         │
│  │           └──→ 回到反思步骤              │         │
│  └─────────────────────────────────────────┘         │
│                         │                            │
└─────────────────────────┼────────────────────────────┘
                          │
                          ▼
                 最终输出: 优化后的代码
```

## 三个核心组件的职责

| 组件 | 角色 | 做了什么 |
|---|---|---|
| `Memory` | 记忆模块 | 存储每一轮的执行代码和反思反馈，支持按时间线检索 |
| `ReflectionAgent` | 调度器 | 编排"初始执行 → 反思 → 优化"的循环流程 |
| 三套 Prompt | 角色切换 | 同一个 LLM 扮演三个角色：程序员、评审专家、根据反馈改代码的程序员 |

三套 Prompt 对应三种角色：

| Prompt 模板 | 扮演的角色 | 输入 | 输出 |
|---|---|---|---|
| `INITIAL_PROMPT_TEMPLATE` | 资深程序员 | 任务描述 | 初始代码 |
| `REFLECT_PROMPT_TEMPLATE` | 严格的代码评审专家 | 任务 + 代码 | 反馈意见（或"无需改进"） |
| `REFINE_PROMPT_TEMPLATE` | 根据反馈改代码的程序员 | 任务 + 上一轮代码 + 反馈 | 优化后的代码 |

## 关键技巧 1：Memory 记忆模块

Memory 是整个 Reflection 模式的基础设施。它用一条时间线记录了所有的"执行"和"反思"：

```
Memory.records 的内部结构:
[
  {"type": "execution",  "content": "def find_primes(n): ..."},      ← 第1次执行
  {"type": "reflection", "content": "建议使用埃氏筛法替代试除法..."},  ← 第1次反思
  {"type": "execution",  "content": "def find_primes(n): ..."},      ← 第2次执行（优化版）
  {"type": "reflection", "content": "无需改进"},                      ← 第2次反思（满意了）
]
```

两个关键方法：

**`add_record(record_type, content)`** — 往时间线末尾追加一条记录：

```python
def add_record(self, record_type: str, content: str):
    self.records.append({"type": record_type, "content": content})
```

**`get_last_execution()`** — 从后往前找最新一次执行结果：

```python
def get_last_execution(self) -> str:
    for record in reversed(self.records):  # ← 倒序遍历
        if record['type'] == 'execution':
            return record['content']
    return None
```

为什么要 `reversed()`？因为最新的执行结果在列表末尾，从后往前找效率更高。

还有一个 **`get_trajectory()`** 方法，把所有记录格式化为连续文本。虽然当前代码没有在 Prompt 中使用它，但它的设计意图是：把完整的"做了什么 → 被批评了什么 → 改了什么"的轨迹传给 LLM，让 LLM 能看到完整的迭代历史。这个方法在更复杂的 Reflection Agent 中会非常有用。

## 关键技巧 2：角色切换（用 Prompt 扮演不同身份）

Reflection 的精髓在于：**同一个 LLM，通过不同的 Prompt 扮演不同的角色**。

```
同一个 LLM
    │
    ├── 初始执行时 → Prompt 说"你是资深程序员"       → 输出：代码
    │
    ├── 反思时    → Prompt 说"你是极其严格的评审专家"  → 输出：反馈
    │
    └── 优化时    → Prompt 说"你根据反馈优化代码"      → 输出：新代码
```

这种"角色切换"的模式在 Agent 设计中非常常见。本质上就是：**LLM 的行为高度依赖 Prompt 中设定的角色和指令**。你让它当评审员，它就会吹毛求疵；你让它当程序员，它就会写代码。

角色设计的两个细节值得关注：

**1. 评审专家被设定为"极其严格"：**

```
你是一位极其严格的代码评审专家和资深算法工程师，对代码的性能有极致的要求。
```

这不是随便写的。如果 Prompt 说"请温和地指出小问题"，LLM 可能会给出很敷衍的反馈，导致迭代没有实质改进。"极其严格"迫使 LLM 认真审查代码。

**2. 反馈有明确的停止条件：**

```
如果代码在算法层面已经达到最优，才能回答"无需改进"。
```

这防止了 LLM 每次都说"还行吧"就停下来。它必须确认代码真的没问题才能说"无需改进"。

## 关键技巧 3：提前终止机制

循环不是一定要跑满 `max_iterations` 轮。代码中有一个提前终止的检查：

```python
if "无需改进" in feedback or "no need for improvement" in feedback.lower():
    print("\n✅ 反思认为代码已无需改进，任务完成。")
    break
```

运行时的两种情况：

```
情况 1: 第1轮反思就说"无需改进" → 只迭代1次就结束
  Memory: [execution_1, reflection_1(无需改进)]
  输出: execution_1 的代码

情况 2: 第2轮反思还说有问题 → 跑满 max_iterations 轮
  Memory: [execution_1, reflection_1, execution_2, reflection_2, execution_3]
  输出: execution_3 的代码（最后一轮优化的结果）
```

注意 `break` 之后取的是 `memory.get_last_execution()`，即最后一次执行记录，而不是最后一次反思记录。这保证了输出一定是代码，而不是反馈文本。

## 以"找出素数"为例的模拟运行过程

```
任务: 编写一个Python函数，找出1到n之间所有的素数。

--- 开始处理任务 ---
--- 正在进行初始尝试 ---
📝 记忆已更新，新增一条 'execution' 记录。

→ 初始代码（v1）: 试除法，对每个数判断能否被 2~√n 整除
  时间复杂度: O(n√n)

--- 第 1/2 轮迭代 ---

-> 正在进行反思...
📝 记忆已更新，新增一条 'reflection' 记录。

→ 反馈: 试除法虽然正确，但效率不够高。
  建议使用埃拉托斯特尼筛法（Sieve of Eratosthenes），
  时间复杂度可以降到 O(n log log n)。

-> 正在进行优化...
📝 记忆已更新，新增一条 'execution' 记录。

→ 优化代码（v2）: 用布尔数组实现埃氏筛法

--- 第 2/2 轮迭代 ---

-> 正在进行反思...
📝 记忆已更新，新增一条 'reflection' 记录。

→ 反馈: 埃氏筛法已是该问题的最优算法，无需改进。

✅ 反思认为代码已无需改进，任务完成。

--- 任务完成 ---
最终生成的代码: v2（埃氏筛法版本）
```

## 与 Plan-and-Solve 的对比

| | Plan-and-Solve | Reflection |
|---|---|---|
| 核心思想 | 先规划，再执行 | 先执行，再审查，循环改进 |
| 流程方向 | 线性（规划 → 步骤1 → 步骤2 → ...） | 环形（执行 → 反思 → 优化 → 反思 → ...） |
| 角色数量 | 2 个（规划器 + 执行器） | 3 个（程序员 + 评审 + 改代码的程序员） |
| 适合场景 | 复杂的多步骤问题 | 需要反复打磨质量的单一任务 |
| 记忆机制 | Executor 通过 history 字符串累积上下文 | Memory 类存储结构化的执行/反思记录 |
| 终止条件 | 执行完所有步骤 | 反馈含"无需改进"或达到最大迭代次数 |
| 能否纠错 | ❌ 步骤间错误会传播 | ✅ 每轮都有机会发现并修正问题 |

## 这个模式的局限

**1. 停止条件依赖关键词匹配**

```python
if "无需改进" in feedback or "no need for improvement" in feedback.lower():
```

这只是简单的字符串包含检查。LLM 可能会说"代码已经很好了，不需要再优化"，其中不含"无需改进"这个精确字符串，就导致无法正确终止。更健壮的做法是让 LLM 输出结构化的 JSON（如 `{"improve": false}`），或者用另一个 LLM 来判断是否应该停止。

**2. 角色之间共享同一个 LLM**

三个角色用的是同一个 `llm_client` 实例。如果 LLM 本身对某个知识点理解有偏差（比如它不熟悉某种算法），那无论是"程序员"还是"评审专家"角色，都会带有同样的认知偏差。现实中可能需要用不同的模型来扮演不同角色。

**3. 只优化不验证**

Reflection 循环中有"反思"和"优化"，但没有"验证"。优化后的代码是否真的比之前好？没有实际运行代码来验证。评审专家只是基于代码逻辑做静态分析，没有跑测试用例。如果加上"运行代码 → 检查输出是否正确 → 检查性能是否提升"这一步，会更可靠。

**4. 反馈可能越来越空泛**

多轮迭代后，容易改进的地方已经被改完了，后续的反馈可能会变得空泛或重复（"可以考虑微调变量名"之类的），但代码实质上没有提升。`max_iterations` 的存在就是为了防止无限循环，但也说明纯粹的反思迭代有收益递减的问题。

## 为什么说它比 Plan-and-Solve 更"像 Agent"？

| Agent 特征 | Plan-and-Solve | Reflection |
|---|---|---|
| 感知环境 | ✅ 接收用户问题 | ✅ 接收用户任务 |
| 规划 | ✅ Planner 生成计划 | ❌ 没有显式规划 |
| 行动 | ⚠️ 只能调用 LLM | ⚠️ 只能调用 LLM |
| 观察结果 | ✅ Executor 累积历史 | ✅ Memory 记录轨迹 |
| 调整策略 | ❌ 计划固定不变 | ✅ 根据反馈调整代码 |

Reflection 模式的核心优势在于 **"调整策略"** 这一项。它能根据反思的结果改变下一步的行为，这比 Plan-and-Solve 的"一条路走到黑"要灵活得多。虽然没有显式的"规划"步骤，但反思本身就是一种隐式的"重新思考"。

## 总结

- **Reflection** = 执行 → 反思 → 优化，循环迭代直到满意
- **Memory** 模块用 `records` 列表按时间线存储所有的执行和反思记录
- 同一个 LLM 通过 **三套 Prompt 扮演三个角色**（程序员、评审专家、优化者）
- 用 **关键词匹配**（"无需改进"）作为提前终止条件
- 优势：能自我纠错、迭代改进质量
- 局限：停止条件脆弱、角色共享同一认知偏差、没有实际验证、反馈可能越来越空泛
