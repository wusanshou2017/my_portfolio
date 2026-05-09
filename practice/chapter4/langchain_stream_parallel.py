"""
LangGraph 并行工具执行演示
使用 StateGraph 手动构建 Agent，让多个工具同时执行。

对比:
  create_agent  → 工具顺序执行（默认，安全优先）
  StateGraph    → 可以自己控制工具执行方式（并行）

关键点:
  - 用 asyncio.to_thread + asyncio.gather 并发执行多个同步工具
  - 所有工具同时启动，总耗时 ≈ 最慢的工具
  - 注意: 工具内不要用 get_stream_writer()（线程上下文丢失）
"""

import os
import time
import concurrent.futures
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.graph import StateGraph, MessagesState, START, END

load_dotenv()

API_KEY = os.getenv("LLM_API_KEY")
BASE_URL = os.getenv("LLM_BASE_URL")
MODEL_ID = os.getenv("LLM_MODEL_ID")

if not all([API_KEY, BASE_URL, MODEL_ID]):
    raise ValueError("请在 .env 文件中设置 LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_ID")


# ============================================================
# 带延时工具（模拟耗时操作）
# 注意: 并行模式下不能在工具内用 get_stream_writer()
# ============================================================
@tool
def get_weather(city: str) -> str:
    """Get weather for a given city."""
    print(f"  🌤️  开始查询 {city} 天气...（等待2秒）")
    time.sleep(2)
    print(f"  ✅ {city} 天气查询完成")
    return f"It's always sunny in {city}!"


@tool
def get_population(city: str) -> str:
    """Get population for a given city."""
    print(f"  👥 开始查询 {city} 人口...（等待3秒）")
    time.sleep(3)
    print(f"  ✅ {city} 人口查询完成")
    return f"{city} 有100万人左右."


# ============================================================
# 构建并行 Agent
# ============================================================
llm = ChatOpenAI(
    model=MODEL_ID,
    api_key=API_KEY,
    base_url=BASE_URL,
    temperature=0,
)

tools = [get_weather, get_population]
tools_by_name = {t.name: t for t in tools}
model_with_tools = llm.bind_tools(tools)


def call_model(state: MessagesState) -> dict:
    """LLM 节点：决定调用哪些工具"""
    response = model_with_tools.invoke(state["messages"])
    return {"messages": [response]}


def call_tools_parallel(state: MessagesState) -> dict:
    """工具节点：并行执行所有工具调用"""
    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {"messages": []}

    t0 = time.time()

    # 用线程池并行执行所有工具
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_tc = {}
        for tc in last_message.tool_calls:
            fn = tools_by_name[tc["name"]]
            future = executor.submit(fn.invoke, tc["args"])
            future_to_tc[future] = tc
        results = []
        for future in concurrent.futures.as_completed(future_to_tc):
            tc = future_to_tc[future]
            result = future.result()
            results.append((tc, result))

    elapsed = time.time() - t0
    print(f"\n  ⏱️  总耗时: {elapsed:.1f}秒")
    print(f"     （理论最慢: 3秒，如果是顺序执行: 2+3=5秒）\n")

    return {
        "messages": [
            ToolMessage(content=result, tool_call_id=tc["id"])
            for tc, result in results
        ]
    }


def should_continue(state: MessagesState) -> str:
    """条件路由：判断是否继续"""
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return END


# 构建图
builder = StateGraph(MessagesState)
builder.add_node("model", call_model)
builder.add_node("tools", call_tools_parallel)
builder.add_edge(START, "model")
builder.add_conditional_edges("model", should_continue, {"tools": "tools", END: END})
builder.add_edge("tools", "model")
graph = builder.compile()


# ============================================================
# 主函数
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("并行工具执行演示")
    print("=" * 60)
    print("get_population → 3秒  |  get_weather → 2秒")
    print("并行总耗时 ≈ max(3, 2) = 3秒\n")

    input_msg = {
        "role": "user",
        "content": "San Francisco的人口有多少？天气怎么样？",
    }

    for chunk in graph.stream(
        {"messages": [input_msg]},
        stream_mode="updates",
    ):
        # stream_mode="updates"（单模式）时 chunk 直接是 dict
        # 格式: {"model": {"messages": [...]}} 或 {"tools": {"messages": [...]}}
        for node_name, update in chunk.items():
            if node_name == "model":
                last = update["messages"][-1]
                if isinstance(last, AIMessage) and last.tool_calls:
                    tools_str = ", ".join(
                        f"{tc['name']}({tc['args']})"
                        for tc in last.tool_calls
                    )
                    print(f"\n  🤖 模型决定调用: [{tools_str}]\n")
                elif isinstance(last, AIMessage) and last.content:
                    print(f"\n  🤖 最终回复: {last.content[:80]}...")
