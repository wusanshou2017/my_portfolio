from dataclasses import dataclass, field


@dataclass
class Config:
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 60
    top_p: float = 1.0
    extra: dict = field(default_factory=dict)
