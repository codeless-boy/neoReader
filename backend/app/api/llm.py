import logging
import time
import json
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session
from langchain_community.chat_message_histories import SQLChatMessageHistory
from ..schemas.llm import LLMRequest, LLMResponse
from ..services.llm.factory import LLMFactory
from ..database import get_session
from ..models import SystemSetting

router = APIRouter()
logger = logging.getLogger("api.llm")

@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    获取指定会话的历史记录。
    """
    try:
        history = SQLChatMessageHistory(
            session_id=session_id,
            connection_string="sqlite:///database.db"
        )
        messages = []
        for msg in history.messages:
            role = "user" if msg.type == "human" else "assistant"
            messages.append({"role": role, "content": msg.content})
        return messages
    except Exception as e:
        logger.error(f"获取聊天历史失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取聊天历史失败")

@router.post("/chat", response_model=None)
async def chat(request: LLMRequest, session: Session = Depends(get_session)):
    """
    LLM 对话接口。
    根据 provider 参数路由到不同的服务提供商。
    支持 stream=True 开启流式响应。
    """
    start_time = time.time()
    
    # 1. 方法入口日志
    logger.info(f"收到 LLM 请求: Provider={request.provider}, Model={request.model}, ConfigKey={request.config_key}, Stream={request.stream}")
    
    try:
        # 2. 从数据库获取实际的 API Key
        setting = session.get(SystemSetting, request.config_key)
        if not setting or not setting.value:
            logger.error(f"未找到 API 配置: {request.config_key}")
            raise HTTPException(status_code=400, detail="未找到有效的 API 配置，请先在系统设置中配置")
            
        api_key = setting.value
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
        logger.info(f"获取 API Key 成功: {masked_key}")

        # 3. 逻辑分叉：根据 provider 选择服务
        logger.info(f"开始获取服务实例: {request.provider}")
        service = LLMFactory.get_service(request.provider)
        
        # 初始化聊天历史
        session_id = request.session_id or "default"
        history = SQLChatMessageHistory(
            session_id=session_id,
            connection_string="sqlite:///database.db"
        )
        # 记录用户消息
        history.add_user_message(request.prompt)
        
        if request.stream:
            # 流式响应处理
            logger.info("准备调用 Service 生成流式内容")
            
            async def event_generator():
                full_content = ""
                try:
                    async for chunk in service.generate_stream(
                        model=request.model,
                        api_key=api_key,
                        prompt=request.prompt,
                        temperature=request.temperature
                    ):
                        full_content += chunk
                        # 构造 SSE 格式数据
                        yield f"data: {json.dumps({'content': chunk, 'provider': request.provider, 'model': request.model}, ensure_ascii=False)}\n\n"
                    
                    # 记录 AI 回复
                    history.add_ai_message(full_content)
                    
                    # 结束标记
                    yield "data: [DONE]\n\n"
                    
                except Exception as e:
                    logger.error(f"流式生成异常: {str(e)}", exc_info=True)
                    yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
            
            return StreamingResponse(event_generator(), media_type="text/event-stream")
            
        else:
            # 4. 外部调用：通过 service 调用 LLM (非流式)
            logger.info("准备调用 Service 生成内容")
            result = await service.generate(
                model=request.model,
                api_key=api_key,
                prompt=request.prompt,
                temperature=request.temperature
            )
            
            # 记录 AI 回复
            history.add_ai_message(result["content"])
            
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
