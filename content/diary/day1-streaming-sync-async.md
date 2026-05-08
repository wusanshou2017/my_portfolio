---
title: hello-agent 学习第1天：流式响应、同步与异步
date: 2026-05-07
tags: [AI, LLM, Python, OpenAI]
description: 学习了 OpenAI API 的流式调用原理，以及同步和异步的区别，深入分析了 OpenAI SDK 源码。
---
## 理解流式响应和同步/异步

今天学习了 `Hello Agents` 书中第4章的 LLM 客户端代码，之前一直觉得流式和 async 异步有关，现在理解了它们是完全独立的两个概念。

## 同步版代码（llm_client.py）

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

## 异步版代码（llm_client_async.py）

```python
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
```

## 同步版 vs 异步版的关键区别

| 同步版                                       | 异步版                                             |
| -------------------------------------------- | -------------------------------------------------- |
| `from openai import OpenAI`                | `from openai import AsyncOpenAI`                 |
| `def think()`                              | `async def think()`                              |
| `self.client.chat.completions.create(...)` | `await self.client.chat.completions.create(...)` |
| `for chunk in response`                    | `async for chunk in response`                    |

异步版额外加了一个 `think_batch()` 方法，用 `asyncio.gather()` 同时并发调用多个请求。

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

不加 `stream=True` 时，API 会等模型全部生成完才一次性返回整个结果。加了之后，API 会在生成过程中一个字一个字地推过来，客户端用 `for chunk in response` 逐块接收：

```python
for chunk in response:
    content = chunk.choices[0].delta.content or ""
    print(content, end="", flush=True)  # 每收到一小块就立即打印
```

就像看视频"边下载边播"，而不是"全部下完再看"。

## 同步 vs 异步

这段代码虽然是流式输出，但它本身是**同步阻塞**的。

|          | 同步 (Sync)                     | 异步 (Async)                              |
| -------- | ------------------------------- | ----------------------------------------- |
| 特点     | 调用 API 时程序**卡住等** | 调用 API 时程序**可以继续干别的事** |
| 关键字   | `def`                         | `async def`                             |
| 等待方式 | 直接等结果返回                  | `await`                                 |
| 适用场景 | 简单脚本、CLI 工具              | Web 服务器、高并发                        |

## asyncio.gather() 并发原理

异步版的 `think_batch()` 方法：

```python
async def think_batch(self, messages_list, temperature=0):
    tasks = [self.think(msgs, temperature) for msgs in messages_list]
    return await asyncio.gather(*tasks)
```

第一行只是创建协程任务（写下待办事项，还没执行）。第二行 `asyncio.gather()` 把所有任务同时交给事件循环并发执行。

对比同步的做法：

```
同步（一个一个排队等）：
请求1 ████████████ 完成（等了3秒）
请求2 ████████████ 完成（又等了3秒）
总共：6秒

异步并发（同时进行）：
请求1 ████████████ 完成
请求2 ████████████ 完成
总共：3秒（因为同时跑）
```

两个请求同时发出，总耗时约等于最慢那个请求的时间，而不是所有请求时间之和。

## 并发时为什么输出会交错？

`asyncio.gather()` 让两个 `think()` 同时运行，两个都在执行流式打印，共用同一个 stdout，所以输出混在一起了。

原因是 asyncio 事件循环的任务切换机制：

```
时刻1: 任务1 await 收到 chunk → 打印 "装" → await 下一个chunk
时刻2: 任务2 await 收到 chunk → 打印 "生" → await 下一个chunk
时刻3: 任务1 await 收到 chunk → 打印 "饰" → await 下一个chunk
时刻4: 任务2 await 收到 chunk → 打印 "成" → await 下一个chunk
...
```

每个 `await` 都是一次让出控制权的机会。两个任务交替执行，共用同一个 stdout，所以输出就混在一起了。实际输出不是严格的逐字交替，而是取决于网络数据到达时机和 chunk 大小。

## 深入源码：流式和 async 的关系

看了 OpenAI SDK 的源码（`openai/resources/chat/completions/completions.py`），`AsyncCompletions.create()` 的实际实现：

```python
async def create(self, ...) -> ChatCompletion | AsyncStream[ChatCompletionChunk]:
    return await self._post(
        "/chat/completions",
        body=...,
        stream=stream or False,                    # 把 stream 参数传给底层
        stream_cls=AsyncStream[ChatCompletionChunk],  # 流式用 AsyncStream
    )
```

源码通过 Python 的 `@overload` 装饰器定义了3个签名：

| overload | stream 参数                          | 返回类型                                     |
| -------- | ------------------------------------ | -------------------------------------------- |
| 第1个    | `stream: Optional[Literal[False]]` | `ChatCompletion`（一次性返回）             |
| 第2个    | `stream: Literal[True]`            | `AsyncStream[ChatCompletionChunk]`（流式） |
| 第3个    | `stream: bool`                     | `ChatCompletion                              |

实际的方法体只有一个，根据 `stream` 的值决定走哪条路。流程图：

```
                AsyncCompletions.create()
                       │
                await self._post()
                       │
          ┌────────────┴────────────┐
          │                         │
    stream=False              stream=True
          │                         │
    返回 ChatCompletion      返回 AsyncStream
    (整个结果一次性给)        (一个chunk一个chunk给)
          │                         │
    都是 await 出来的          async for 遍历
```

## 总结

- **流式** = 输出方式（一点点给 vs 一次性给）
- **同步/异步** = 执行方式（等不等 vs 同时干别的）
- 它们互不影响，是两个完全独立的维度
- 同步版代码：**流式 + 同步** = 一边打字一边输出，但输出期间程序不能干别的
- 异步版代码：**流式 + 异步** = 一边打字一边输出，且等待期间可以干别的事
