import os
from typing import Optional, Iterator, List, Dict
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class HelloAgentsLLM:
    """
    统一LLM客户端，兼容OpenAI接口。
    支持 provider 自动检测和手动指定。
    """

    PROVIDER_PATTERNS = {
        "deepseek": {"base_url": "https://api.deepseek.com/v1", "env_key": "DEEPSEEK_API_KEY"},
        "openai": {"base_url": "https://api.openai.com/v1", "env_key": "OPENAI_API_KEY"},
        "zhipu": {"base_url": "https://open.bigmodel.cn/api/paas/v4", "env_key": "ZHIPU_API_KEY"},
        "qwen": {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "env_key": "QWEN_API_KEY"},
        "moonshot": {"base_url": "https://api.moonshot.cn/v1", "env_key": "MOONSHOT_API_KEY"},
    }

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        provider: Optional[str] = "auto",
        **kwargs
    ):
        self.provider = provider

        if provider == "auto":
            api_key = api_key or os.getenv("LLM_API_KEY")
            base_url = base_url or os.getenv("LLM_BASE_URL")
            self.model = model or os.getenv("LLM_MODEL_ID")
            timeout = kwargs.get("timeout") or int(os.getenv("LLM_TIMEOUT", 60))
        elif provider in self.PROVIDER_PATTERNS:
            info = self.PROVIDER_PATTERNS[provider]
            api_key = api_key or os.getenv(info["env_key"])
            base_url = base_url or info["base_url"]
            self.model = model or os.getenv("LLM_MODEL_ID")
            timeout = kwargs.get("timeout", 60)
        else:
            api_key = api_key or os.getenv("LLM_API_KEY")
            base_url = base_url or os.getenv("LLM_BASE_URL")
            self.model = model or os.getenv("LLM_MODEL_ID")
            timeout = kwargs.get("timeout", 60)

        if not all([self.model, api_key, base_url]):
            raise ValueError(
                "模型ID、API密钥和服务地址必须被提供或在.env文件中定义。\n"
                f"当前: model={self.model}, api_key={'有' if api_key else '无'}, base_url={base_url}"
            )

        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens")
        self.timeout = timeout
        self._client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    def think(self, messages: List[Dict[str, str]], temperature: float = 0) -> str:
        print(f"🧠 正在调用 {self.model} 模型...")
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
            )
            print("✅ 大语言模型响应成功:")
            collected = []
            for chunk in response:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content or ""
                print(content, end="", flush=True)
                collected.append(content)
            print()
            return "".join(collected)
        except Exception as e:
            print(f"❌ 调用LLM API时发生错误: {e}")
            return None

    def invoke(self, messages: List[Dict[str, str]], **kwargs) -> str:
        temperature = kwargs.get("temperature", self.temperature)
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=False,
                **({k: v for k, v in kwargs.items() if k in ("max_tokens", "top_p") and v}),
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ 调用LLM API时发生错误: {e}")
            return ""

    def stream_invoke(self, messages: List[Dict[str, str]], **kwargs) -> Iterator[str]:
        temperature = kwargs.get("temperature", self.temperature)
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                stream=True,
                **({k: v for k, v in kwargs.items() if k in ("max_tokens", "top_p") and v}),
            )
            for chunk in response:
                if not chunk.choices:
                    continue
                content = chunk.choices[0].delta.content or ""
                if content:
                    yield content
        except Exception as e:
            print(f"❌ 流式调用LLM API时发生错误: {e}")
