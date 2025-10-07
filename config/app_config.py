#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用配置文件
"""

from pathlib import Path

# 应用基本信息
APP_NAME = "视频处理工具集"
APP_VERSION = "2.0.0"
APP_AUTHOR = "开发团队"

# 文件格式支持
VIDEO_EXTENSIONS = {
    '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', 
    '.webm', '.m4v', '.3gp', '.mts', '.m2ts', '.ts'
}

SUBTITLE_EXTENSIONS = {
    '.srt', '.ass', '.ssa', '.vtt', '.sub'
}

AUDIO_EXTENSIONS = {
    '.mp3', '.wav', '.m4a', '.wma', '.aac', 
    '.ogg', '.amr', '.flac', '.aiff'
}

# 处理配置
MAX_FILE_SIZE_MB = 500  # 超过此大小将转码为MP3
DEFAULT_THREADS = 4
MAX_THREADS = 32

# 激活系统配置
SECRET_KEY = "VideoAudioExtractor_2024_Secret_Key"

# 日志配置
LOG_FILE_NAME = ".processing_log.json"

# 路径配置
def get_app_root():
    """获取应用根目录"""
    return Path(__file__).parent.parent

def get_bin_path():
    """获取二进制文件目录"""
    return get_app_root() / "bin"

def get_resources_path():
    """获取资源文件目录"""
    return get_app_root() / "resources"

def get_images_path():
    """获取图像资源目录"""
    return get_resources_path() / "images"



