from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class LLMRequest(BaseModel):
    provider: str = Field(..., description="服务提供商，如 'glm'")
    model: str = Field(..., description="模型名称，如 'glm-4-flash'")
    api_key: str = Field(..., description="API 密钥")
    prompt: str = Field(..., description="提示词")
    temperature: float = Field(0.7, description="采样温度，控制输出的随机性")

class LLMResponse(BaseModel):
    content: str = Field(..., description="生成的文本内容")
    provider: str = Field(..., description="服务提供商")
    model: str = Field(..., description="模型名称")
    usage: Optional[Dict[str, Any]] = Field(None, description="Token 使用情况")
