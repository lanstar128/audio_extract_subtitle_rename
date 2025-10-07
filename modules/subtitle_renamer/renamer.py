#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕重命名器模块
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher

from config.app_config import VIDEO_EXTENSIONS, SUBTITLE_EXTENSIONS, LOG_FILE_NAME

# 预定义字幕后缀列表
SUBTITLE_SUFFIXES = [
    '_原文', '_原版', '_英文', '_中文', '_简体', '_繁体',
    '_subtitle', '_sub', '_srt', '_ass', '_vtt',
    '_zh', '_en', '_chs', '_cht', '_jpn', '_kor',
    '_1', '_2', '_3', '_4', '_5'
]


def truncate_filename(filename: str, max_length: int = 35, head_chars: int = 10, tail_chars: int = 10) -> str:
    """
    智能截断长文件名，保留开头和结尾部分
    
    Args:
        filename: 完整文件名（包含扩展名）
        max_length: 最大显示长度，超过此长度才截断
        head_chars: 开头保留字符数
        tail_chars: 结尾保留字符数（不含扩展名）
    
    Returns:
        截断后的文件名，格式为 "开头...结尾.扩展名"
    
    Examples:
        >>> truncate_filename("5021e8fe6905df2ba70ba42afd0584a5.mp4", 30, 10, 8)
        "5021e8fe69...fd0584a5.mp4"
        >>> truncate_filename("short.mp4", 30, 10, 8)
        "short.mp4"
    """
    if len(filename) <= max_length:
        return filename
    
    # 分离文件名和扩展名
    path_obj = Path(filename)
    stem = path_obj.stem  # 文件名（不含扩展名）
    ext = path_obj.suffix  # 扩展名（包含点号）
    
    # 如果文件名本身就很短，不需要截断
    if len(stem) <= (head_chars + tail_chars + 3):  # 3是"..."的长度
        return filename
    
    # 截断文件名：保留开头和结尾
    head = stem[:head_chars]
    tail = stem[-tail_chars:] if tail_chars > 0 else ""
    
    return f"{head}...{tail}{ext}"


@dataclass
class FileItem:
    """文件项数据类"""
    path: Path
    stem: str
    ext: str


@dataclass
class PlanRow:
    """重命名计划行"""
    sub: Optional[FileItem]  # 字幕文件，可为空（只有视频文件时）
    video: Optional[FileItem]  # 视频文件，可为空（只有字幕文件时）
    target_name: Optional[str]
    reason: str  # 匹配说明/跳过原因


