#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyInstaller打包脚本
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    """主函数"""
    print("开始打包程序...")
    
    # 项目根目录
    project_root = Path(__file__).parent.parent
    tools_dir = Path(__file__).parent
    
    # 切换到项目根目录
    os.chdir(project_root)
    
    # 清理之前的构建
    print("清理之前的构建文件...")
    build_dirs = ['build', 'dist']
    for build_dir in build_dirs:
        if Path(build_dir).exists():
            shutil.rmtree(build_dir)
            print(f"   删除 {build_dir}/")
    
    # 执行PyInstaller打包
    print("执行PyInstaller打包...")
    spec_file = tools_dir / 'app.spec'
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        str(spec_file)
    ]
    
    try:
        # 隐藏PyInstaller的控制台窗口
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        result = subprocess.run(
            cmd, 
            check=True, 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            errors='ignore',
            startupinfo=startupinfo
        )
        
        print("PyInstaller打包完成！")
        
        # 检查输出文件
        dist_dir = project_root / 'dist' / 'audio_subtitle_tools'
        if dist_dir.exists():
            exe_file = dist_dir / 'audio_subtitle_tools.exe'
            if exe_file.exists():
                print(f"可执行文件位置: {exe_file}")
                print(f"文件大小: {exe_file.stat().st_size / 1024 / 1024:.1f} MB")
            else:
                print("未找到可执行文件")
                return False
        else:
            print("未找到输出目录")
            return False
            
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller打包失败: {e}")
        if e.stdout:
            print("标准输出:")
            print(e.stdout)
        if e.stderr:
            print("错误输出:")
            print(e.stderr)
        return False
    except Exception as e:
        print(f"打包过程出错: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
    print("打包完成！")
