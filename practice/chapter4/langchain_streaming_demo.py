"""
LangChain Streaming 完整教程学习脚本
来源: https://docs.langchain.com/oss/python/langchain/streaming

本脚本演示了 LangChain 流式系统的所有核心模式:
1.  Agent Progress (updates)             - 获取 agent 每一步的状态更新
2.  LLM Tokens (messages)                - 逐 token 流式输出 LLM 响应
3.  Custom Updates (custom)              - 从工具中发送自定义的实时更新
4.  Multiple Modes                       - 同时使用多种流式模式
5.  Streaming Tool Calls                 - 流式输出 tool call 生成过程 + 完成后的解析结果
5b. Accessing Completed Messages         - 在流式循环中聚合 chunks 获取完整消息
6.  Streaming Thinking/Reasoning Tokens  - 流式输出模型的思考/推理过程
7.  Disable Streaming                    - 禁用特定模型的流式输出
8.  v2 Streaming Format                  - 使用 version="v2" 的统一输出格式
9.  Streaming with Human-in-the-Loop     - 人机协作场景下的流式输出（需额外依赖）
10. Streaming from Sub-agents            - 多 Agent 场景下的流式输出（需额外依赖）
11. 基础 LLM 流式                        - 非 Agent 场景下直接流式调用
"""

import os
from typing import Any, Literal
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, AIMessageChunk, AnyMessage, ToolMessage
from langchain_core.runnables import Runnable
from langgraph.config import get_stream_writer
from pydantic import BaseModel

load_dotenv()

# ============================================================
# 0. 基础配置 - 从环境变量加载
# ============================================================
API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL_ID = os.getenv("LLM_MODEL_ID")

if not all([API_KEY, BASE_URL, MODEL_ID]):
    raise ValueError("请在 .env 文件中设置 LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_ID")


# ============================================================
# 1. 定义工具函数
# ============================================================
@tool
def get_weather(city: str) -> str:
    """Get weather for a given city."""
    writer = get_stream_writer()
    writer(f"Looking up data for city: {city}")
    writer(f"Acquired data for city: {city}")
    return f"It's always sunny in {city}!"


@tool
def get_population(city: str) -> str:
    """Get population for a given city."""
    writer = get_stream_writer()
    writer(f"Querying population database for: {city}")
    return f"{city} has a population of about 1 million."


# ============================================================
# 2. 创建 Agent (兼容 OpenAI 接口)
# ============================================================
def create_my_agent():
    llm = ChatOpenAI(
        model=MODEL_ID,
        api_key=API_KEY,
        base_url=BASE_URL,
        temperature=0,
    )
    agent = create_agent(
        model=llm,
        tools=[get_weather, get_population],
    )
    return agent


def create_my_llm():
    return ChatOpenAI(
        model=MODEL_ID,
        api_key=API_KEY,
        base_url=BASE_URL,
        temperature=0,
    )


# ============================================================
# 演示 1: Agent Progress (stream_mode="updates")
# 教程章节: Agent Progress
# ============================================================
def demo_agent_progress(agent):
    """
    stream_mode="updates" 会在 agent 每一步执行后发出一个事件。
    典型的流程是: LLM调用 -> 工具执行 -> LLM最终响应
    每一步都会产生一个 chunk，包含该步骤的输出。
    """
    print("=" * 60)
    print("演示 1: Agent Progress (stream_mode='updates')")
    print("=" * 60)
    print("说明: 获取 agent 每一步的状态更新，每个 chunk 对应一个 agent 步骤\n")

    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
        stream_mode="updates",
    ):
        for step, data in chunk.items():
            last_msg = data["messages"][-1]
            print(f"  步骤: {step}")
            print(f"  内容: {last_msg.content_blocks if hasattr(last_msg, 'content_blocks') else last_msg.content}")
            print()

    print("✅ Agent Progress 演示结束\n")


