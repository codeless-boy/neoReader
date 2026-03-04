import logging
import time
from typing import Dict, Any, AsyncGenerator
from .base import BaseLLMService
from langchain_community.chat_models import ChatZhipuAI
from langchain_core.messages import HumanMessage

logger = logging.getLogger("service.llm.glm")

class GLMService(BaseLLMService):
    async def generate(self, model: str, api_key: str, prompt: str, temperature: float = 0.7) -> Dict[str, Any]:
        """
        调用智谱 AI (GLM) API 生成文本 (LangChain)。
        """
        start_time = time.time()
        
        # 1. 方法入口日志：记录入参（脱敏）
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
        logger.info(f"GLM服务调用开始(LangChain): 模型={model}, APIKey={masked_key}, Temperature={temperature}")

        try:
            # 2. 外部调用日志：记录请求动作
            logger.info("初始化 LangChain ChatZhipuAI 客户端")
            
            chat = ChatZhipuAI(
                api_key=api_key,
                model=model,
                temperature=temperature
            )
            
            req_start = time.time()
            response = await chat.ainvoke([HumanMessage(content=prompt)])
            req_duration = (time.time() - req_start) * 1000
            
            # 记录外部调用结果
            logger.info(f"LangChain 请求完成: 耗时={req_duration:.2f}ms")
            
            content = response.content
            # LangChain response.response_metadata usually contains usage info
            usage = response.response_metadata.get("token_usage", {})
            
            total_duration = (time.time() - start_time) * 1000
            logger.info(f"GLM服务调用成功: 耗时={total_duration:.2f}ms")
            
            return {
                "content": content,
                "usage": usage,
                "provider": "glm",
                "model": model
            }
                
        except Exception as e:
            # 3. 异常捕获日志：记录完整堆栈
            logger.error(f"GLM服务调用异常: {str(e)}", exc_info=True)
            raise e

    async def generate_stream(self, model: str, api_key: str, prompt: str, temperature: float = 0.7) -> AsyncGenerator[str, None]:
        """
        流式调用智谱 AI (GLM) API (LangChain)。
        """
        start_time = time.time()
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
        logger.info(f"GLM流式服务调用开始(LangChain): 模型={model}, APIKey={masked_key}, Temperature={temperature}")

        try:
            logger.info("初始化 LangChain ChatZhipuAI 客户端 (Streaming)")
            
            chat = ChatZhipuAI(
                api_key=api_key,
                model=model,
                temperature=temperature,
                streaming=True
            )
            
            logger.info("开始接收 LangChain 流式数据")
            
            async for chunk in chat.astream([HumanMessage(content=prompt)]):
                if chunk.content:
                    yield chunk.content
                            
            total_duration = (time.time() - start_time) * 1000
            logger.info(f"GLM流式服务调用结束: 耗时={total_duration:.2f}ms")
            
        except Exception as e:
            logger.error(f"GLM流式服务调用异常: {str(e)}", exc_info=True)
            raise e
