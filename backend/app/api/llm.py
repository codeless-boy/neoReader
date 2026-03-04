import logging
import time
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from ..schemas.llm import LLMRequest, LLMResponse
from ..services.llm.factory import LLMFactory

router = APIRouter()
logger = logging.getLogger("api.llm")

@router.post("/chat", response_model=None)
async def chat(request: LLMRequest):
    """
    LLM 对话接口。
    根据 provider 参数路由到不同的服务提供商。
    支持 stream=True 开启流式响应。
    """
    start_time = time.time()
    masked_key = f"{request.api_key[:4]}...{request.api_key[-4:]}" if len(request.api_key) > 8 else "***"
    
    # 1. 方法入口日志
    logger.info(f"收到 LLM 请求: Provider={request.provider}, Model={request.model}, APIKey={masked_key}, Stream={request.stream}")
    
    try:
        # 2. 逻辑分叉：根据 provider 选择服务
        logger.info(f"开始获取服务实例: {request.provider}")
        service = LLMFactory.get_service(request.provider)
        
        if request.stream:
            # 流式响应处理
            logger.info("准备调用 Service 生成流式内容")
            
            async def event_generator():
                try:
                    async for chunk in service.generate_stream(
                        model=request.model,
                        api_key=request.api_key,
                        prompt=request.prompt,
                        temperature=request.temperature
                    ):
                        # 构造 SSE 格式数据
                        yield f"data: {json.dumps({'content': chunk, 'provider': request.provider, 'model': request.model}, ensure_ascii=False)}\n\n"
                    
                    # 结束标记
                    yield "data: [DONE]\n\n"
                    
                except Exception as e:
                    logger.error(f"流式生成异常: {str(e)}", exc_info=True)
                    yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            
            return StreamingResponse(event_generator(), media_type="text/event-stream")
            
        else:
            # 3. 外部调用：通过 service 调用 LLM (非流式)
            logger.info("准备调用 Service 生成内容")
            result = await service.generate(
                model=request.model,
                api_key=request.api_key,
                prompt=request.prompt,
                temperature=request.temperature
            )
            
            total_time = (time.time() - start_time) * 1000
            logger.info(f"LLM 请求处理成功: 耗时={total_time:.2f}ms")
            
            return LLMResponse(
                content=result["content"],
                provider=result["provider"],
                model=result["model"],
                usage=result.get("usage")
            )
        
    except ValueError as e:
        # 捕获不支持的 Provider 异常
        logger.warning(f"请求参数错误: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        # 4. 异常捕获日志：记录完整堆栈
        logger.error(f"处理 LLM 请求时发生未捕获异常: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务器内部错误")