# ============================================================
# 演示 2: LLM Tokens (stream_mode="messages")
# 教程章节: LLM Tokens
# ============================================================
def demo_llm_tokens(agent):
    """
    stream_mode="messages" 会逐 token 流式输出 LLM 的响应。
    每个 token 是一个元组 (AIMessageChunk, metadata)。
    metadata 包含 langgraph_node 等信息，告诉你这个 token 来自哪个节点。
    """
    print("=" * 60)
    print("演示 2: LLM Tokens (stream_mode='messages')")
    print("=" * 60)
    print("说明: 逐 token 流式输出 LLM 响应，包括工具调用的参数\n")

    for token, metadata in agent.stream(
        {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
        stream_mode="messages",
    ):
        node = metadata["langgraph_node"]
        content_blocks = token.content_blocks if hasattr(token, "content_blocks") else []
        if content_blocks:
            for block in content_blocks:
                if block.get("type") == "tool_call":
                    print(f"  [{node}] 工具调用: {block.get('name')}({block.get('args', '')})")
                elif block.get("type") == "tool_call_chunk":
                    args = block.get("args", "")
                    if args:
                        print(f"  [{node}] 参数片段: {args}", end="", flush=True)
                elif block.get("type") == "text":
                    print(f"  [{node}] 文本: {block.get('text', '')}", end="", flush=True)

    print("\n\n✅ LLM Tokens 演示结束\n")


# ============================================================
# 演示 3: Custom Updates (stream_mode="custom")
# 教程章节: Custom Updates
# ============================================================
def demo_custom_updates(agent):
    """
    stream_mode="custom" 会接收工具中通过 get_stream_writer() 发送的自定义数据。
    工具可以在执行过程中发送任意格式的进度信息。
    """
    print("=" * 60)
    print("演示 3: Custom Updates (stream_mode='custom')")
    print("=" * 60)
    print("说明: 工具内部通过 get_stream_writer() 发送自定义进度信息\n")

    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
        stream_mode="custom",
    ):
        print(f"  📡 自定义更新: {chunk}")

    print("\n✅ Custom Updates 演示结束\n")


