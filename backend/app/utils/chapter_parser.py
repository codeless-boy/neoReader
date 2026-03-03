import re
import aiofiles
from typing import List, Tuple

# Pre-compiled regex for chapter matching
# Matches:
# 1. "第" + [Chinese/Arabic numerals] + [章/回/卷/部/节]
# 2. "Chapter" + [Arabic numerals/Roman numerals]
# 3. [Arabic numerals] + "." or "、"
# 4. [Chinese numerals] + "." or "、"
# 5. Special titles: 序, 前言, 楔子, 后记, 尾声
CHAPTER_PATTERN = re.compile(
    r'^\s*((?:第[0-9零一二三四五六七八九十百千]+[章回卷部节]|Chapter\s+[0-9IVX]+|[0-9]+[、\.]|[一二三四五六七八九十]+[、\.])\s*.*|(?:序|前言|楔子|后记|尾声)\s*)$',
    re.MULTILINE
)

class ChapterExtractor:
    @staticmethod
    async def parse(file_path: str, encoding: str = 'utf-8') -> List[Tuple[str, int]]:
        """
        Parse chapters from a TXT file.
        Returns a list of tuples: (title, start_offset)
        """
        chapters = []
        
        # Always include a default start chapter
        chapters.append(("开始阅读", 0))
        
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                # Read file line by line in binary mode to keep track of byte offsets
                current_offset = 0
                async for line_bytes in f:
                    line_len = len(line_bytes)
                    
                    try:
                        # Decode line to string for regex matching
                        line_str = line_bytes.decode(encoding).strip()
                    except UnicodeDecodeError:
                        # Skip lines that cannot be decoded
                        current_offset += line_len
                        continue
                        
                    # Skip empty lines or lines that are too long (likely content)
                    if not line_str or len(line_str) > 50:
                        current_offset += line_len
                        continue
                        
                    # Check regex match
                    match = CHAPTER_PATTERN.match(line_str)
                    if match:
                        title = match.group(1)
                        chapters.append((title, current_offset))
                    
                    current_offset += line_len
                    
        except Exception as e:
            print(f"Error parsing chapters: {e}")
            # Even if parsing fails, we return at least the default chapter
            
        return chapters
