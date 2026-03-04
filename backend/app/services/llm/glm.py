import logging
import time
import httpx
from typing import Dict, Any, List
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
