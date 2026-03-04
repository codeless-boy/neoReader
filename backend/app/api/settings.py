from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import SystemSetting
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()

DEFAULT_SETTINGS = [
    # Appearance
    SystemSetting(
        key="appearance.theme.mode",
        category="appearance",
        group="Theme",
        label="Mode",
        value="light",
        field_type="select",
        options=json.dumps([{"label": "Light", "value": "light"}, {"label": "Dark", "value": "dark"}, {"label": "Auto", "value": "auto"}]),
        description="Application theme mode",
        sort_order=1
    ),
    # Storage
    SystemSetting(
        key="storage.library.path",
        category="storage",
        group="Library",
        label="Scan Path",
        value="backend/static/uploads",
        field_type="readonly",
        description="Path where books are stored",
        sort_order=1
    ),
    # Reader
    SystemSetting(
        key="reader.display.fontSize",
        category="reader",
        group="Display",
        label="Default Font Size",
        value="16",
        field_type="number",
        description="Default font size for reader",
        sort_order=1
    ),
    SystemSetting(
        key="reader.display.pageMode",
        category="reader",
        group="Display",
        label="Page Mode",
        value="scroll",
        field_type="select",
        options=json.dumps([{"label": "Scroll", "value": "scroll"}, {"label": "Pagination", "value": "pagination"}]),
        description="Default page turning mode",
        sort_order=2
    ),
    # LLM
    SystemSetting(
        key="llm.provider.glm.api_key",
        category="model",
        group="provider",
        label="GLM API Key",
        value="",
        field_type="text",
        description="智谱 AI (GLM) 的 API Key",
        sort_order=10
    ),
    SystemSetting(
        key="llm.model.glm.name",
        category="model",
        group="model",
        label="GLM 模型",
        value="glm-4-flash",
        field_type="readonly",
        description="当前支持的 GLM 模型",
        sort_order=20
    )
]

def init_settings(session: Session):
    """Initialize default settings if they don't exist."""
    for setting in DEFAULT_SETTINGS:
        existing = session.get(SystemSetting, setting.key)
        if not existing:
            session.add(setting)
            session.commit()
            logger.info(f"Initialized setting: {setting.key}")

@router.get("/", response_model=Dict[str, Dict[str, List[SystemSetting]]])
def get_settings(session: Session = Depends(get_session)):
    """
    Get all settings grouped by category -> group.
    """
    settings = session.exec(select(SystemSetting).order_by(SystemSetting.sort_order)).all()
    
    result = {}
    for setting in settings:
        if setting.category not in result:
            result[setting.category] = {}
        if setting.group not in result[setting.category]:
            result[setting.category][setting.group] = []
        
        result[setting.category][setting.group].append(setting)
    
    return result

@router.put("/{key}", response_model=SystemSetting)
def update_setting(key: str, value: str, session: Session = Depends(get_session)):
    """
    Update a specific setting.
    """
    setting = session.get(SystemSetting, key)
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    
    setting.value = value
    session.add(setting)
    session.commit()
    session.refresh(setting)
    logger.info(f"Updated setting {key} to {value}")
    return setting

@router.get("/system-info")
def get_system_info():
    """Get read-only system information."""
    import os
    import platform
    return {
        "os": platform.system(),
        "platform": platform.platform(),
        "cwd": os.getcwd(),
        "version": "0.1.0"
    }
