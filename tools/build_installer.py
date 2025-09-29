#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inno Setup安装包制作脚本
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def find_inno_setup():
    """查找Inno Setup编译器"""
    possible_paths = [
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe", 
        r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        r"C:\Program Files\Inno Setup 5\ISCC.exe",
    ]
    
    for path in possible_paths:
        if Path(path).exists():
            return path
    
    return None

def main():
    """主函数"""
    print("开始制作安装包...")
    
    # 项目根目录
    project_root = Path(__file__).parent.parent
    tools_dir = Path(__file__).parent
    
    # 切换到项目根目录
    os.chdir(project_root)
    
    # 检查dist目录是否存在
    dist_dir = project_root / 'dist' / 'audio_subtitle_tools'
    if not dist_dir.exists():
        print("错误: 未找到PyInstaller输出目录，请先运行build.py")
        return False
    
    # 检查exe文件是否存在
    exe_file = dist_dir / 'audio_subtitle_tools.exe'
    if not exe_file.exists():
        print("错误: 未找到可执行文件")
        return False
    
    print(f"找到可执行文件: {exe_file}")
    
    # 查找Inno Setup
    iscc_path = find_inno_setup()
    if not iscc_path:
        print("错误: 未找到Inno Setup编译器")
        print("请从以下地址下载并安装Inno Setup:")
        print("https://jrsoftware.org/isinfo.php")
        return False
    
    print(f"找到Inno Setup编译器: {iscc_path}")
    
    # 创建installer目录
    installer_dir = project_root / 'installer'
    installer_dir.mkdir(exist_ok=True)
    
    # Inno Setup脚本路径
    iss_file = tools_dir / 'setup.iss'
    
    # 执行Inno Setup编译
    print("执行Inno Setup编译...")
    
    try:
        # 隐藏Inno Setup的控制台窗口
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        result = subprocess.run(
            [iscc_path, str(iss_file)],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            startupinfo=startupinfo
        )
        
        print("Inno Setup编译完成！")
        
        # 检查输出文件
        setup_files = list(installer_dir.glob('*.exe'))
        if setup_files:
            setup_file = setup_files[0]
            print(f"安装包位置: {setup_file}")
            print(f"文件大小: {setup_file.stat().st_size / 1024 / 1024:.1f} MB")
            return True
        else:
            print("未找到生成的安装包")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"Inno Setup编译失败: {e}")
        if e.stdout:
            print("标准输出:")
            print(e.stdout)
        if e.stderr:
            print("错误输出:")
            print(e.stderr)
        return False
    except Exception as e:
        print(f"编译过程出错: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
    print("安装包制作完成！")


