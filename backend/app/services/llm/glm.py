import logging
import time
import httpx
import json
from typing import Dict, Any, List, AsyncGenerator
from .base import BaseLLMService

logger = logging.getLogger("service.llm.glm")

class GLMService(BaseLLMService):
    API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    async def generate(self, model: str, api_key: str, prompt: str, temperature: float = 0.7) -> Dict[str, Any]:
        """
        调用智谱 AI (GLM) API 生成文本。
        """
        start_time = time.time()
        
        # 1. 方法入口日志：记录入参（脱敏）
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
        logger.info(f"GLM服务调用开始: 模型={model}, APIKey={masked_key}, Temperature={temperature}")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature
        }

        try:
            # 2. 外部调用日志：记录请求动作
            logger.info(f"发起外部请求: URL={self.API_URL}")
            
            async with httpx.AsyncClient() as client:
                req_start = time.time()
                response = await client.post(self.API_URL, json=payload, headers=headers, timeout=60.0)
                req_duration = (time.time() - req_start) * 1000
                
                # 记录外部调用结果
                logger.info(f"外部请求完成: 状态码={response.status_code}, 耗时={req_duration:.2f}ms")
                
                if response.status_code != 200:
                    error_msg = f"GLM API 调用失败: {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                data = response.json()
                
                content = data["choices"][0]["message"]["content"]
                usage = data.get("usage", {})
                
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
        流式调用智谱 AI (GLM) API。
        """
        start_time = time.time()
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
        logger.info(f"GLM流式服务调用开始: 模型={model}, APIKey={masked_key}, Temperature={temperature}")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "stream": True
        }

        try:
            logger.info(f"发起流式外部请求: URL={self.API_URL}")
            
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", self.API_URL, json=payload, headers=headers, timeout=60.0) as response:
                    if response.status_code != 200:
                        error_content = await response.aread()
                        error_msg = f"GLM API 流式调用失败: {error_content.decode('utf-8')}"
                        logger.error(error_msg)
                        raise Exception(error_msg)
                    
                    logger.info("流式连接建立成功，开始接收数据")
                    
                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        
                        if line == "data: [DONE]":
                            break
                        
                        try:
                            chunk = json.loads(line[6:])
                            content = chunk["choices"][0]["delta"].get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            logger.warning(f"解析流式响应失败: {line}")
                            continue
                            
            total_duration = (time.time() - start_time) * 1000
            logger.info(f"GLM流式服务调用结束: 耗时={total_duration:.2f}ms")
            
        except Exception as e:
            logger.error(f"GLM流式服务调用异常: {str(e)}", exc_info=True)
            raise e
