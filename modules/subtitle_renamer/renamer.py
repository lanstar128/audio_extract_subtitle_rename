#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字幕重命名器模块
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from rapidfuzz import fuzz

from config.app_config import VIDEO_EXTENSIONS, SUBTITLE_EXTENSIONS, LOG_FILE_NAME
from modules.common.utils import extract_episode_tokens, get_media_duration


@dataclass
class FileItem:
    """文件项数据类"""
    path: Path
    stem: str
    ext: str
    episodes: List[int]
    duration: Optional[float] = None


@dataclass
class PlanRow:
    """重命名计划行"""
    sub: FileItem
    video: Optional[FileItem]
    target_name: Optional[str]
    reason: str  # 匹配说明/跳过原因


class SubtitleRenamer:
    """字幕重命名器"""
    
    def __init__(self, use_duration: bool = False):
        self.use_duration = use_duration
    
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
                    ext=ext, 
                    episodes=extract_episode_tokens(p.stem)
                )
                
                # 如果启用了时长匹配且是视频文件，获取时长
                if self.use_duration and ext in VIDEO_EXTENSIONS:
                    item.duration = get_media_duration(p)
                
                if ext in VIDEO_EXTENSIONS:
                    videos.append(item)
                else:
                    subs.append(item)
        
        return videos, subs
    
    def build_plan(self, videos: List[FileItem], subs: List[FileItem]) -> List[PlanRow]:
        """构建重命名计划"""
        plan: List[PlanRow] = []
        video_by_episode: Dict[int, List[FileItem]] = {}
        
        # 按剧集编号分组视频
        for v in videos:
            for ep in v.episodes:
                video_by_episode.setdefault(ep, []).append(v)
        
        for s in subs:
            matched: Optional[FileItem] = None
            reason = ""
            
            # 1) 先尝试剧集编号匹配
            for ep in s.episodes:
                if ep in video_by_episode:
                    candidates = video_by_episode[ep]
                    # 若有多个候选，按与字幕同目录优先、再按模糊度
                    candidates_sorted = sorted(
                        candidates,
                        key=lambda v: (
                            0 if v.path.parent == s.path.parent else 1,
                            -fuzz.ratio(v.stem, s.stem)
                        )
                    )
                    matched = candidates_sorted[0]
                    reason = f"编号匹配(E{ep})"
                    break
            
            # 2) 再做模糊匹配
            if not matched:
                best_v = None
                best_score = -1
                for v in videos:
                    score = fuzz.token_set_ratio(v.stem, s.stem)
                    # 同目录加成
                    if v.path.parent == s.path.parent:
                        score += 5
                    if score > best_score:
                        best_score, best_v = score, v
                if best_v and best_score >= 60:  # 经验阈值
                    matched = best_v
                    reason = f"模糊匹配(相似度 {best_score})"
            
            # 3) 可选时长匹配
            if self.use_duration and matched and matched.duration is not None:
                # 这里可以进一步验证时长匹配
                # 字幕文件时长估算需要解析字幕内容，暂时跳过
                pass
            
            if matched:
                new_stem = matched.stem
                target = str(s.path.with_name(new_stem + s.ext).name)
                plan.append(PlanRow(sub=s, video=matched, target_name=target, reason=reason))
            else:
                plan.append(PlanRow(sub=s, video=None, target_name=None, reason="未匹配到视频，保留原名"))
        
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
            if not row.video or not row.target_name:
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
