@echo off
chcp 65001 >nul
title 视频处理工具集

echo.
echo =============================================
echo    视频处理工具集 v2.0.0
echo    整合音频提取和字幕重命名功能
echo =============================================
echo.

echo 正在启动程序...
python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ 程序运行失败！
    echo.
    echo 可能的解决方案：
    echo 1. 确保已安装 Python 3.8+
    echo 2. 运行：pip install -r requirements.txt
    echo 3. 检查是否有其他错误信息
    echo.
    pause
)

