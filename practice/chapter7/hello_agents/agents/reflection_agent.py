from typing import Optional, Dict
from ..core.agent import Agent
from ..core.llm import HelloAgentsLLM
from ..core.config import Config
from ..core.message import Message


DEFAULT_PROMPTS = {
    "initial": "请完成以下任务：{task}",
    "reflect": "请审查以下内容，指出不足之处：\n任务：{task}\n内容：{content}",
    "refine": "请根据反馈优化内容：\n任务：{task}\n反馈：{feedback}",
}


class ReflectionAgent(Agent):

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        custom_prompts: Optional[Dict[str, str]] = None,
        max_reflections: int = 2,
    ):
        super().__init__(name, llm, system_prompt, config)
        self.prompts = custom_prompts or DEFAULT_PROMPTS
        self.max_reflections = max_reflections

    def run(self, input_text: str, **kwargs) -> str:
        self._do_reflection(input_text, kwargs)
        final = self._history[-1].content if self._history else ""
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final, "assistant"))
        return final

    def _do_reflection(self, task: str, kwargs: dict) -> None:
        prompt = self.prompts["initial"].format(task=task)
        initial = self.llm.invoke([{"role": "user", "content": prompt}], **kwargs)
        self._history.append(Message(prompt, "user"))
        self._history.append(Message(initial, "assistant"))

        for _ in range(self.max_reflections):
            reflect_prompt = self.prompts["reflect"].format(task=task, content=initial)
            feedback = self.llm.invoke([{"role": "user", "content": reflect_prompt}], **kwargs)

            refine_prompt = self.prompts["refine"].format(task=task, feedback=feedback)
            refined = self.llm.invoke(
                [{"role": "user", "content": refine_prompt}],
                **kwargs,
            )

            self._history.append(Message(reflect_prompt, "user"))
            self._history.append(Message(feedback, "assistant"))
            self._history.append(Message(refine_prompt, "user"))
            self._history.append(Message(refined, "assistant"))

            initial = refined
