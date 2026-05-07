import os
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv
from typing import List, Dict

load_dotenv()

class HelloAgentsLLMAsync:
    """
    为本书 "Hello Agents" 定制的异步LLM客户端。
    使用 AsyncOpenAI 实现非阻塞调用，适合高并发场景。
    """
    def __init__(self, model: str = None, apiKey: str = None, baseUrl: str = None, timeout: int = None):
        self.model = model or os.getenv("LLM_MODEL_ID")
        apiKey = apiKey or os.getenv("LLM_API_KEY")
        baseUrl = baseUrl or os.getenv("LLM_BASE_URL")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))

        if not all([self.model, apiKey, baseUrl]):
            raise ValueError("模型ID、API密钥和服务地址必须被提供或在.env文件中定义。")

        self.client = AsyncOpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout)

    async def think(self, messages: List[Dict[str, str]], temperature: float = 0) -> str:
        """
        异步调用大语言模型，流式接收响应。
        调用时使用 await，不会阻塞事件循环。
        """
        print(f"🧠 正在调用 {self.model} 模型...")
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )

            print("✅ 大语言模型响应成功:")
            collected_content = []
            async for chunk in response:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)
                collected_content.append(content)
            print()
            return "".join(collected_content)

        except Exception as e:
            print(f"❌ 调用LLM API时发生错误: {e}")
            return None

    async def think_batch(self, messages_list: List[List[Dict[str, str]]], temperature: float = 0) -> List[str]:
        """
        并发调用多次LLM，适合同时处理多个请求的场景。
        """
        tasks = [self.think(msgs, temperature) for msgs in messages_list]
        return await asyncio.gather(*tasks)


if __name__ == '__main__':
    async def main():
        try:
            llmClient = HelloAgentsLLMAsync()

            exampleMessages = [
                {"role": "system", "content": "You are a helpful assistant that writes Python code."},
                {"role": "user", "content": "写一个快速排序算法"}
            ]

            print("--- 单次调用 ---")
            responseText = await llmClient.think(exampleMessages)
            if responseText:
                print("\n\n--- 完整模型响应 ---")
                print(responseText)

            print("\n\n--- 并发调用 ---")
            batchMessages = [
                [
                    {"role": "system", "content": "You are a Python expert."},
                    {"role": "user", "content": "写一个桶排序算法并且解释它的原理"}
                ],
                [
                    {"role": "system", "content": "You are a Python expert."},
                    {"role": "user", "content": "写一个快速排序算法并且解释下它的原理"}
                ],
            ]
            results = await llmClient.think_batch(batchMessages)
            for i, result in enumerate(results):
                print(f"\n请求{i+1}结果: {result}")

        except ValueError as e:
            print(e)

    asyncio.run(main())


