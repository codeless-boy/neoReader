import chardet
import aiofiles
import os
from fastapi import UploadFile
from pathlib import Path
import shutil

UPLOAD_DIR = Path("backend/static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

async def detect_encoding(file_path: str) -> str:
    """Detect the encoding of a file."""
    try:
        async with aiofiles.open(file_path, 'rb') as f:
            rawdata = await f.read(10000)  # Read more for better accuracy
        result = chardet.detect(rawdata)
        return result['encoding'] or 'utf-8'
    except Exception:
        return 'utf-8'

async def save_upload_file(upload_file: UploadFile) -> tuple[str, int]:
    """
    Save uploaded file to disk.
    Returns: (file_path, file_size)
    """
    file_path = UPLOAD_DIR / upload_file.filename
    
    # Handle duplicate filenames
    if file_path.exists():
        stem = file_path.stem
        suffix = file_path.suffix
        counter = 1
        while file_path.exists():
            file_path = UPLOAD_DIR / f"{stem}_{counter}{suffix}"
            counter += 1
            
    async with aiofiles.open(file_path, 'wb') as out_file:
        while content := await upload_file.read(1024 * 1024):  # 1MB chunks
            await out_file.write(content)
            
    file_size = os.path.getsize(file_path)
    return str(file_path), file_size

def delete_file(file_path: str):
    """Delete a file from disk."""
    path = Path(file_path)
    if path.exists():
        path.unlink()
