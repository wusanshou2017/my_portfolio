"""
RAGTool - 检索增强生成工具
通过 BaseTool 的 run() 接口提供文档管理、检索和问答操作。
支持 actions: add_text, add_document, search, ask, stats, clear
"""
import os
from typing import Dict, Any, Optional, List
from ..base import BaseTool


class RAGTool(BaseTool):
    """RAG 工具：基于关键词匹配的轻量检索增强生成"""

    def __init__(
        self,
        knowledge_base_path: str = "./rag_kb",
        rag_namespace: str = "default",
    ):
        self.knowledge_base_path = knowledge_base_path
        self.rag_namespace = rag_namespace
        # 内存中的文档存储：{doc_id: {"text": str, "chunks": List[str], "metadata": dict}}
        self._documents: Dict[str, Dict[str, Any]] = {}

    @property
    def name(self) -> str:
        return "rag"

    @property
    def description(self) -> str:
        return "RAG检索增强工具，支持文档添加、知识检索和智能问答"

    def run(self, params) -> str:
        """
        统一执行接口。
        params: {"action": "search|add_text|add_document|ask|stats|clear", ...}
        """
        if isinstance(params, str):
            params = {"action": params}

        action = params.get("action", "stats")
        return self._dispatch(action, params)

    def _dispatch(self, action: str, params: Dict[str, Any]) -> str:
        handler = {
            "add_text": self._action_add_text,
            "add_document": self._action_add_document,
            "search": self._action_search,
            "ask": self._action_ask,
            "stats": self._action_stats,
            "clear": self._action_clear,
        }.get(action)

        if not handler:
            return f"错误：不支持的操作 '{action}'"

        try:
            return handler(params)
        except Exception as e:
            return f"错误：{e}"

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 100) -> List[str]:
        """简单文本分块"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - overlap
        return chunks

    def _search_chunks(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """在所有文档块中搜索匹配"""
        query_lower = query.lower()
        scored = []

        for doc_id, doc in self._documents.items():
            for i, chunk in enumerate(doc.get("chunks", [])):
                chunk_lower = chunk.lower()
                # 简单的词频匹配得分
                score = sum(1 for word in query_lower.split() if word in chunk_lower)
                if score > 0:
                    scored.append({
                        "doc_id": doc_id,
                        "chunk_index": i,
                        "chunk": chunk,
                        "score": score,
                    })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    def _action_add_text(self, params: Dict[str, Any]) -> str:
        """添加纯文本到知识库"""
        text = params.get("text", "")
        document_id = params.get("document_id", "")
        chunk_size = int(params.get("chunk_size", 500))
        chunk_overlap = int(params.get("chunk_overlap", 100))

        if not document_id:
            document_id = f"doc_{len(self._documents) + 1}"

        chunks = self._chunk_text(text, chunk_size, chunk_overlap)
        self._documents[document_id] = {
            "text": text,
            "chunks": chunks,
            "metadata": {k: v for k, v in params.items()
                         if k not in ("action", "text", "document_id", "chunk_size", "chunk_overlap")},
        }
        return f"✅ 已添加文档 '{document_id}' ({len(chunks)} 个文本块)"

    def _action_add_document(self, params: Dict[str, Any]) -> str:
        """添加文件到知识库"""
        file_path = params.get("file_path", "")
        document_id = params.get("document_id", "")

        if not os.path.exists(file_path):
            return f"错误：文件不存在 '{file_path}'"

        if not document_id:
            document_id = os.path.splitext(os.path.basename(file_path))[0]

        # 读取文件内容
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            return f"错误：无法读取文件 '{file_path}'（编码问题）"

        return self._action_add_text({
            "text": text,
            "document_id": document_id,
            "chunk_size": params.get("chunk_size", 500),
            "chunk_overlap": params.get("chunk_overlap", 100),
        })

    def _action_search(self, params: Dict[str, Any]) -> str:
        """搜索知识库"""
        query = params.get("query", "")
        limit = int(params.get("limit", 5))

        results = self._search_chunks(query, limit)

        if not results:
            return f"未找到与 '{query}' 相关的内容。"

        lines = [f"🔍 搜索结果 (query: '{query}'):"]
        for i, r in enumerate(results, 1):
            preview = r["chunk"][:150].replace("\n", " ")
            lines.append(f"  {i}. [{r['doc_id']}] (score={r['score']}) {preview}...")
        return "\n".join(lines)

    def _action_ask(self, params: Dict[str, Any]) -> str:
        """基于知识库回答问题"""
        question = params.get("question", "")
        limit = int(params.get("limit", 5))

        results = self._search_chunks(question, limit)

        if not results:
            return f"知识库中没有找到与 '{question}' 相关的内容。"

        # 拼接相关片段作为答案
        lines = [f"💬 基于知识库回答 '{question}':\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"参考 {i} ({r['doc_id']}):\n{r['chunk'][:300]}")
            if len(r["chunk"]) > 300:
                lines.append("...")
            lines.append("")

        return "\n".join(lines)

    def _action_stats(self, params: Dict[str, Any]) -> str:
        """统计信息"""
        total_chunks = sum(len(d["chunks"]) for d in self._documents.values())
        lines = [f"📊 RAG 知识库统计 (命名空间: {self.rag_namespace}):"]
        lines.append(f"  文档数: {len(self._documents)}")
        lines.append(f"  文本块总数: {total_chunks}")
        return "\n".join(lines)

    def _action_clear(self, params: Dict[str, Any]) -> str:
        """清空知识库"""
        self._documents.clear()
        return "✅ 已清空知识库"
