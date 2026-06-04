from typing import Optional, List
from hello_agents import PlanAndSolveAgent, HelloAgentsLLM, Config, Message

MY_PLANNER_PROMPT = """你是一个任务规划专家。请针对以下问题，制定一个分步执行计划。每个步骤必须是一个具体的、可以直接计算或回答的子任务。

## 问题
{question}

请严格按以下格式输出计划：
1. [具体子任务描述]
2. [具体子任务描述]
3. [具体子任务描述]
...

注意：只输出计划步骤，不要输出计算过程或答案。"""

MY_EXECUTOR_PROMPT = """你是一个精确的任务执行者。

## 原始问题
{question}

## 已完成步骤的已知数据
{completed}

## 当前子任务
{current_step}

## 输出要求
只输出一个精确的数值结果，不要输出计算过程、等式或解释。例如：直接输出 30，不要输出 "15 * 2 = 30"。"""


class MyPlanAndSolveAgent(PlanAndSolveAgent):
    """
    重写的 Plan-and-Solve Agent
    先规划再执行，支持逐步打印过程
    """

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        max_steps: int = 5,
    ):
        super().__init__(name, llm, system_prompt, config, max_steps)
        print(f"✅ {name} 初始化完成，最大步数: {max_steps}")

    def run(self, input_text: str, **kwargs) -> str:
        print(f"\n🤖 {self.name} 开始处理: {input_text}")

        # 阶段1：规划
        print("\n📋 阶段1：生成执行计划...")
        plan = self._plan(input_text, **kwargs)
        print(f"  计划: {plan[:300]}")

        steps = self._parse_steps(plan)
        if not steps:
            self.add_message(Message(input_text, "user"))
            self.add_message(Message(plan, "assistant"))
            return plan

        # 阶段2：逐步执行
        print(f"\n🔧 阶段2：逐步执行（共 {len(steps)} 步）")
        results = []
        for i, step in enumerate(steps[: self.max_steps]):
            print(f"\n  --- 执行步骤 {i+1}: {step} ---")
            known = f"原始问题: {input_text}\n"
            if results:
                known += "\n".join(f"步骤{j+1}结果: {results[j]}" for j in range(i))
            answer = self._execute_step(input_text, known, step, **kwargs)
            print(f"  📌 结果: {answer}")
            results.append(answer)

        # 阶段3：汇总
        print("\n📊 阶段3：汇总结果...")
        final = "\n".join(f"步骤{i+1}: {r}" for i, r in enumerate(results))
        summary_prompt = f"原始问题：{input_text}\n\n以下是各步骤的执行结果：\n{final}\n\n请综合以上结果，给出最终答案。只输出最终答案，不要解释过程。"
        final_answer = self.llm.invoke([{"role": "user", "content": summary_prompt}], **kwargs)
        print(f"  🎯 最终答案: {final_answer}")

        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_answer, "assistant"))
        return final_answer

    def _plan(self, question: str, **kwargs) -> str:
        prompt = MY_PLANNER_PROMPT.format(question=question)
        return self.llm.invoke([{"role": "user", "content": prompt}], **kwargs)

    def _execute_step(self, question: str, completed: str, current_step: str, **kwargs) -> str:
        prompt = MY_EXECUTOR_PROMPT.format(
            question=question,
            completed=completed or "暂无",
            current_step=current_step,
        )
        collected = []
        for chunk in self.llm.stream_invoke([{"role": "user", "content": prompt}], **kwargs):
            print("chunk:...",chunk, end="", flush=True)
            collected.append(chunk)
    
        return "".join(collected)
