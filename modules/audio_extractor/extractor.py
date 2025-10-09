#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频提取器模块 - 重新设计的音频处理逻辑
"""

import os
import time
import json
import subprocess
import threading
import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from queue import Queue

from PyQt6.QtCore import QThread, pyqtSignal, QMutex

from config.app_config import (
    VIDEO_EXTENSIONS, AUDIO_EXTENSIONS, MAX_FILE_SIZE_MB,
    get_bin_path
)
from modules.common.utils import find_ffmpeg, find_ffprobe


@dataclass
class AudioStreamInfo:
    """音频流信息"""
    codec: str = "unknown"
    channels: int = 0
    sample_rate: int = 0
    duration: float = 0.0
    stream_index: int = 0


@dataclass
class VolumeAnalysis:
    """音量分析结果"""
    left_volume: float = -60.0
    right_volume: float = -60.0
    audio_type: str = "unknown"  # true_stereo, pseudo_stereo_left, pseudo_stereo_right, mono, no_audio
    detection_position: str = "unknown"  # 检测位置：开头/中间/结尾


@dataclass
class ProcessingDecision:
    """处理决策"""
    can_copy_directly: bool = False
    needs_channel_fix: bool = False
    target_format: str = "aac"
    processing_reason: str = ""


@dataclass
class ProcessResult:
    """处理结果数据类"""
    success: bool
    input_file: str
    output_file: str
    error_msg: str = ""
    processing_time: float = 0.0
    audio_type: str = "unknown"
    left_volume: float = -30.0
    right_volume: float = -30.0
    was_copied_directly: bool = False
    processing_decision: str = ""


@dataclass
class FileItem:
    """文件项数据类"""
    path: Path
    stem: str
    ext: str
    duration: Optional[float] = None


class AudioExtractor(QThread):
    """音频提取工作线程 - 重新设计"""
    
    # 信号定义
    progress_updated = pyqtSignal(int)
    file_processed = pyqtSignal(ProcessResult)
    current_file_changed = pyqtSignal(str)
    current_file_progress = pyqtSignal(int)
    processing_finished = pyqtSignal()
    
    # 音频检测常量
    SILENCE_THRESHOLD = -50.0  # 使用-50dB作为静音阈值
    COMPLETE_SILENCE_THRESHOLD = -80.0  # 完全静音阈值
    
    def __init__(self, input_dir: str, output_dir: str, 
                 same_folder: bool = False, keep_structure: bool = True,
                 skip_existing: bool = True, max_threads: int = 4):
        super().__init__()
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir) if not same_folder else None
        self.same_folder = same_folder
        self.keep_structure = keep_structure
        self.skip_existing = skip_existing
        self.max_threads = max_threads
        self.logger = logging.getLogger(__name__)
        
        self.video_files: List[Path] = []
        self.total_files = 0
        self.processed_files = 0
        self.is_paused = False
        self.is_stopped = False
        
        # 获取ffmpeg路径
        self.ffmpeg_path = find_ffmpeg()
        self.ffprobe_path = find_ffprobe()
        
        # 文件大小限制 (MB转字节)
        self.max_file_size = MAX_FILE_SIZE_MB * 1024 * 1024
        
        # 线程锁和当前文件管理
        self.mutex = QMutex()
        self.current_active_file = None
        self.active_processes = []
    
    def scan_video_files(self) -> List[Path]:
        """扫描视频文件"""
        video_files = []
        
        def scan_directory(directory: Path):
            try:
                for item in directory.iterdir():
                    if item.is_file() and item.suffix.lower() in VIDEO_EXTENSIONS:
                        video_files.append(item)
                    elif item.is_dir():
                        scan_directory(item)
            except PermissionError:
                self.logger.warning(f"无权限访问目录: {directory}")
        
        scan_directory(self.input_dir)
        return sorted(video_files)
    
    # ==================== 新的音频流分析逻辑 ====================
    
    def get_audio_stream_info(self, video_file: Path) -> Optional[AudioStreamInfo]:
        """获取音频流基本信息"""
        try:
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-select_streams", "a:0",  # 选择第一个音频流
                "-show_entries", "stream=codec_name,channels,sample_rate,duration:format=duration",
                "-of", "json",
                str(video_file)
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                streams = data.get('streams', [])
                format_info = data.get('format', {})
                
                if streams:
                    stream = streams[0]
                    return AudioStreamInfo(
                        codec=stream.get('codec_name', 'unknown'),
                        channels=int(stream.get('channels', 0)),
                        sample_rate=int(stream.get('sample_rate', 0)),
                        duration=float(stream.get('duration', 0) or format_info.get('duration', 0)),
                        stream_index=0
                    )
                    
        except Exception as e:
            self.logger.warning(f"获取音频流信息失败 {video_file.name}: {e}")
            
        return None
    
    def detect_pseudo_stereo(self, video_file: Path, stream_info: AudioStreamInfo) -> VolumeAnalysis:
        """
        检测伪立体声 - 使用-50dB阈值
        检测策略：
        1. 视频≥1分钟检测前1分钟，<1分钟检测10秒
        2. 检测位置：只检测一个位置（优先中间位置）
        3. 阈值判断：-50dB为静音，-80dB为完全静音
        """
        try:
            duration = stream_info.duration
            
            # 确定检测时长
            if duration >= 60:
                detection_duration = 60  # 1分钟
            else:
                detection_duration = min(10, max(5, duration))  # 10秒或实际时长
            
            # 确定检测位置：优先选择中间位置，如果视频太短则选择开头
            if duration > detection_duration * 1.5:
                # 视频足够长，检测中间位置
                start_time = max(0, (duration - detection_duration) / 2)
                position_name = "中间"
            else:
                # 视频较短，检测开头
                start_time = 0
                position_name = "开头"
            
            # 执行检测
            left_vol, right_vol = self._detect_position_volumes(
                video_file, stream_info.stream_index, start_time, detection_duration
            )
            
            print(f"[音频检测] {video_file.name} - {position_name}位置({start_time:.1f}s): 左={left_vol:.1f}dB, 右={right_vol:.1f}dB")
            self.logger.info(f"音频检测 - {position_name}: 左={left_vol:.1f}dB, 右={right_vol:.1f}dB")
            
            # 判断音频类型
            audio_type = self._determine_audio_type(left_vol, right_vol)
            print(f"[音频判断] {audio_type} (阈值: {self.SILENCE_THRESHOLD}dB)")
            
            return VolumeAnalysis(
                left_volume=left_vol,
                right_volume=right_vol,
                audio_type=audio_type,
                detection_position=position_name
            )
            
        except Exception as e:
            self.logger.warning(f"伪立体声检测失败 {video_file.name}: {e}")
            return VolumeAnalysis(
                left_volume=-60.0,
                right_volume=-60.0,
                audio_type="unknown",
                detection_position="检测失败"
            )
    
    def _detect_position_volumes(self, video_file: Path, stream_index: int, 
                                start_time: float, duration: float) -> Tuple[float, float]:
        """检测指定位置的左右声道音量"""
        try:
            cmd = [
                self.ffmpeg_path,
                "-ss", str(start_time),
                "-i", str(video_file),
                "-map", f"0:a:{stream_index}",
                "-af", "astats",
                "-f", "null",
                "-t", str(duration),
                "-"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=duration + 10,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            left_rms = -60.0
            right_rms = -60.0
            
            if result.stderr:
                lines = result.stderr.split('\n')
                current_channel = None
                
                for line in lines:
                    line = line.strip()
                    
                    # 检测通道
                    if 'Overall' in line:
                        current_channel = 'overall'
                    elif 'Channel: 1' in line or 'Channel 0' in line or 'FL' in line:
                        current_channel = 'left'
                    elif 'Channel: 2' in line or 'Channel 1' in line or 'FR' in line:
                        current_channel = 'right'
                    
                    # 提取RMS音量
                    if 'RMS level dB:' in line and current_channel:
                        try:
                            rms_str = line.split('RMS level dB:')[1].strip()
                            rms_value = float(rms_str)
                            
                            if current_channel == 'left':
                                left_rms = rms_value
                            elif current_channel == 'right':
                                right_rms = rms_value
                                
                        except:
                            pass
            
            return left_rms, right_rms
            
        except Exception:
            return -60.0, -60.0
    
    def _determine_audio_type(self, left_vol: float, right_vol: float) -> str:
        """
        根据音量判断音频类型
        使用-50dB作为静音阈值
        """
        # 检测失败的情况
        if left_vol == -60.0 and right_vol == -60.0:
            return "unknown"
        
        # 完全静音
        if left_vol < self.COMPLETE_SILENCE_THRESHOLD and right_vol < self.COMPLETE_SILENCE_THRESHOLD:
            return "no_audio"
        
        # 伪立体声检测（使用-50dB阈值）
        if left_vol < self.SILENCE_THRESHOLD and right_vol >= self.SILENCE_THRESHOLD:
            return "pseudo_stereo_right"  # 只有右声道有声音
        elif right_vol < self.SILENCE_THRESHOLD and left_vol >= self.SILENCE_THRESHOLD:
            return "pseudo_stereo_left"   # 只有左声道有声音
        elif left_vol >= self.SILENCE_THRESHOLD and right_vol >= self.SILENCE_THRESHOLD:
            return "true_stereo"          # 正常立体声
        else:
            return "mono"                 # 单声道或其他情况
    
    # ==================== 处理决策逻辑 ====================
    
    def make_processing_decision(self, video_file: Path, stream_info: AudioStreamInfo, 
                               volume_analysis: VolumeAnalysis) -> ProcessingDecision:
        """
        制定处理决策
        决策流程：
        1. 检测音频格式是否支持
        2. 检测是否需要修复伪立体声
        3. 确定最终输出格式
        """
        # 获取原始音频格式
        original_ext = f".{stream_info.codec}"
        if stream_info.codec in ['aac', 'mp3', 'ac3']:
            original_ext = f".{stream_info.codec}"
        else:
            original_ext = ".aac"  # 默认格式
        
        # 检查格式支持
        format_supported = original_ext.lower() in AUDIO_EXTENSIONS
        
        # 检查是否需要声道修复
        needs_channel_fix = volume_analysis.audio_type in ["pseudo_stereo_left", "pseudo_stereo_right"]
        
        # 检查是否可以直接复制
        can_copy_directly = (
            volume_analysis.audio_type == "true_stereo" and
            stream_info.channels >= 2 and
            format_supported and
            not stream_info.codec.startswith('pcm_')  # PCM需要转码
        )
        
        # 确定目标格式
        if can_copy_directly:
            target_format = stream_info.codec
        elif format_supported and not needs_channel_fix:
            target_format = stream_info.codec
        else:
            target_format = "aac"  # 默认转为AAC
        
        # 生成处理原因
        reasons = []
        if volume_analysis.audio_type == "no_audio":
            reasons.append("视频无音频")
        elif volume_analysis.audio_type == "unknown":
            reasons.append("音频检测失败")
        elif needs_channel_fix:
            reasons.append(f"伪立体声合并声道({volume_analysis.audio_type})")
        elif not format_supported:
            reasons.append(f"格式不支持({stream_info.codec})")
        elif stream_info.codec.startswith('pcm_'):
            reasons.append("PCM需要转码")
        elif can_copy_directly:
            reasons.append("直接复制音频流")
        else:
            reasons.append("标准转码")
        
        processing_reason = "; ".join(reasons)
        
        print(f"[处理决策] {video_file.name}")
        print(f"  - 音频类型: {volume_analysis.audio_type}")
        print(f"  - 原始格式: {stream_info.codec} ({stream_info.channels}声道)")
        print(f"  - 格式支持: {format_supported}")
        print(f"  - 需要声道修复: {needs_channel_fix}")
        print(f"  - 可直接复制: {can_copy_directly}")
        print(f"  - 目标格式: {target_format}")
        print(f"  - 处理原因: {processing_reason}")
        
        return ProcessingDecision(
            can_copy_directly=can_copy_directly,
            needs_channel_fix=needs_channel_fix,
            target_format=target_format,
            processing_reason=processing_reason
        )
    
    # ==================== 音频处理执行逻辑 ====================
    
    def extract_audio(self, video_file: Path) -> ProcessResult:
        """主要的音频提取逻辑 - 重新设计"""
        start_time = time.time()
        
        try:
            # 第一步：获取音频流信息
            stream_info = self.get_audio_stream_info(video_file)
            if not stream_info:
                return ProcessResult(
                    success=False,
                    input_file=str(video_file),
                    output_file="",
                    error_msg="无法获取音频流信息",
                    processing_time=time.time() - start_time
                )
            
            # 第二步：检测伪立体声
            volume_analysis = self.detect_pseudo_stereo(video_file, stream_info)
            
            # 特殊处理：检查是否需要提示用户
            if (volume_analysis.left_volume < self.SILENCE_THRESHOLD and 
                volume_analysis.right_volume < self.SILENCE_THRESHOLD):
                print(f"[警告] {video_file.name} - 音频音量过低，请检查视频是否有声音")
                self.logger.warning(f"音频音量过低: 左={volume_analysis.left_volume:.1f}dB, 右={volume_analysis.right_volume:.1f}dB")
            
            # 第三步：制定处理决策
            decision = self.make_processing_decision(video_file, stream_info, volume_analysis)
            
            # 第四步：确定输出文件路径
            output_file = self._get_output_path(video_file, decision.target_format)
            
            # 检查是否跳过已存在的文件
            if self.skip_existing and output_file.exists():
                return ProcessResult(
                    success=True,
                    input_file=str(video_file),
                    output_file=str(output_file),
                    processing_time=time.time() - start_time,
                    audio_type=volume_analysis.audio_type,
                    left_volume=volume_analysis.left_volume,
                    right_volume=volume_analysis.right_volume,
                    was_copied_directly=False,
                    processing_decision="跳过已存在文件"
                )
            
            # 第五步：执行音频处理
            success = self._execute_audio_processing(
                video_file, output_file, stream_info, volume_analysis, decision
            )
            
            if success:
                # 第六步：检查输出文件大小，如果超过500MB则转为MP3
                final_output = self._check_and_compress_if_needed(output_file, video_file, stream_info.duration)
                
                return ProcessResult(
                    success=True,
                    input_file=str(video_file),
                    output_file=str(final_output),
                    processing_time=time.time() - start_time,
                    audio_type=volume_analysis.audio_type,
                    left_volume=volume_analysis.left_volume,
                    right_volume=volume_analysis.right_volume,
                    was_copied_directly=decision.can_copy_directly,
                    processing_decision=decision.processing_reason
                )
            else:
                return ProcessResult(
                    success=False,
                    input_file=str(video_file),
                    output_file=str(output_file),
                    error_msg="音频处理执行失败",
                    processing_time=time.time() - start_time,
                    audio_type=volume_analysis.audio_type,
                    left_volume=volume_analysis.left_volume,
                    right_volume=volume_analysis.right_volume,
                    processing_decision=decision.processing_reason
                )
                
        except Exception as e:
            return ProcessResult(
                success=False,
                input_file=str(video_file),
                output_file="",
                error_msg=f"音频提取异常: {str(e)}",
                processing_time=time.time() - start_time
            )
    
    def _execute_audio_processing(self, video_file: Path, output_file: Path, 
                                 stream_info: AudioStreamInfo, volume_analysis: VolumeAnalysis,
                                 decision: ProcessingDecision) -> bool:
        """执行音频处理"""
        try:
            # 确保输出目录存在
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 构建FFmpeg命令
            if decision.can_copy_directly:
                # 直接复制音频流
                cmd = [
                    self.ffmpeg_path,
                    "-i", str(video_file),
                    "-map", "0:a:0",
                    "-vn",
                    "-c:a", "copy",
                    "-progress", "pipe:1",
                    "-v", "warning",
                    "-y",
                    str(output_file)
                ]
            elif decision.needs_channel_fix:
                # 需要修复伪立体声 - 合并两个声道
                # 将左右声道混合后输出到两个声道，避免因误判而丢失音频
                # 例如：对话场景中，即使开头只有一人说话，后续另一人说话时也不会丢失
                audio_filter = "pan=stereo|c0=0.5*c0+0.5*c1|c1=0.5*c0+0.5*c1"
                
                cmd = [
                    self.ffmpeg_path,
                    "-i", str(video_file),
                    "-map", "0:a:0",
                    "-vn",
                    "-af", audio_filter,
                    "-c:a", "aac",
                    "-b:a", "128k",
                    "-progress", "pipe:1",
                    "-v", "warning",
                    "-y",
                    str(output_file)
                ]
            else:
                # 标准转码
                cmd = [
                    self.ffmpeg_path,
                    "-i", str(video_file),
                    "-map", "0:a:0",
                    "-vn",
                    "-c:a", decision.target_format,
                    "-progress", "pipe:1",
                    "-v", "warning",
                    "-y",
                    str(output_file)
                ]
                
                # 为AAC添加码率设置
                if decision.target_format == "aac":
                    cmd.insert(-4, "-b:a")
                    cmd.insert(-4, "128k")
            
            # 执行命令并监控进度
            return self._run_ffmpeg_with_progress(cmd, video_file, stream_info.duration)
            
        except Exception as e:
            self.logger.error(f"音频处理执行失败 {video_file.name}: {e}")
            return False
    
    def _run_ffmpeg_with_progress(self, cmd: List[str], video_file: Path, duration: float) -> bool:
        """运行FFmpeg并监控进度"""
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # 添加到活跃进程列表
            self.mutex.lock()
            self.active_processes.append(process)
            self.mutex.unlock()
            
            last_progress = 0
            
            # 监控进度
            while True:
                if self.is_stopped:
                    process.terminate()
                    break
                    
                output = process.stdout.readline()
                if not output and process.poll() is not None:
                    break
                
                if output.startswith('out_time_ms='):
                    try:
                        current_time = int(output.split('=')[1]) / 1000000.0
                        if duration > 0:
                            progress = min(100, int((current_time / duration) * 100))
                            if progress > last_progress:
                                last_progress = progress
                                # 只有当前活跃文件才发射进度信号
                                self.mutex.lock()
                                is_active = self.current_active_file == str(video_file)
                                self.mutex.unlock()
                                if is_active:
                                    self.current_file_progress.emit(progress)
                    except:
                        pass
                elif output.startswith('progress=end'):
                    self.mutex.lock()
                    is_active = self.current_active_file == str(video_file)
                    self.mutex.unlock()
                    if is_active:
                        self.current_file_progress.emit(100)
            
            # 获取结果
            _, stderr = process.communicate()
            
            # 从活跃进程列表移除
            self.mutex.lock()
            if process in self.active_processes:
                self.active_processes.remove(process)
            self.mutex.unlock()
            
            return process.returncode == 0
            
        except Exception as e:
            self.logger.error(f"FFmpeg执行异常: {e}")
            return False
    
    def _check_and_compress_if_needed(self, output_file: Path, video_file: Path, duration: float) -> Path:
        """检查文件大小，如果超过500MB则压缩为MP3"""
        try:
            if not output_file.exists():
                return output_file
            
            file_size = output_file.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            if file_size > self.max_file_size:
                print(f"[文件压缩] {output_file.name} 大小 {file_size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB，转换为MP3")
                
                # 生成MP3文件路径
                mp3_output = output_file.with_suffix('.mp3')
                
                # 转换为MP3
                cmd = [
                    self.ffmpeg_path,
                    "-i", str(output_file),
                    "-c:a", "mp3",
                    "-b:a", "128k",
                    "-progress", "pipe:1",
                    "-v", "warning",
                    "-y",
                    str(mp3_output)
                ]
                
                if self._run_ffmpeg_with_progress(cmd, video_file, duration):
                    # 删除原文件
                    try:
                        output_file.unlink()
                    except:
                        pass
                    return mp3_output
                else:
                    print(f"[压缩失败] 保留原文件: {output_file.name}")
                    return output_file
            
            return output_file
            
        except Exception as e:
            self.logger.warning(f"文件大小检查失败: {e}")
            return output_file
    
    def _get_output_path(self, video_file: Path, target_format: str) -> Path:
        """获取输出文件路径"""
        if target_format in ['aac', 'mp3', 'ac3', 'flac', 'ogg', 'wav']:
            ext = f".{target_format}"
        else:
            ext = ".aac"  # 默认扩展名
        
        if self.same_folder:
            return video_file.parent / f"{video_file.stem}{ext}"
        else:
            if self.keep_structure:
                relative_path = video_file.relative_to(self.input_dir)
                output_path = self.output_dir / relative_path.parent / f"{video_file.stem}{ext}"
            else:
                output_path = self.output_dir / f"{video_file.stem}{ext}"
            
            return output_path
    
    # ==================== 多线程处理逻辑 ====================
    
    def run(self):
        """主运行逻辑"""
        try:
            # 扫描视频文件
            self.video_files = self.scan_video_files()
            self.total_files = len(self.video_files)
            
            if self.total_files == 0:
                self.processing_finished.emit()
                return
            
            # 使用线程池处理文件
            thread_pool = []
            file_queue = Queue()
            
            # 将文件添加到队列
            for video_file in self.video_files:
                file_queue.put(video_file)
            
            # 启动工作线程
            for i in range(min(self.max_threads, self.total_files)):
                thread = threading.Thread(target=self._worker_thread, args=(file_queue,))
                thread.daemon = True
                thread.start()
                thread_pool.append(thread)
            
            # 等待所有线程完成
            for thread in thread_pool:
                thread.join()
            
            self.processing_finished.emit()
            
        except Exception as e:
            self.logger.error(f"处理过程异常: {e}")
            self.processing_finished.emit()
    
    def _worker_thread(self, file_queue: Queue):
        """工作线程"""
        while not file_queue.empty() and not self.is_stopped:
            try:
                video_file = file_queue.get_nowait()
            except:
                break
            
            # 暂停检查
            while self.is_paused and not self.is_stopped:
                time.sleep(0.1)
            
            if self.is_stopped:
                break
            
            # 设置当前活跃文件
            self.mutex.lock()
            self.current_active_file = str(video_file)
            self.mutex.unlock()
            
            # 发射当前文件变化信号
            self.current_file_changed.emit(video_file.name)
            
            # 处理文件
            result = self.extract_audio(video_file)
            
            # 发射处理完成信号
            self.file_processed.emit(result)
            
            # 更新总体进度
            self.mutex.lock()
            self.processed_files += 1
            progress = int((self.processed_files / self.total_files) * 100)
            self.mutex.unlock()
            
            self.progress_updated.emit(progress)
    
    # ==================== 控制方法 ====================
    
    def pause(self):
        """暂停处理"""
        self.is_paused = True
    
    def resume(self):
        """恢复处理"""
        self.is_paused = False
    
    def stop(self):
        """停止处理"""
        self.is_stopped = True
        
        # 终止所有活跃进程
        self.mutex.lock()
        for process in self.active_processes[:]:
            try:
                process.terminate()
            except:
                pass
        self.active_processes.clear()
        self.mutex.unlock()