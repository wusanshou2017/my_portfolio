import re
from typing import Optional, List
from ..core.agent import Agent
from ..core.llm import HelloAgentsLLM
from ..core.config import Config
from ..core.message import Message


PLANNER_PROMPT = """你是一个任务规划专家。请针对以下问题，制定一个分步执行计划。

## 问题
{question}

请输出一个编号列表，每一步是一个清晰可执行的子任务。"""

EXECUTOR_PROMPT = """你是一个任务执行者。请根据已有的信息和当前子任务，给出精确的答案。

## 原始问题
{question}

## 已完成的步骤
{completed}

## 当前需要执行的子任务
{current_step}

请只执行当前子任务，给出结果。"""


class PlanAndSolveAgent(Agent):

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        max_steps: int = 5,
    ):
        super().__init__(name, llm, system_prompt, config)
        self.max_steps = max_steps

    def run(self, input_text: str, **kwargs) -> str:
        plan = self._plan(input_text, **kwargs)
        steps = self._parse_steps(plan)
        if not steps:
            self.add_message(Message(input_text, "user"))
            self.add_message(Message(plan, "assistant"))
            return plan

        results = []
        for i, step in enumerate(steps[: self.max_steps]):
            completed = "\n".join(f"步骤{j+1}: {results[j]}" for j in range(i))
            answer = self._execute_step(input_text, completed, step, **kwargs)
            results.append(answer)

        final = "\n".join(f"步骤{i+1}: {r}" for i, r in enumerate(results))
        summary_prompt = f"原始问题：{input_text}\n\n以下是各步骤的执行结果：\n{final}\n\n请综合以上结果，给出最终答案。"
        final_answer = self.llm.invoke([{"role": "user", "content": summary_prompt}], **kwargs)

        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final_answer, "assistant"))
        return final_answer

    def _plan(self, question: str, **kwargs) -> str:
        prompt = PLANNER_PROMPT.format(question=question)
        return self.llm.invoke([{"role": "user", "content": prompt}], **kwargs)

    def _parse_steps(self, plan: str) -> List[str]:
        lines = plan.strip().split("\n")
        steps = []
        for line in lines:
            line = line.strip()
            match = re.match(r"^\d+[\.\)、]\s*(.+)", line)
            if match:
                steps.append(match.group(1).strip())
        return steps

    def _execute_step(self, question: str, completed: str, current_step: str, **kwargs) -> str:
        prompt = EXECUTOR_PROMPT.format(question=question, completed=completed, current_step=current_step)
        return self.llm.invoke([{"role": "user", "content": prompt}], **kwargs)
