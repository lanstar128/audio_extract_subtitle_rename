#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用工具函数模块
"""

import os
import re
import subprocess
from pathlib import Path
from typing import List, Optional
from config.app_config import get_bin_path


def find_ffmpeg() -> Optional[str]:
    """查找FFmpeg可执行文件路径"""
    # 直接使用项目bin目录中的ffmpeg
    local_ffmpeg = get_bin_path() / "ffmpeg.exe"
    if local_ffmpeg.exists():
        return str(local_ffmpeg)
    
    return None


def find_ffprobe() -> Optional[str]:
    """查找FFprobe可执行文件路径"""
    # 直接使用项目bin目录中的ffprobe
    local_ffprobe = get_bin_path() / "ffprobe.exe"
    if local_ffprobe.exists():
        return str(local_ffprobe)
    
    return None


def extract_episode_tokens(name: str) -> List[int]:
    """从文件名中提取可能的剧集编号（多种格式）"""
    s = name.lower()
    tokens = set()
    
    # S01E02 / S1E2
    for m in re.finditer(r"s(\d{1,2})e(\d{1,3})", s):
        tokens.add(int(m.group(2)))
    
    # E02 / ep02
    for m in re.finditer(r"(?:e|ep)[\s\._-]?(\d{1,3})", s):
        tokens.add(int(m.group(1)))
    
    # 第02集 / 02集
    for m in re.finditer(r"第(\d{1,3})集", name):
        tokens.add(int(m.group(1)))
    
    # 纯数字片段（避免误伤：仅当<=3位且前后分隔清晰）
    for m in re.finditer(r"(?<!\d)(\d{1,3})(?!\d)", s):
        n = int(m.group(1))
        if 0 < n <= 999:
            tokens.add(n)
    
    return sorted(tokens)


def get_media_duration(path: Path) -> Optional[float]:
    """获取媒体文件时长"""
    ffprobe = find_ffprobe()
    if not ffprobe:
        return None
    
    try:
        result = subprocess.run([
            ffprobe, "-v", "error", 
            "-show_entries", "format=duration", 
            "-of", "default=noprint_wrappers=1:nokey=1", 
            str(path)
        ], capture_output=True, text=True, check=True,
           creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        return float(result.stdout.strip())
    except Exception:
        return None


def format_time(seconds: float) -> str:
    """格式化时间显示"""
    if seconds < 60:
        return f"{int(seconds)}秒"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}分{secs}秒"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}时{minutes}分{secs}秒"


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小显示"""
    if size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f}MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f}GB"


def validate_phone_number(phone: str) -> bool:
    """验证手机号格式"""
    phone_clean = ''.join(c for c in phone if c.isdigit())
    return len(phone_clean) == 11 and phone_clean.startswith(('13', '14', '15', '16', '17', '18', '19'))


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除不安全字符"""
    # 移除或替换Windows不允许的字符
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # 移除控制字符
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    # 限制长度
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200 - len(ext)] + ext
    
    return filename.strip()


def ensure_unique_filename(filepath: Path) -> Path:
    """确保文件名唯一，如果已存在则添加数字后缀"""
    if not filepath.exists():
        return filepath
    
    counter = 1
    while True:
        name_parts = filepath.stem + f"_{counter}" + filepath.suffix
        new_path = filepath.parent / name_parts
        if not new_path.exists():
            return new_path
        counter += 1
