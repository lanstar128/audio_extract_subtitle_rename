#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频处理工具集 - 主程序入口
整合音频提取和字幕重命名功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入主窗口
from src.main_window import main

if __name__ == "__main__":
    main()
