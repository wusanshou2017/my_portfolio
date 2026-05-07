---
title: 学习日记第4天：流式响应、同步与异步
date: 2026-05-01
tags: [AI, LLM, Python, OpenAI]
description: 学习了 OpenAI API 的流式调用原理，以及同步和异步的区别。
---

## 今天的主题：理解流式响应和同步/异步

今天学习了 `Hello Agents` 书中第4章的 LLM 客户端代码，搞懂了流式响应的原理，以及同步和异步的区别。

## 核心代码

```python
import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict

# 加载 .env 文件中的环境变量
load_dotenv()

class HelloAgentsLLM:
    """
    为本书 "Hello Agents" 定制的LLM客户端。
    它用于调用任何兼容OpenAI接口的服务，并默认使用流式响应。
    """
    def __init__(self, model: str = None, apiKey: str = None, baseUrl: str = None, timeout: int = None):
        """
        初始化客户端。优先使用传入参数，如果未提供，则从环境变量加载。
        """
        self.model = model or os.getenv("LLM_MODEL_ID")
        apiKey = apiKey or os.getenv("LLM_API_KEY")
        baseUrl = baseUrl or os.getenv("LLM_BASE_URL")
        timeout = timeout or int(os.getenv("LLM_TIMEOUT", 60))
        
        if not all([self.model, apiKey, baseUrl]):
            raise ValueError("模型ID、API密钥和服务地址必须被提供或在.env文件中定义。")

        self.client = OpenAI(api_key=apiKey, base_url=baseUrl, timeout=timeout)

    def think(self, messages: List[Dict[str, str]], temperature: float = 0) -> str:
        """
        调用大语言模型进行思考，并返回其响应。
        """
        print(f"🧠 正在调用 {self.model} 模型...")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )
            
            # 处理流式响应
            print("✅ 大语言模型响应成功:")
            collected_content = []
            for chunk in response:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)
                collected_content.append(content)
            print()  # 在流式输出结束后换行
            return "".join(collected_content)

        except Exception as e:
            print(f"❌ 调用LLM API时发生错误: {e}")
            return None

# --- 客户端使用示例 ---
if __name__ == '__main__':
    try:
        llmClient = HelloAgentsLLM()
        
        exampleMessages = [
            {"role": "system", "content": "You are a helpful assistant that writes Python code."},
            {"role": "user", "content": "写一个快速排序算法"}
        ]
        
        print("--- 调用LLM ---")
        responseText = llmClient.think(exampleMessages)
        if responseText:
            print("\n\n--- 完整模型响应 ---")
            print(responseText)

    except ValueError as e:
        print(e)
```

## 为什么是流式的？

关键在于 `create()` 方法中的 `stream=True` 参数：

```python
response = self.client.chat.completions.create(
    model=self.model,
    messages=messages,
    temperature=temperature,
    stream=True,  # 开启流式
)
```

不加 `stream=True` 时，API 会等模型**全部生成完**才一次性返回整个结果。加了之后，API 会在生成过程中**一个字一个字地推过来**，客户端用 `for chunk in response` 逐块接收：

```python
for chunk in response:
    content = chunk.choices[0].delta.content or ""
    print(content, end="", flush=True)  # 每收到一小块就立即打印
```

就像看视频"边下载边播"，而不是"全部下完再看"。

## 同步 vs 异步

这段代码虽然是流式输出，但它本身是**同步阻塞**的。

### 对比

| | 同步 (Sync) | 异步 (Async) |
|--|--|--|
| 这段代码 | 是同步 | 不是 |
| 特点 | 调用 API 时程序**卡住等** | 调用 API 时程序**可以继续干别的事** |
| 关键字 | `def` | `async def` |
| 等待方式 | 直接等结果返回 | `await` |
| 适用场景 | 简单脚本、CLI 工具 | Web 服务器、高并发 |

### 如果要改成异步

需要用 `AsyncOpenAI` + `async/await`：

```python
from openai import AsyncOpenAI

class HelloAgentsLLMAsync:
    def __init__(self, ...):
        self.client = AsyncOpenAI(api_key=apiKey, base_url=baseUrl)
    
    async def think(self, messages):
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
        )
        async for chunk in response:
            content = chunk.choices[0].delta.content or ""
            print(content, end="", flush=True)
```

## 总结

- **流式** = 输出方式（一点点给 vs 一次性给）
- **同步/异步** = 执行方式（等不等 vs 同时干别的）
- 这段代码：**流式 + 同步** = 一边打字一边输出，但输出期间程序不能干别的

## 明天的计划

- 学习 Agent 的基本概念
- 了解 ReAct 框架
- 动手实现一个简单的 Agent
