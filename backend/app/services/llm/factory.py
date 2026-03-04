from typing import Dict, Type
from .base import BaseLLMService
from .glm import GLMService

class LLMFactory:
    _services: Dict[str, Type[BaseLLMService]] = {
        "glm": GLMService
    }
    
    @classmethod
    def get_service(cls, provider: str) -> BaseLLMService:
        """
        根据提供商名称获取对应的 LLM 服务实例。
        
        Args:
            provider (str): 服务提供商名称
            
        Returns:
            BaseLLMService: 对应的服务实例
            
        Raises:
            ValueError: 如果提供商不支持
        """
        service_cls = cls._services.get(provider.lower())
        if not service_cls:
            raise ValueError(f"不支持的服务提供商: {provider}")
            
        return service_cls()
