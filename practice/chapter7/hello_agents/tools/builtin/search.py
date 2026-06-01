import os
from ..base import BaseTool


def search(query: str) -> str:
    print(f"🔍 正在执行搜索: {query}")
    api_key = os.getenv("SERPAPI_API_KEY") or os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "错误：未配置搜索API密钥（SERPAPI_API_KEY 或 TAVILY_API_KEY）。"

    if os.getenv("SERPAPI_API_KEY"):
        return _search_serpapi(query, api_key)
    elif os.getenv("TAVILY_API_KEY"):
        return _search_tavily(query, api_key)
    return "错误：没有可用的搜索API密钥。"


def _search_serpapi(query: str, api_key: str) -> str:
    try:
        from serpapi import Client
        client = Client(api_key=api_key)
        results = client.search(
            params={"engine": "google", "q": query, "api_key": api_key, "gl": "cn", "hl": "zh-cn"}
        ).as_dict()

        if "answer_box" in results and "answer" in results["answer_box"]:
            return results["answer_box"]["answer"]
        if "knowledge_graph" in results and "description" in results["knowledge_graph"]:
            return results["knowledge_graph"]["description"]
        if "organic_results" in results and results["organic_results"]:
            snippets = [
                f"[{i+1}] {res.get('title', '')}\n{res.get('snippet', '')}"
                for i, res in enumerate(results["organic_results"][:3])
            ]
            return "\n\n".join(snippets)
        return f"未找到关于 '{query}' 的信息。"
    except Exception as e:
        return f"SerpApi 搜索错误: {e}"


def _search_tavily(query: str, api_key: str) -> str:
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, max_results=3)
        if response.get("answer"):
            return f"AI直接答案：{response['answer']}"
        results = []
        for i, item in enumerate(response.get("results", [])[:3], 1):
            results.append(f"[{i}] {item.get('title', '')}\n{item.get('content', '')[:200]}")
        return "\n\n".join(results) if results else "未找到结果。"
    except Exception as e:
        return f"Tavily 搜索错误: {e}"


class SearchTool(BaseTool):

    @property
    def name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return "搜索互联网信息，获取实时数据和新闻"

    def run(self, params) -> str:
        if isinstance(params, dict):
            query = params.get("query", params.get("input", ""))
        else:
            query = str(params)
        return search(query)