# ============================================================
# 演示 4: Multiple Modes (stream_mode=["updates", "custom"])
# 教程章节: Stream Multiple Modes
# ============================================================
def demo_multiple_modes(agent):
    """
    stream_mode 可以传入列表，同时使用多种流式模式。
    每个 chunk 是一个元组 (stream_mode, data)，
    告诉你这个 chunk 来自哪种流式模式。
    """
    print("=" * 60)
    print("演示 4: Multiple Modes (stream_mode=['updates', 'custom'])")
    print("=" * 60)
    print("说明: 同时使用 updates 和 custom 两种流式模式\n")

    for stream_mode, chunk in agent.stream(
        {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
        stream_mode=["updates", "custom"],
    ):
        if stream_mode == "custom":
            print(f"  [custom] {chunk}")
        elif stream_mode == "updates":
            for step, data in chunk.items():
                last_msg = data["messages"][-1]
                content = last_msg.content if not hasattr(last_msg, 'content_blocks') else str(last_msg.content_blocks)
                if len(content) > 100:
                    content = content[:100] + "..."
                print(f"  [updates] 步骤={step}, 内容={content}")
        print()

    print("✅ Multiple Modes 演示结束\n")


# ============================================================
# 演示 5: Streaming Tool Calls (stream_mode=["messages", "updates"])
# 教程章节: Streaming Tool Calls (基础)
# ============================================================
def demo_streaming_tool_calls(agent):
    """
    同时使用 "messages" 和 "updates" 两种模式:
    - messages: 流式输出部分 tool call JSON（LLM 正在生成工具调用参数的过程）
    - updates:  输出完成解析后的 tool call 和 tool response（工具执行结果）
    """
    print("=" * 60)
    print("演示 5: Streaming Tool Calls (stream_mode=['messages', 'updates'])")
    print("=" * 60)
    print("说明: 同时流式输出 tool call 的生成过程和完成后的解析结果\n")

    def _render_message_chunk(token: AIMessageChunk) -> None:
        if token.text:
            print(f"    [text] {token.text}", end="|")
        if token.tool_call_chunks:
            for tc in token.tool_call_chunks:
                if tc.get("name") or tc.get("args"):
                    print(f"    [tool_call_chunk] name={tc.get('name')}, args={tc.get('args', '')}", end="")
        print()

    def _render_completed_message(message: AnyMessage) -> None:
        if isinstance(message, AIMessage) and message.tool_calls:
            print(f"    ✅ 完成的 Tool Calls: {message.tool_calls}")
        if isinstance(message, ToolMessage):
            content_blocks = message.content_blocks if hasattr(message, 'content_blocks') else [{"type": "text", "text": message.content}]
            print(f"    🔧 Tool Response: {content_blocks}")

    input_message = {"role": "user", "content": "What is the weather in Boston?"}
    for chunk in agent.stream(
        {"messages": [input_message]},
        stream_mode=["messages", "updates"],
    ):
        if isinstance(chunk, tuple):
            stream_mode, data = chunk
            if stream_mode == "messages":
                token, metadata = data
                if isinstance(token, AIMessageChunk):
                    _render_message_chunk(token)
            elif stream_mode == "updates":
                for source, update in data.items():
                    if source in ("model", "tools"):
                        _render_completed_message(update["messages"][-1])
        else:
            for source, update in chunk.items():
                if source in ("model", "tools"):
                    _render_completed_message(update["messages"][-1])

    print("\n✅ Streaming Tool Calls 演示结束\n")


# ============================================================
# 演示 5b: Accessing Completed Messages (聚合 chunks)
# 教程章节: Accessing completed messages (聚合方式)
# ============================================================
def demo_accessing_completed_messages(agent):
    """
    当 completed messages 不在 state 中时，可以在流式循环中聚合 chunks。
    使用 full_message = full_message + token 累积消息，
    通过 chunk_position == "last" 判断消息结束。
    """
    print("=" * 60)
    print("演示 5b: Accessing Completed Messages (聚合 chunks)")
    print("=" * 60)
    print("说明: 在流式循环中聚合 AIMessageChunk 获取完整消息\n")

    def _render_message_chunk(token: AIMessageChunk) -> None:
        if token.text:
            print(token.text, end="|")
        if token.tool_call_chunks:
            print(token.tool_call_chunks)

    full_message = None
    input_message = {"role": "user", "content": "What is the weather in Boston?"}
    for chunk in agent.stream(
        {"messages": [input_message]},
        stream_mode=["messages", "updates"],
    ):
        if isinstance(chunk, tuple):
            stream_mode, data = chunk
            if stream_mode == "messages":
                token, metadata = data
                if isinstance(token, AIMessageChunk):
                    _render_message_chunk(token)
                    full_message = token if full_message is None else full_message + token
                    if hasattr(token, 'chunk_position') and token.chunk_position == "last":
                        if full_message.tool_calls:
                            print(f"\n    ✅ 聚合得到的 Tool Calls: {full_message.tool_calls}")
                        full_message = None
            elif stream_mode == "updates":
                for source, update in data.items():
                    if source == "tools":
                        last_msg = update["messages"][-1]
                        if isinstance(last_msg, ToolMessage):
                            print(f"    🔧 Tool Response: {last_msg.content}")

    print("\n✅ Accessing Completed Messages 演示结束\n")


# ============================================================
# 演示 6: Streaming Thinking / Reasoning Tokens
# 教程章节: Streaming thinking / reasoning tokens
# ============================================================
def demo_streaming_thinking_tokens(agent):
    """
    流式输出模型的思考/推理过程。
    通过过滤 content_blocks 中 type == "reasoning" 的块来获取推理内容。
    LangChain 会将不同供应商的推理格式统一为标准的 "reasoning" 类型。

    注意: 需要模型支持 reasoning/thinking 模式。
    """
    print("=" * 60)
    print("演示 6: Streaming Thinking / Reasoning Tokens")
    print("=" * 60)
    print("说明: 过滤 content_blocks 中 type=='reasoning' 获取推理过程\n")

    for token, metadata in agent.stream(
        {"messages": [{"role": "user", "content": "What is 15 * 27?"}]},
        stream_mode="messages",
    ):
        if not isinstance(token, AIMessageChunk):
            continue
        content_blocks = token.content_blocks if hasattr(token, "content_blocks") else []
        reasoning_blocks = [b for b in content_blocks if b.get("type") == "reasoning"]
        text_blocks = [b for b in content_blocks if b.get("type") == "text"]
        if reasoning_blocks:
            for r in reasoning_blocks:
                reasoning_text = r.get("reasoning", r.get("text", ""))
                if reasoning_text:
                    print(f"  [thinking] {reasoning_text}", end="", flush=True)
        if text_blocks:
            for t in text_blocks:
                print(f"  [text] {t.get('text', '')}", end="", flush=True)

    print("\n\n✅ Streaming Thinking Tokens 演示结束\n")


# ============================================================
# 演示 7: Disable Streaming
# 教程章节: Disable Streaming
# ============================================================
def demo_disable_streaming():
    """
    通过设置 streaming=False 禁用特定模型的流式输出。
    适用于:
    - 多 Agent 系统中控制哪些 Agent 流式输出
    - 混合支持和不支持流式的模型
    - 部署到 LangSmith 时不希望某些模型输出流式到客户端
    """
    print("=" * 60)
    print("演示 7: Disable Streaming")
    print("=" * 60)
    print("说明: 设置 streaming=False 禁用流式输出，模型会等待完整响应后返回\n")

    llm_no_stream = ChatOpenAI(
        model=MODEL_ID,
        api_key=API_KEY,
        base_url=BASE_URL,
        temperature=0,
        streaming=False,
    )

    print("✅ 调用 non-streaming 模型（等待完整响应）...")
    response = llm_no_stream.invoke("用一句话介绍什么是流式输出")
    print(f"  完整响应: {response.content}")
    print(f"  响应长度: {len(response.content)} 字符")
    print("\n✅ Disable Streaming 演示结束\n")


# ============================================================
# 演示 8: v2 Streaming Format
# 教程章节: v2 streaming format
# ============================================================
def demo_v2_format(agent):
    """
    使用 version="v2" 获取统一输出格式。
    每个 chunk 是一个 StreamPart dict，包含 type, ns, data 三个 key。
    不再需要解包 tuple，直接用 chunk["type"] 和 chunk["data"] 访问。
    """
    print("=" * 60)
    print("演示 8: v2 Streaming Format (version='v2')")
    print("=" * 60)
    print("说明: 统一的 StreamPart dict 格式，用 chunk['type'] 和 chunk['data'] 访问\n")

    try:
        for chunk in agent.stream(
            {"messages": [{"role": "user", "content": "What is the weather in SF?"}]},
            stream_mode=["updates", "custom"],
            version="v2",
        ):
            chunk_type = chunk["type"] if isinstance(chunk, dict) else "unknown"
            data = chunk.get("data", chunk)
            print(f"  chunk type: {chunk_type}")
            if chunk_type == "custom":
                print(f"  [custom] {data}")
            elif chunk_type == "updates":
                if isinstance(data, dict):
                    for step, update in data.items():
                        last_msg = update["messages"][-1] if "messages" in update else update
                        content = str(last_msg.content_blocks if hasattr(last_msg, 'content_blocks') else last_msg.content)
                        if len(content) > 100:
                            content = content[:100] + "..."
                        print(f"  [updates] 步骤={step}, 内容={content}")
            print()
    except TypeError as e:
        print(f"  ⚠️ v2 格式需要 LangGraph >= 1.1，当前环境可能不支持: {e}\n")

    print("✅ v2 Streaming Format 演示结束\n")


# ============================================================
# 演示 9: Streaming with Human-in-the-Loop
# 教程章节: Streaming with human-in-the-loop
# 注意: 需要 HumanInTheLoopMiddleware 等额外依赖，演示为概念代码
# ============================================================
def demo_human_in_the_loop_concept():
    """
    人机协作场景下的流式输出概念演示。

    核心思路:
    1. 配置 HumanInTheLoopMiddleware 中间件，指定哪些工具需要人工审批
    2. 配置 checkpointer 保存状态
    3. 在 stream 循环中收集 __interrupt__ 事件
    4. 人工做出决策后，用 Command(resume=decisions) 恢复执行

    以下为概念代码，实际运行需要额外依赖:
    """
    print("=" * 60)
    print("演示 9: Streaming with Human-in-the-Loop (概念代码)")
    print("=" * 60)
    print("说明: 人机协作场景，工具调用前暂停等待人工审批\n")

    concept_code = '''
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, Interrupt

checkpointer = InMemorySaver()
agent = create_agent(
    model=llm,
    tools=[get_weather],
    middleware=[HumanInTheLoopMiddleware(interrupt_on={"get_weather": True})],
    checkpointer=checkpointer,
)

config = {"configurable": {"thread_id": "some_id"}}
interrupts = []
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "What is the weather in Boston?"}]},
    config=config,
    stream_mode=["messages", "updates"],
):
    # 处理流式 token
    if chunk["type"] == "messages":
        token, metadata = chunk["data"]
        ...
    # 收集中断事件
    elif chunk["type"] == "updates":
        for source, update in chunk["data"].items():
            if source == "__interrupt__":
                interrupts.extend(update)
                # 展示需要审批的工具调用
                _render_interrupt(update[0])

# 人工做出决策
decisions = {interrupt.id: {"decisions": [{"type": "approve"}]} for interrupt in interrupts}

# 用 Command 恢复执行
for chunk in agent.stream(
    Command(resume=decisions),
    config=config,
    stream_mode=["messages", "updates"],
):
    ...  # 流式循环不变
'''
    print(concept_code)
    print("✅ Human-in-the-Loop 概念演示结束\n")


# ============================================================
# 演示 10: Streaming from Sub-agents
# 教程章节: Streaming from sub-agents
# 注意: 需要多 Agent 配置，演示为概念代码
# ============================================================
def demo_sub_agents_concept():
    """
    多 Agent 场景下的流式输出概念演示。

    核心思路:
    1. 给每个 Agent 设置 name 参数
    2. 使用 subgraphs=True 开启子图流式
    3. 通过 metadata["lc_agent_name"] 区分 token 来自哪个 Agent

    以下为概念代码:
    """
    print("=" * 60)
    print("演示 10: Streaming from Sub-agents (概念代码)")
    print("=" * 60)
    print("说明: 多 Agent 场景，通过 lc_agent_name 区分 token 来源\n")

    concept_code = '''
from langchain.chat_models import init_chat_model

# 创建子 Agent
weather_agent = create_agent(
    model=init_chat_model("openai:gpt-5.4"),
    tools=[get_weather],
    name="weather_agent",  # 设置 Agent 名称
)

# 子 Agent 作为工具被主 Agent 调用
def call_weather_agent(query: str) -> str:
    result = weather_agent.invoke({"messages": [{"role": "user", "content": query}]})
    return result["messages"][-1].text

# 创建主 Agent
agent = create_agent(
    model=init_chat_model("openai:gpt-5.4"),
    tools=[call_weather_agent],
    name="supervisor",  # 设置主 Agent 名称
)

# 流式输出时追踪当前活跃的 Agent
current_agent = None
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "What is the weather in Boston?"}]},
    stream_mode=["messages", "updates"],
    subgraphs=True,  # 开启子图流式
):
    if chunk["type"] == "messages":
        token, metadata = chunk["data"]
        # 通过 lc_agent_name 区分 Agent
        agent_name = metadata.get("lc_agent_name")
        if agent_name and agent_name != current_agent:
            print(f"\\n🤖 {agent_name}: ")
            current_agent = agent_name
        # 渲染 token...
'''
    print(concept_code)
    print("✅ Sub-agents 概念演示结束\n")


# ============================================================
# 演示 11: 基础 LLM 流式 (非 Agent 场景)
# ============================================================
def demo_basic_llm_stream():
    """
    不使用 Agent，直接对 LLM 进行流式调用。
    这与 OpenAI SDK 的流式调用更接近。
    """
    print("=" * 60)
    print("演示 11: 基础 LLM 流式 (非 Agent 场景)")
    print("=" * 60)
    print("说明: 直接使用 ChatOpenAI 的 stream 方法，逐 token 输出\n")

    llm = create_my_llm()

    print("✅ 模型响应:")
    collected = []
    for chunk in llm.stream("用一句话介绍什么是流式输出"):
        content = chunk.content or ""
        print(content, end="", flush=True)
        collected.append(content)
    print()
    print(f"\n完整响应长度: {len(''.join(collected))} 字符")
    print("\n✅ 基础 LLM 流式演示结束\n")


# ============================================================
# 主函数
# ============================================================
if __name__ == "__main__":
    print("\n" + "#" * 60)
    print("#  LangChain Streaming 完整教程学习脚本")
    print("#  来源: https://docs.langchain.com/oss/python/langchain/streaming")
    print("#" * 60 + "\n")

    print("⚠️  注意: Agent 相关演示需要支持 tool_calling 的模型")
    print("⚠️  演示 9 (Human-in-the-Loop) 和 演示 10 (Sub-agents) 为概念代码\n")

    agent = None
    try:
        agent = create_my_agent()

        agent_demos = [
            ("1. Agent Progress", demo_agent_progress),
            ("2. LLM Tokens", demo_llm_tokens),
            ("3. Custom Updates", demo_custom_updates),
            ("4. Multiple Modes", demo_multiple_modes),
            ("5. Streaming Tool Calls", demo_streaming_tool_calls),
            ("5b. Accessing Completed Messages", demo_accessing_completed_messages),
            ("6. Streaming Thinking Tokens", demo_streaming_thinking_tokens),
        ]
        for name, demo_func in agent_demos:
            try:
                demo_func(agent)
            except Exception as e:
                print(f"⚠️  {name} 演示失败: {e}\n")
    except Exception as e:
        print(f"⚠️  Agent 创建失败（模型可能不支持 tool calling）: {e}\n")

    standalone_demos = [
        ("7. Disable Streaming", demo_disable_streaming),
        ("8. v2 Streaming Format", lambda: demo_v2_format(agent) if agent else print("  ⚠️ 跳过: Agent 未创建\n")),
        ("9. Human-in-the-Loop (概念)", demo_human_in_the_loop_concept),
        ("10. Sub-agents (概念)", demo_sub_agents_concept),
        ("11. 基础 LLM 流式", demo_basic_llm_stream),
    ]
    for name, demo_func in standalone_demos:
        try:
            demo_func()
        except Exception as e:
            print(f"⚠️  {name} 演示失败: {e}\n")

    print("#" * 60)
    print("#  所有演示完成")
    print("#" * 60)
