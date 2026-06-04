from typing import Optional, Dict
from hello_agents import ReflectionAgent, HelloAgentsLLM, Config, Message


class MyReflectionAgent(ReflectionAgent):
    """
    重写的 Reflection Agent
    生成→反思→优化 循环，支持逐步打印
    """

    def __init__(
        self,
        name: str,
        llm: HelloAgentsLLM,
        system_prompt: Optional[str] = None,
        config: Optional[Config] = None,
        custom_prompts: Optional[Dict[str, str]] = None,
        max_reflections: int = 2,
    ):
        super().__init__(name, llm, system_prompt, config, custom_prompts, max_reflections)
        print(f"✅ {name} 初始化完成，最大反思轮数: {max_reflections}")

    def run(self, input_text: str, **kwargs) -> str:
        print(f"\n🤖 {self.name} 开始处理: {input_text[:100]}")

        # 阶段1：生成初稿
        print("\n✍️ 阶段1：生成初稿...")
        prompt = self.prompts["initial"].format(task=input_text)
        initial = self.llm.invoke([{"role": "user", "content": prompt}], **kwargs)
        self._history.append(Message(prompt, "user"))
        self._history.append(Message(initial, "assistant"))
        print(f"  📝 初稿: {initial[:200]}")

        # 阶段2：反思循环
        for i in range(self.max_reflections):
            print(f"\n🔄 反思轮次 {i+1}/{self.max_reflections}...")

            # 2a: 审查
            print("  🔍 审查中...")
            reflect_prompt = self.prompts["reflect"].format(task=input_text, content=initial)
            feedback = self.llm.invoke([{"role": "user", "content": reflect_prompt}], **kwargs)
            print(f"  💬 反馈: {feedback[:200]}")

            # 2b: 优化
            print("  ✏️ 优化中...")
            refine_prompt = self.prompts["refine"].format(task=input_text, feedback=feedback)
            refined = self.llm.invoke([{"role": "user", "content": refine_prompt}], **kwargs)

            self._history.append(Message(reflect_prompt, "user"))
            self._history.append(Message(feedback, "assistant"))
            self._history.append(Message(refine_prompt, "user"))
            self._history.append(Message(refined, "assistant"))
            print(f"  📝 优化后: {refined[:200]}")

            initial = refined

        final = self._history[-1].content if self._history else ""
        self.add_message(Message(input_text, "user"))
        self.add_message(Message(final, "assistant"))

        print(f"\n🎯 最终结果: {final[:300]}")
        return final
