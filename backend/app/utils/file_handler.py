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

async def convert_to_utf8(file_path: str, original_encoding: str) -> str:
    """
    Convert file content to UTF-8 encoding.
    Returns: new file path (same as input if no conversion needed or failed)
    """
    if not original_encoding or original_encoding.lower() == 'utf-8':
        return file_path
        
    try:
        # Create a temporary file path
        temp_path = str(file_path) + ".utf8.tmp"
        
        async with aiofiles.open(file_path, 'rb') as source_file:
            content_bytes = await source_file.read()
            
        # Decode with original encoding and encode to utf-8
        try:
            content_str = content_bytes.decode(original_encoding)
        except UnicodeDecodeError:
            # Fallback: try 'gb18030' for Chinese if original detection was 'gb2312' or 'gbk'
            if original_encoding.lower() in ['gb2312', 'gbk']:
                content_str = content_bytes.decode('gb18030', errors='replace')
            else:
                content_str = content_bytes.decode(original_encoding, errors='replace')
                
        async with aiofiles.open(temp_path, 'w', encoding='utf-8') as target_file:
            await target_file.write(content_str)
            
        # Replace original file with UTF-8 version
        os.replace(temp_path, file_path)
        return file_path
        
    except Exception as e:
        print(f"Error converting to UTF-8: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return file_path

async def save_upload_file(upload_file: UploadFile) -> tuple[str, int]:
    """
    Save uploaded file to disk.
    Returns: (file_path, file_size)
    """
    # Sanitize filename (simple version)
    filename = Path(upload_file.filename).name
    file_path = UPLOAD_DIR / filename
    
    # Handle duplicate filenames
    if file_path.exists():
        stem = file_path.stem
        suffix = file_path.suffix
        counter = 1
        while file_path.exists():
            new_name = f"{stem}_{counter}{suffix}"
            file_path = UPLOAD_DIR / new_name
            counter += 1
            
    # Save original content first
    async with aiofiles.open(file_path, 'wb') as out_file:
        while content := await upload_file.read(1024 * 1024):  # 1MB chunks
            await out_file.write(content)
            
    return str(file_path), os.path.getsize(file_path)

def delete_file(file_path: str):
    """Delete a file from disk."""
    path = Path(file_path)
    if path.exists():
        path.unlink()