class SubtitleRenamer:
    """字幕重命名器"""
    
    def __init__(self):
        pass
    
    def _try_suffix_match(self, subtitle_stem: str, video_dict: Dict[str, FileItem]) -> Optional[Tuple[FileItem, str]]:
        """尝试后缀匹配
        
        Returns:
            Optional[Tuple[FileItem, str]]: (匹配的视频文件, 清理后的文件名) 或 None
        """
        for suffix in SUBTITLE_SUFFIXES:
            if subtitle_stem.endswith(suffix):
                cleaned_name = subtitle_stem[:-len(suffix)]
                if cleaned_name in video_dict:
                    return video_dict[cleaned_name], cleaned_name
        return None
    
    def _try_similarity_match(self, subtitle_stem: str, video_dict: Dict[str, FileItem], threshold: float = 0.7) -> Optional[Tuple[FileItem, str, float]]:
        """尝试相似度匹配
        
        Returns:
            Optional[Tuple[FileItem, str, float]]: (匹配的视频文件, 视频文件名, 相似度) 或 None
        """
        best_match = None
        best_ratio = 0.0
        best_video = None
        
        for video_stem, video_item in video_dict.items():
            ratio = SequenceMatcher(None, subtitle_stem, video_stem).ratio()
            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_match = video_stem
                best_video = video_item
        
        if best_match:
            return best_video, best_match, best_ratio
        return None
    
    def scan_files(self, root: Path) -> Tuple[List[FileItem], List[FileItem]]:
        """扫描视频和字幕文件"""
        videos, subs = [], []
        
        for p in root.rglob('*'):
            if not p.is_file():
                continue
            
            ext = p.suffix.lower()
            if ext in VIDEO_EXTENSIONS | SUBTITLE_EXTENSIONS:
                item = FileItem(
                    path=p, 
                    stem=p.stem, 
                    ext=ext
                )
                
                if ext in VIDEO_EXTENSIONS:
                    videos.append(item)
                else:
                    subs.append(item)
        
        return videos, subs
    
    def build_plan(self, videos: List[FileItem], subs: List[FileItem]) -> List[PlanRow]:
        """构建重命名计划"""
        plan: List[PlanRow] = []
        
        # 为视频文件建立索引，便于查找
        video_dict = {}
        for v in videos:
            # 使用文件名（不含扩展名）作为键
            video_dict[v.stem] = v
        
        # 为字幕文件建立索引，用于检测只有视频文件的情况
        sub_dict = {}
        for s in subs:
            sub_dict[s.stem] = s
        
        # 处理字幕文件（原有逻辑）
        for s in subs:
            matched_video: Optional[FileItem] = None
            target_name: Optional[str] = None
            reason = ""
            
            # 1. 精确匹配：字幕文件名与视频文件名完全一致
            if s.stem in video_dict:
                matched_video = video_dict[s.stem]
                reason = "已有字幕"
                target_name = None  # 不需要重命名
            else:
                # 2. 后缀匹配：尝试移除预定义后缀后匹配
                suffix_match = self._try_suffix_match(s.stem, video_dict)
                if suffix_match:
                    matched_video, cleaned_name = suffix_match
                    target_name = cleaned_name + s.ext
                    reason = "需要重命名"
                else:
                    # 3. 相似度匹配：使用字符串相似度算法
                    similarity_match = self._try_similarity_match(s.stem, video_dict)
                    if similarity_match:
                        matched_video, video_stem, ratio = similarity_match
                        target_name = video_stem + s.ext
                        reason = "确认字幕是否正确"
                    else:
                        # 4. 无匹配
                        reason = "未匹配到视频"
            
            plan.append(PlanRow(
                sub=s, 
                video=matched_video, 
                target_name=target_name, 
                reason=reason
            ))
        
        # 处理只有视频文件没有字幕文件的情况
        for v in videos:
            # 检查该视频文件是否已有对应的字幕文件
            if v.stem not in sub_dict:
                # 检查是否有带后缀的字幕文件匹配这个视频
                has_related_subtitle = False
                for sub_stem in sub_dict.keys():
                    for suffix in SUBTITLE_SUFFIXES:
                        if sub_stem.endswith(suffix):
                            cleaned_name = sub_stem[:-len(suffix)]
                            if cleaned_name == v.stem:
                                has_related_subtitle = True
                                break
                    if has_related_subtitle:
                        break
                
                # 如果没有任何相关字幕文件，则添加到计划中
                if not has_related_subtitle:
                    plan.append(PlanRow(
                        sub=None,  # 没有字幕文件
                        video=v,
                        target_name=None,
                        reason="缺少字幕文件"
                    ))
        
        return plan
    
    def execute_plan(self, plan: List[PlanRow], root_dir: Path) -> Tuple[int, int, List[str]]:
        """执行重命名计划
        
        Returns:
            Tuple[int, int, List[str]]: (成功数量, 冲突数量, 冲突列表)
        """
        # 组装重命名任务
        tasks: List[Tuple[Path, Path]] = []
        conflicts: List[str] = []
        
        for row in plan:
            if not row.sub or not row.video or not row.target_name:
                continue
            
            src = row.sub.path
            dst = src.with_name(row.target_name)
            
            if dst.exists() and dst.resolve() != src.resolve():
                conflicts.append(f"目标已存在：{dst.name}")
                continue
            
            tasks.append((src, dst))
        
        if not tasks:
            return 0, len(conflicts), conflicts
        
        # 备份日志
        log_path = root_dir / LOG_FILE_NAME
        history = []
        if log_path.exists():
            try:
                history = json.loads(log_path.read_text(encoding="utf-8"))
            except Exception:
                history = []
        
        batch_log = []
        success = 0
        
        for src, dst in tasks:
            try:
                old = src.name
                new = dst.name
                if old == new:
                    continue
                
                src.rename(dst)
                batch_log.append({
                    "old": str(dst.name), 
                    "new": str(old), 
                    "dir": str(dst.parent)
                })
                success += 1
            except Exception as e:
                print("Rename failed:", src, "->", dst, e)
        
        if batch_log:
            history.append(batch_log)
            log_path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
        
        return success, len(conflicts), conflicts
    
    def undo_last_operation(self, root_dir: Path) -> Tuple[bool, int, str]:
        """撤销上一次操作
        
        Returns:
            Tuple[bool, int, str]: (是否成功, 恢复数量, 错误信息)
        """
        log_path = root_dir / LOG_FILE_NAME
        if not log_path.exists():
            return False, 0, "没有可撤销的记录"
        
        try:
            history = json.loads(log_path.read_text(encoding="utf-8"))
        except Exception:
            return False, 0, "日志文件读取失败"
        
        if not history:
            return False, 0, "没有可撤销的记录"
        
        last_batch = history.pop()  # LIFO
        restored = 0
        
        for rec in last_batch:
            d = Path(rec["dir"]) if rec.get("dir") else root_dir
            a = d / rec["old"]  # 当前名（重命名后的）
            b = d / rec["new"]  # 恢复为原名
            try:
                if a.exists():
                    a.rename(b)
                    restored += 1
            except Exception as e:
                print("Undo failed:", a, "->", b, e)
        
        log_path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
        return True, restored, ""




