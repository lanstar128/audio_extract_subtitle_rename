#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理临时文件脚本
"""

import os
import shutil
from pathlib import Path

def main():
    """主函数"""
    print("开始清理临时文件...")
    
    # 项目根目录
    project_root = Path(__file__).parent.parent
    
    # 切换到项目根目录
    os.chdir(project_root)
    
    # 需要清理的目录和文件
    cleanup_items = [
        'build',           # PyInstaller构建目录
        'dist',            # PyInstaller输出目录
        '__pycache__',     # Python缓存目录
        '*.spec',          # PyInstaller规格文件
        '*.pyc',           # Python编译文件
        '*.pyo',           # Python优化文件
    ]
    
    cleaned_count = 0
    
    for item in cleanup_items:
        if item.startswith('*'):
            # 处理通配符文件
            import glob
            for file_path in glob.glob(item, recursive=True):
                try:
                    Path(file_path).unlink()
                    print(f"删除文件: {file_path}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"删除文件失败 {file_path}: {e}")
        else:
            # 处理目录
            item_path = Path(item)
            if item_path.exists():
                try:
                    if item_path.is_dir():
                        shutil.rmtree(item_path)
                        print(f"删除目录: {item_path}")
                    else:
                        item_path.unlink()
                        print(f"删除文件: {item_path}")
                    cleaned_count += 1
                except Exception as e:
                    print(f"删除失败 {item_path}: {e}")
    
    # 递归清理所有__pycache__目录
    for pycache_dir in project_root.rglob('__pycache__'):
        try:
            shutil.rmtree(pycache_dir)
            print(f"删除缓存目录: {pycache_dir}")
            cleaned_count += 1
        except Exception as e:
            print(f"删除缓存目录失败 {pycache_dir}: {e}")
    
    # 递归清理所有.pyc文件
    for pyc_file in project_root.rglob('*.pyc'):
        try:
            pyc_file.unlink()
            print(f"删除缓存文件: {pyc_file}")
            cleaned_count += 1
        except Exception as e:
            print(f"删除缓存文件失败 {pyc_file}: {e}")
    
    print(f"\n清理完成！共清理了 {cleaned_count} 个项目。")
    
    # 显示保留的重要文件
    print("\n保留的重要文件:")
    installer_dir = project_root / 'installer'
    if installer_dir.exists():
        for installer_file in installer_dir.glob('*.exe'):
            size_mb = installer_file.stat().st_size / 1024 / 1024
            print(f"  安装包: {installer_file.name} ({size_mb:.1f} MB)")
    
    tools_dir = project_root / 'tools'
    if tools_dir.exists():
        print(f"  打包脚本目录: {tools_dir}")
        for script_file in tools_dir.glob('*.py'):
            print(f"    - {script_file.name}")
        for script_file in tools_dir.glob('*.iss'):
            print(f"    - {script_file.name}")
        for script_file in tools_dir.glob('*.spec'):
            print(f"    - {script_file.name}")

if __name__ == "__main__":
    main()


