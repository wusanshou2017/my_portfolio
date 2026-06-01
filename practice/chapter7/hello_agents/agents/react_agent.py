import re
from typing import Optional, List, Tuple
from ..core.agent import Agent
from ..core.llm import HelloAgentsLLM
from ..core.config import Config
from ..core.message import Message
from ..tools.registry import ToolRegistry


REACT_PROMPT = """你是一个具备推理和行动能力的AI助手。

## 可用工具
{tools}

## 工作流程
请严格按照以下格式进行回应，每次只能执行一个步骤：

Thought: 你的思考过程，用于分析问题、拆解任务和规划下一步行动。
Action: 你决定采取的行动，格式为：
- `{{tool_name}}[{{tool_input}}]` - 调用指定工具
- `Finish[最终答案]` - 当你有足够信息给出最终答案时

## 重要提醒
1. 每次回应必须包含Thought和Action两部分
2. 工具调用的格式必须严格遵循：工具名[参数]
3. 只有当你确信有足够信息回答问题时，才使用Finish
4. 如果工具返回的信息不够，继续使用其他工具或相同工具的不同参数

## 当前任务
**Question:** {question}

## 执行历史
{history}

现在开始你的推理和行动：
"""


class ReActAgent(Agent):

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
    ):
        super().__init__(name, llm, system_prompt, config)
        self.tool_registry: Optional[ToolRegistry] = None
        self.max_steps = 5

    def run(self, input_text: str, **kwargs) -> str:
        raise NotImplementedError("ReActAgent.run 需要由子类实现")

    def _parse_output(self, text: str) -> Tuple[str, Optional[str]]:
        thought_match = re.search(r"Thought:\s*(.+?)(?=\n(?:Thought|Action|$))", text, re.DOTALL)
        action_match = re.search(r"Action:\s*(.+?)(?:\n|$)", text, re.DOTALL)

        thought = thought_match.group(1).strip() if thought_match else ""
        action = action_match.group(1).strip() if action_match else None
        return thought, action

    def _parse_action(self, action: str) -> Tuple[str, str]:
        match = re.match(r"(\w+)\[(.+)\]", action.strip())
        if match:
            return match.group(1), match.group(2)
        return action, ""

    def _parse_action_input(self, action: str) -> str:
        match = re.match(r"Finish\[(.+)\]", action.strip())
        if match:
            return match.group(1)
        return action.replace("Finish[", "").rstrip("]").strip()
