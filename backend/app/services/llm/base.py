from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseLLMService(ABC):
    @abstractmethod
    async def generate(self, model: str, api_key: str, prompt: str, temperature: float = 0.7) -> Dict[str, Any]:
        """
        生成文本内容。
        
        Args:
            model (str): 模型名称
            api_key (str): API 密钥
            prompt (str): 提示词
            temperature (float): 采样温度
            
        Returns:
            Dict[str, Any]: 包含生成内容和使用情况的字典
        """
        pass
