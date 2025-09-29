#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键打包脚本 - 完整流程
"""

import os
import sys
import subprocess
from pathlib import Path

def run_script(script_name):
    """运行指定脚本"""
    script_path = Path(__file__).parent / script_name
    if not script_path.exists():
        print(f"错误: 找不到脚本 {script_name}")
        return False
    
    print(f"\n{'='*50}")
    print(f"运行脚本: {script_name}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"脚本运行失败: {e}")
        return False
    except Exception as e:
        print(f"运行过程出错: {e}")
        return False

def main():
    """主函数"""
    print("开始完整打包流程...")
    print("这将执行以下步骤:")
    print("1. 使用PyInstaller打包为exe")
    print("2. 使用Inno Setup制作安装包")
    print("3. 清理临时文件")
    
    # 项目根目录
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # 执行步骤
    steps = [
        ("build.py", "PyInstaller打包"),
        ("build_installer.py", "制作安装包"),
        ("cleanup.py", "清理临时文件"),
    ]
    
    for script, description in steps:
        print(f"\n开始执行: {description}")
        if not run_script(script):
            print(f"错误: {description} 失败")
            return False
        print(f"完成: {description}")
    
    print(f"\n{'='*50}")
    print("所有步骤完成！")
    print(f"{'='*50}")
    
    # 显示最终结果
    installer_dir = project_root / 'installer'
    if installer_dir.exists():
        installer_files = list(installer_dir.glob('*.exe'))
        if installer_files:
            installer_file = installer_files[0]
            size_mb = installer_file.stat().st_size / 1024 / 1024
            print(f"\n最终安装包:")
            print(f"文件: {installer_file}")
            print(f"大小: {size_mb:.1f} MB")
        else:
            print("\n警告: 未找到安装包文件")
    else:
        print("\n警告: 未找到installer目录")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n打包过程中出现错误！")
        sys.exit(1)
    print("\n打包完成！可以分发安装包了。")


