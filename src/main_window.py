#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主应用程序窗口
"""

import sys
import os
import time
import subprocess
import platform
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QLabel, QLineEdit, QProgressBar,
                             QTextEdit, QFileDialog, QCheckBox, QSpinBox, QGroupBox,
                             QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
                             QStatusBar, QFrame, QApplication, QDialog, QMenu)
from PyQt6.QtCore import QTimer, Qt, QUrl
from PyQt6.QtGui import QIcon, QDesktopServices, QDragEnterEvent, QDropEvent, QColor

from config.app_config import APP_NAME, APP_VERSION, get_images_path
from ui.styles.app_style import APP_STYLE
from ui.components.login_dialog import LoginDialog
from modules.common.login_manager import LoginManager
from modules.audio_extractor.extractor import AudioExtractor, ProcessResult
from modules.subtitle_renamer.renamer import SubtitleRenamer, PlanRow, truncate_filename
from modules.common.utils import find_ffmpeg, find_ffprobe


class MainWindow(QMainWindow):
    """主应用程序窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1000, 700)
        self.resize(1000, 800)
        self.setAcceptDrops(True)
        
        # 设置窗口图标
        icon_path = get_images_path() / "logo.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # 设置样式
        self.setStyleSheet(APP_STYLE)
        
        # 初始化组件
        self.audio_extractor: Optional[AudioExtractor] = None
        self.subtitle_renamer = SubtitleRenamer()
        
        # 音频提取相关状态
        self.audio_start_time = 0
        self.audio_successful_files = 0
        self.audio_failed_files = 0
        
        # 字幕重命名相关状态
        self.subtitle_root_dir: Optional[Path] = None
        self.subtitle_plan = []
        
        self.init_ui()
        self.load_settings()
    
    def _get_icon(self):
        """获取应用图标"""
        icon_path = get_images_path() / "logo.ico"
        if icon_path.exists():
            return QIcon(str(icon_path))
        return QIcon()
    
    def _show_message_box(self, message_type, title, text, parent=None):
        """显示带图标的消息框"""
        if parent is None:
            parent = self
        
        msg = QMessageBox(parent)
        msg.setWindowIcon(self._get_icon())
        msg.setWindowTitle(title)
        msg.setText(text)
        
        if message_type == "information":
            msg.setIcon(QMessageBox.Icon.Information)
        elif message_type == "warning":
            msg.setIcon(QMessageBox.Icon.Warning)
        elif message_type == "critical":
            msg.setIcon(QMessageBox.Icon.Critical)
        elif message_type == "question":
            msg.setIcon(QMessageBox.Icon.Question)
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            return msg.exec()
        
        msg.exec()
        return None
    
    def init_ui(self):
        """初始化用户界面"""
        # 创建中心widget和标签页
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标签页控件
        self.tab_widget = QTabWidget()
        
        # 创建音频提取标签页
        self.audio_tab = self.create_audio_extractor_tab()
        self.tab_widget.addTab(self.audio_tab, "🎵 音频提取")
        
        # 创建字幕重命名标签页
        self.subtitle_tab = self.create_subtitle_renamer_tab()
        self.tab_widget.addTab(self.subtitle_tab, "📝 字幕重命名")
        
        main_layout.addWidget(self.tab_widget)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("准备就绪")
        
        # 状态更新定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time_display)
    
    def create_audio_extractor_tab(self):
        """创建音频提取标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 文件选择区域
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout(file_group)
        
        # 素材文件夹选择
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("素材文件夹："))
        self.audio_input_path_edit = QLineEdit()
        self.audio_input_path_edit.setPlaceholderText("选择包含视频文件的文件夹...")
        self.audio_input_browse_btn = QPushButton("浏览...")
        self.audio_input_browse_btn.setObjectName("browse_btn")
        self.audio_input_browse_btn.clicked.connect(self.browse_audio_input_folder)
        input_layout.addWidget(self.audio_input_path_edit)
        input_layout.addWidget(self.audio_input_browse_btn)
        file_layout.addLayout(input_layout)
        
        # 导出文件夹选择
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("导出文件夹："))
        self.audio_output_path_edit = QLineEdit()
        self.audio_output_path_edit.setPlaceholderText("选择音频文件保存位置...")
        self.audio_output_browse_btn = QPushButton("浏览...")
        self.audio_output_browse_btn.setObjectName("browse_btn")
        self.audio_output_browse_btn.clicked.connect(self.browse_audio_output_folder)
        self.audio_same_folder_cb = QCheckBox("导出到原文件夹")
        self.audio_same_folder_cb.toggled.connect(self.on_audio_same_folder_toggled)
        output_layout.addWidget(self.audio_output_path_edit)
        output_layout.addWidget(self.audio_output_browse_btn)
        output_layout.addWidget(self.audio_same_folder_cb)
        file_layout.addLayout(output_layout)
        
        layout.addWidget(file_group)
        
        # 处理设置区域
        settings_group = QGroupBox("处理设置")
        settings_main_layout = QVBoxLayout(settings_group)
        
        # 单行布局：复选框和线程数设置
        settings_row_layout = QHBoxLayout()
        self.audio_keep_structure_cb = QCheckBox("保持原始目录结构")
        self.audio_keep_structure_cb.setChecked(True)
        self.audio_skip_existing_cb = QCheckBox("跳过已存在的文件")
        self.audio_skip_existing_cb.setChecked(True)
        
        settings_row_layout.addWidget(self.audio_keep_structure_cb)
        settings_row_layout.addWidget(self.audio_skip_existing_cb)
        settings_row_layout.addStretch()
        
        # 线程数设置
        thread_label = QLabel("并发线程数:")
        thread_label.setMinimumWidth(80)
        self.audio_thread_spinbox = QSpinBox()
        self.audio_thread_spinbox.setRange(1, 32)
        # 自动设置默认线程数为CPU核心数
        import multiprocessing
        cpu_count = multiprocessing.cpu_count()
        default_threads = min(max(cpu_count, 4), 16)  # 最少4个，最多16个
        self.audio_thread_spinbox.setValue(default_threads)
        self.audio_thread_spinbox.setMinimumWidth(100)
        self.audio_thread_spinbox.setMaximumWidth(140)
        self.audio_thread_spinbox.setSuffix(" 个")
        self.audio_thread_spinbox.setToolTip(f"设置并发处理的线程数量\n当前CPU核心数: {cpu_count}\n建议设置为CPU核心数的1-2倍\n默认值: {default_threads}")
        
        settings_row_layout.addWidget(thread_label)
        settings_row_layout.addWidget(self.audio_thread_spinbox)
        
        settings_main_layout.addLayout(settings_row_layout)
        layout.addWidget(settings_group)
        
        # 控制按钮区域
        control_layout = QHBoxLayout()
        self.audio_start_btn = QPushButton("开始提取")
        self.audio_start_btn.clicked.connect(self.start_audio_extraction)
        self.audio_pause_btn = QPushButton("暂停")
        self.audio_pause_btn.clicked.connect(self.pause_audio_extraction)
        self.audio_pause_btn.setEnabled(False)
        self.audio_stop_btn = QPushButton("停止")
        self.audio_stop_btn.clicked.connect(self.stop_audio_extraction)
        self.audio_stop_btn.setEnabled(False)
        
        control_layout.addWidget(self.audio_start_btn)
        control_layout.addWidget(self.audio_pause_btn)
        control_layout.addWidget(self.audio_stop_btn)
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 进度显示区域
        progress_group = QGroupBox("进度信息")
        progress_layout = QVBoxLayout(progress_group)
        
        # 整体进度
        overall_layout = QHBoxLayout()
        overall_layout.addWidget(QLabel("总体进度:"))
        self.audio_progress_bar = QProgressBar()
        self.audio_progress_bar.setRange(0, 100)
        self.audio_progress_bar.setValue(0)
        self.audio_progress_bar.setMinimumHeight(25)
        overall_layout.addWidget(self.audio_progress_bar)
        progress_layout.addLayout(overall_layout)
        
        # 当前文件信息
        self.audio_current_file_label = QLabel("等待开始...")
        self.audio_current_file_label.setStyleSheet("""
            font-weight: 600; 
            color: #656d76; 
            padding: 12px 16px;
            background-color: #f6f8fa;
            border-radius: 6px;
            font-size: 13px;
        """)
        progress_layout.addWidget(self.audio_current_file_label)
        
        # 当前文件进度
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel("当前文件:"))
        self.audio_current_file_progress = QProgressBar()
        self.audio_current_file_progress.setObjectName("current_progress")
        self.audio_current_file_progress.setRange(0, 100)
        self.audio_current_file_progress.setValue(0)
        self.audio_current_file_progress.setMinimumHeight(18)
        current_layout.addWidget(self.audio_current_file_progress)
        progress_layout.addLayout(current_layout)
        
        # 统计信息
        stats_layout = QHBoxLayout()
        self.audio_stats_label = QLabel("准备就绪")
        self.audio_time_label = QLabel("")
        stats_layout.addWidget(self.audio_stats_label)
        stats_layout.addStretch()
        stats_layout.addWidget(self.audio_time_label)
        progress_layout.addLayout(stats_layout)
        
        layout.addWidget(progress_group)
        
        # 日志区域
        log_group = QGroupBox("处理日志")
        log_layout = QVBoxLayout(log_group)
        
        self.audio_log_text = QTextEdit()
        self.audio_log_text.setMaximumHeight(150)
        log_layout.addWidget(self.audio_log_text)
        
        layout.addWidget(log_group)
        
        return tab
    
    def create_subtitle_renamer_tab(self):
        """创建字幕重命名标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 顶部：选择目录 + 选项
        top = QHBoxLayout()
        self.subtitle_dir_edit = QLineEdit()
        self.subtitle_dir_edit.setPlaceholderText("选择素材库文件夹，或直接把文件夹拖到这里…")
        subtitle_browse_btn = QPushButton("浏览…")
        subtitle_browse_btn.setObjectName("browse_btn")
        subtitle_browse_btn.clicked.connect(self.browse_subtitle_folder)
        
        self.subtitle_use_duration_cb = QCheckBox("启用时长匹配")
        self.subtitle_use_duration_cb.stateChanged.connect(self.on_subtitle_duration_toggle)
        
        top.addWidget(self.subtitle_dir_edit, 1)
        top.addWidget(subtitle_browse_btn)
        top.addWidget(self.subtitle_use_duration_cb)
        layout.addLayout(top)
        
        # 操作区
        ops = QHBoxLayout()
        self.subtitle_scan_btn = QPushButton("扫描并生成重命名计划")
        self.subtitle_scan_btn.clicked.connect(self.scan_subtitles)
        self.subtitle_apply_btn = QPushButton("开始重命名")
        self.subtitle_apply_btn.clicked.connect(self.apply_subtitle_rename)
        self.subtitle_apply_btn.setEnabled(False)
        self.subtitle_undo_btn = QPushButton("撤销上一次操作")
        self.subtitle_undo_btn.clicked.connect(self.undo_subtitle_rename)
        ops.addWidget(self.subtitle_scan_btn)
        ops.addWidget(self.subtitle_apply_btn)
        ops.addWidget(self.subtitle_undo_btn)
        layout.addLayout(ops)
        
        # 计划表
        self.subtitle_table = QTableWidget(0, 4)
        self.subtitle_table.setHorizontalHeaderLabels(["视频", "字幕", "识别结果", "字幕重命名为"])
        
        # 设置自适应列宽
        header = self.subtitle_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 视频列
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 字幕列
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)             # 识别结果列
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # 字幕重命名为列
        
        # 设置固定宽度
        self.subtitle_table.setColumnWidth(2, 150)  # 识别结果列固定150px
        
        # 设置表格属性
        self.subtitle_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.subtitle_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.subtitle_table.setAlternatingRowColors(False)
        self.subtitle_table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.subtitle_table.verticalHeader().setVisible(False)
        
        # 设置右键菜单
        self.subtitle_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.subtitle_table.customContextMenuRequested.connect(self.show_subtitle_context_menu)
        
        # 设置行高
        self.subtitle_table.verticalHeader().setDefaultSectionSize(32)
        
        layout.addWidget(self.subtitle_table, 1)
        
        return tab
    
    # ===== 拖拽支持 =====
    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
    
    def dropEvent(self, e: QDropEvent):
        urls = e.mimeData().urls()
        if not urls:
            return
        
        path = Path(urls[0].toLocalFile())
        if path.is_dir():
            # 根据当前标签页设置不同的路径
            current_tab = self.tab_widget.currentIndex()
            if current_tab == 0:  # 音频提取标签页
                self.audio_input_path_edit.setText(str(path))
                self.status_bar.showMessage(f"已选择音频提取素材文件夹：{path}")
            elif current_tab == 1:  # 字幕重命名标签页
                self.subtitle_root_dir = path
                self.subtitle_dir_edit.setText(str(path))
                self.status_bar.showMessage(f"已选择字幕重命名文件夹：{path}")
    
    # ===== 音频提取相关方法 =====
    def browse_audio_input_folder(self):
        """浏览选择音频提取输入文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择包含视频文件的文件夹", 
            self.audio_input_path_edit.text()
        )
        if folder:
            self.audio_input_path_edit.setText(folder)
    
    def browse_audio_output_folder(self):
        """浏览选择音频提取输出文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择音频文件保存文件夹", 
            self.audio_output_path_edit.text()
        )
        if folder:
            self.audio_output_path_edit.setText(folder)
    
    def on_audio_same_folder_toggled(self, checked):
        """音频提取同文件夹选项切换"""
        self.audio_output_path_edit.setEnabled(not checked)
        self.audio_output_browse_btn.setEnabled(not checked)
    
    def start_audio_extraction(self):
        """开始音频提取"""
        # 验证输入
        input_dir = self.audio_input_path_edit.text().strip()
        if not input_dir or not os.path.exists(input_dir):
            self._show_message_box("warning", "错误", "请选择有效的素材文件夹")
            return
        
        same_folder = self.audio_same_folder_cb.isChecked()
        output_dir = ""
        if not same_folder:
            output_dir = self.audio_output_path_edit.text().strip()
            if not output_dir:
                self._show_message_box("warning", "错误", "请选择输出文件夹或勾选'导出到原文件夹'")
                return
        
        # 重置统计
        self.audio_successful_files = 0
        self.audio_failed_files = 0
        self.audio_start_time = time.time()
        
        # 创建处理线程
        self.audio_extractor = AudioExtractor(
            input_dir=input_dir,
            output_dir=output_dir,
            same_folder=same_folder,
            keep_structure=self.audio_keep_structure_cb.isChecked(),
            skip_existing=self.audio_skip_existing_cb.isChecked(),
            max_threads=self.audio_thread_spinbox.value()
        )
        
        # 连接信号
        self.audio_extractor.progress_updated.connect(self.update_audio_progress)
        self.audio_extractor.file_processed.connect(self.on_audio_file_processed)
        self.audio_extractor.current_file_changed.connect(self.update_audio_current_file)
        self.audio_extractor.current_file_progress.connect(self.update_audio_current_file_progress)
        self.audio_extractor.processing_finished.connect(self.on_audio_processing_finished)
        
        # 更新UI状态
        self.audio_start_btn.setEnabled(False)
        self.audio_pause_btn.setEnabled(True)
        self.audio_stop_btn.setEnabled(True)
        self.audio_progress_bar.setValue(0)
        
        # 清空日志
        self.audio_log_text.clear()
        self.log_audio_message(f"开始处理，素材文件夹：{input_dir}")
        if not same_folder:
            self.log_audio_message(f"输出文件夹：{output_dir}")
        
        # 启动定时器和处理线程
        self.timer.start(1000)  # 每秒更新一次时间
        self.audio_extractor.start()
    
    def pause_audio_extraction(self):
        """暂停音频提取"""
        if self.audio_extractor:
            if self.audio_extractor.is_paused:
                self.audio_extractor.resume()
                self.audio_pause_btn.setText("暂停")
                self.log_audio_message("恢复处理")
            else:
                self.audio_extractor.pause()
                self.audio_pause_btn.setText("继续")
                self.log_audio_message("暂停处理")
    
    def stop_audio_extraction(self):
        """停止音频提取"""
        if self.audio_extractor:
            self.audio_extractor.stop()
            self.log_audio_message("正在停止处理...")
            
            # 等待处理线程结束，最多等待5秒
            if self.audio_extractor.isRunning():
                if not self.audio_extractor.wait(5000):  # 5秒超时
                    self.log_audio_message("强制停止处理线程")
                    self.audio_extractor.terminate()
            
            self.log_audio_message("处理已停止")
    
    def update_audio_progress(self, value):
        """更新音频提取进度条"""
        self.audio_progress_bar.setValue(value)
        
        # 更新文本显示
        total = self.audio_extractor.total_files if self.audio_extractor else 0
        processed = self.audio_extractor.processed_files if self.audio_extractor else 0
        
        self.update_audio_progress_text(processed, total, value)
    
    def update_audio_current_file(self, filename):
        """更新当前处理文件显示"""
        # 截断过长的文件名以适应显示
        display_name = filename
        if len(filename) > 50:
            display_name = f"{filename[:25]}...{filename[-20:]}"
        
        self.audio_current_file_label.setText(f"🎬 正在处理：{display_name}")
        # 重置当前文件进度条
        self.audio_current_file_progress.setValue(0)
        
        # 当开始新文件时，更新整体进度（基于已完成的文件）
        if self.audio_extractor:
            self.update_audio_overall_progress_with_current_file(0)
    
    def update_audio_current_file_progress(self, progress):
        """更新当前文件处理进度"""
        self.audio_current_file_progress.setValue(progress)
        
        # 同时更新整体进度，让其更平滑
        self.update_audio_overall_progress_with_current_file(progress)
    
    def update_audio_overall_progress_with_current_file(self, current_file_progress):
        """基于当前文件进度更新整体进度，实现平滑效果"""
        if not self.audio_extractor:
            return
            
        total_files = self.audio_extractor.total_files
        processed_files = self.audio_extractor.processed_files
        
        if total_files == 0:
            return
        
        # 计算基础进度（已完成的文件）
        base_progress = (processed_files / total_files) * 100
        
        # 计算当前文件对整体进度的贡献
        current_file_contribution = (current_file_progress / 100) * (1 / total_files) * 100
        
        # 合并计算最终进度
        overall_progress = base_progress + current_file_contribution
        overall_progress = min(100, max(0, overall_progress))  # 确保在0-100范围内
        
        # 更新进度条
        self.audio_progress_bar.setValue(int(overall_progress))
        
        # 更新统计文本
        self.update_audio_progress_text(processed_files, total_files, int(overall_progress))
    
    def update_audio_progress_text(self, processed, total, progress_value):
        """更新音频提取进度文本显示"""
        # 计算预估剩余时间
        eta_text = ""
        if processed > 0 and self.audio_start_time > 0:
            elapsed = time.time() - self.audio_start_time
            avg_time_per_file = elapsed / processed
            remaining = total - processed
            remaining_time = avg_time_per_file * remaining
            
            if remaining_time > 60:
                eta_text = f"预计剩余: {int(remaining_time // 60)}分{int(remaining_time % 60)}秒"
            else:
                eta_text = f"预计剩余: {int(remaining_time)}秒"
        
        progress_text = f"进度：{processed}/{total} 文件 ({progress_value}%)"
        if eta_text:
            progress_text += f" | {eta_text}"
            
        self.audio_stats_label.setText(progress_text)
    
    def on_audio_file_processed(self, result: ProcessResult):
        """处理单个音频文件完成"""
        if result.success:
            self.audio_successful_files += 1
            
            # 构建音频类型描述
            audio_desc = self._get_audio_type_description(result.audio_type, result.left_volume, result.right_volume)
            audio_suffix = f" - {audio_desc}" if audio_desc else ""
            
            if result.error_msg == "文件已存在，跳过":
                self.log_audio_message(f"跳过：{Path(result.input_file).name} (已存在){audio_suffix}")
            elif result.error_msg and result.error_msg.startswith("已转换为MP3"):
                # 显示转码成功信息
                reason = result.error_msg.split("(原因: ")[1].rstrip(")")
                self.log_audio_message(f"转码：{Path(result.input_file).name} → MP3 ({reason}){audio_suffix}")
            elif result.error_msg and result.error_msg.startswith("转码失败"):
                # 显示转码失败但提取成功的信息
                reason = result.error_msg.split("(原因: ")[1].rstrip(")")
                self.log_audio_message(f"成功：{Path(result.input_file).name} → {Path(result.output_file).suffix} (转码失败: {reason}){audio_suffix}")
            else:
                # 显示是直接复制还是转码
                if result.was_copied_directly:
                    self.log_audio_message(f"复制：{Path(result.input_file).name} → {Path(result.output_file).suffix} (直接复制音频流){audio_suffix}")
                else:
                    self.log_audio_message(f"转码：{Path(result.input_file).name} → {Path(result.output_file).suffix} (音频转码){audio_suffix}")
        else:
            self.audio_failed_files += 1
            audio_desc = self._get_audio_type_description(result.audio_type, result.left_volume, result.right_volume)
            audio_suffix = f" - {audio_desc}" if audio_desc else ""
            self.log_audio_message(f"失败：{Path(result.input_file).name} - {result.error_msg}{audio_suffix}")
    
    def _get_audio_type_description(self, audio_type: str, left_vol: float, right_vol: float) -> str:
        """获取音频类型的描述文字，只在异常情况时返回描述"""
        if audio_type == "true_stereo":
            return ""  # 正常立体声不显示
        elif audio_type == "pseudo_stereo_left":
            return f"⚠️ 检测到伪立体声，已转换成真立体声 (L:{left_vol:.1f}dB R:{right_vol:.1f}dB)"
        elif audio_type == "pseudo_stereo_right":
            return f"⚠️ 检测到伪立体声，已转换成真立体声 (L:{left_vol:.1f}dB R:{right_vol:.1f}dB)"
        elif audio_type == "mono":
            return f"⚠️ 检测到单声道，已转换成真立体声 (L:{left_vol:.1f}dB R:{right_vol:.1f}dB)"
        elif audio_type == "unknown":
            return f"⚠️ 检测到伪立体声，已转换成真立体声 (L:{left_vol:.1f}dB R:{right_vol:.1f}dB)"
        else:
            return f"⚠️ 检测失败，已转换 (L:{left_vol:.1f}dB R:{right_vol:.1f}dB)"
    
    def on_audio_processing_finished(self):
        """所有音频处理完成"""
        self.timer.stop()
        
        # 更新UI状态
        self.audio_start_btn.setEnabled(True)
        self.audio_pause_btn.setEnabled(False)
        self.audio_stop_btn.setEnabled(False)
        self.audio_pause_btn.setText("暂停")
        self.audio_current_file_label.setText("处理完成")
        self.audio_current_file_progress.setValue(0)  # 重置当前文件进度条
        
        # 显示完成统计
        elapsed_time = time.time() - self.audio_start_time
        total_files = self.audio_successful_files + self.audio_failed_files
        
        self.log_audio_message("=" * 50)
        self.log_audio_message(f"🎉 处理完成！")
        self.log_audio_message(f"总文件数：{total_files}")
        self.log_audio_message(f"成功：{self.audio_successful_files}")
        self.log_audio_message(f"失败：{self.audio_failed_files}")
        self.log_audio_message(f"总耗时：{elapsed_time:.1f} 秒")
        if total_files > 0:
            self.log_audio_message(f"平均速度：{total_files/elapsed_time:.1f} 文件/秒")
        
        # 弹出完成提示
        self._show_message_box(
            "information", "处理完成", 
            f"音频提取完成！\n\n"
            f"成功：{self.audio_successful_files} 个文件\n"
            f"失败：{self.audio_failed_files} 个文件\n"
            f"总耗时：{elapsed_time:.1f} 秒"
        )
    
    def log_audio_message(self, message):
        """添加音频提取日志消息"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.audio_log_text.append(formatted_message)
        
        # 自动滚动到底部
        scrollbar = self.audio_log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    # ===== 字幕重命名相关方法 =====
    def browse_subtitle_folder(self):
        """浏览选择字幕重命名文件夹"""
        d = QFileDialog.getExistingDirectory(self, "选择素材库文件夹")
        if d:
            self.subtitle_root_dir = Path(d)
            self.subtitle_dir_edit.setText(d)
            self.status_bar.showMessage(f"已选择：{d}")
    
    def on_subtitle_duration_toggle(self):
        """字幕时长匹配选项切换"""
        # 简化后的重命名器不再使用时长匹配功能
        pass
    
    def scan_subtitles(self):
        """扫描字幕和视频文件"""
        if not self.subtitle_root_dir or not self.subtitle_root_dir.exists():
            self._show_message_box("warning", APP_NAME, "请先选择有效的素材库文件夹。")
            return
        
        self.status_bar.showMessage("扫描中…")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        
        try:
            dir_files = self.subtitle_renamer.scan_files(self.subtitle_root_dir)
            self.subtitle_plan = self.subtitle_renamer.build_plan_from_grouped(dir_files)
            self.populate_subtitle_table(self.subtitle_plan)
            self.subtitle_apply_btn.setEnabled(any(r.target_name for r in self.subtitle_plan))
            
            # 统计所有目录的视频和字幕总数
            total_videos = sum(len(videos) for videos, subs in dir_files.values())
            total_subs = sum(len(subs) for videos, subs in dir_files.values())
            self.status_bar.showMessage(f"扫描完成：视频 {total_videos} 个，字幕 {total_subs} 个。")
        finally:
            QApplication.restoreOverrideCursor()
    
    def populate_subtitle_table(self, plan):
        """填充字幕重命名计划表格"""
        self.subtitle_table.setRowCount(0)
        for row in plan:
            r = self.subtitle_table.rowCount()
            self.subtitle_table.insertRow(r)
            
            # 视频文件列 - 使用截断显示
            vid_name = row.video.path.name if row.video else ""
            vid_item = QTableWidgetItem(truncate_filename(vid_name) if vid_name else "")
            if vid_name:
                vid_item.setToolTip(vid_name)  # 悬停显示完整文件名
            
            # 字幕文件列 - 使用截断显示
            sub_name = row.sub.path.name if row.sub else ""
            sub_item = QTableWidgetItem(truncate_filename(sub_name) if sub_name else "")
            if sub_name:
                sub_item.setToolTip(sub_name)  # 悬停显示完整文件名
            
            # 识别结果列 - 更新为新的标识文字
            result_text = row.reason  # 直接使用 renamer.py 中的标识文字
            result_item = QTableWidgetItem(result_text)
            
            # 字幕重命名为列 - 使用截断显示
            if row.target_name:
                rename_text = truncate_filename(row.target_name)
                rename_item = QTableWidgetItem(rename_text)
                rename_item.setToolTip(row.target_name)  # 悬停显示完整文件名
            elif row.reason == "已有字幕":
                rename_text = "无需重命名"
                rename_item = QTableWidgetItem(rename_text)
            elif row.reason == "缺少字幕文件":
                rename_text = "需要字幕文件"
                rename_item = QTableWidgetItem(rename_text)
            else:
                rename_text = ""
                rename_item = QTableWidgetItem(rename_text)
            
            # 配色：根据识别结果设置不同的提示色彩
            if not row.video:
                # 未匹配到视频：浅红色背景
                for it in (vid_item, sub_item, result_item, rename_item):
                    it.setBackground(QColor("#ffebee"))  # 浅红色背景
                    it.setForeground(QColor("#c62828"))  # 深红色文字
            elif not row.sub:
                # 缺少字幕文件：浅蓝色背景
                for it in (vid_item, sub_item, result_item, rename_item):
                    it.setBackground(QColor("#e3f2fd"))  # 浅蓝色背景
                    it.setForeground(QColor("#1565c0"))  # 蓝色文字
            elif row.reason == "确认字幕是否正确":
                # 相似度匹配：浅橙色背景提醒用户确认
                for it in (vid_item, sub_item, result_item, rename_item):
                    it.setBackground(QColor("#fff3e0"))  # 浅橙色背景
                    it.setForeground(QColor("#ef6c00"))  # 橙色文字
            elif row.reason == "已有字幕":
                # 已有字幕：浅绿色背景
                for it in (vid_item, sub_item, result_item, rename_item):
                    it.setBackground(QColor("#e8f5e8"))  # 浅绿色背景
                    it.setForeground(QColor("#2e7d32"))  # 绿色文字
            
            self.subtitle_table.setItem(r, 0, vid_item)
            self.subtitle_table.setItem(r, 1, sub_item)
            self.subtitle_table.setItem(r, 2, result_item)
            self.subtitle_table.setItem(r, 3, rename_item)
    
    def show_subtitle_context_menu(self, position):
        """显示字幕表格右键菜单"""
        item = self.subtitle_table.itemAt(position)
        if item is None:
            return
        
        row = item.row()
        if row >= len(self.subtitle_plan):
            return
        
        plan_row = self.subtitle_plan[row]
        column = item.column()
        
        menu = QMenu(self)
        
        # 根据点击的列确定文件路径
        file_path = None
        if column == 0 and plan_row.video:  # 视频文件列
            file_path = plan_row.video.path
            menu.addAction("打开视频文件位置", lambda: self.open_file_location(file_path))
        elif column == 1 and plan_row.sub:  # 字幕文件列
            file_path = plan_row.sub.path
            menu.addAction("打开字幕文件位置", lambda: self.open_file_location(file_path))
        
        # 如果有文件路径才显示菜单
        if file_path and file_path.exists():
            menu.exec(self.subtitle_table.mapToGlobal(position))
    
    def open_file_location(self, file_path):
        """打开文件位置并选中文件"""
        if not file_path or not file_path.exists():
            self._show_message_box("warning", "提示", "文件不存在或路径无效！")
            return
        
        try:
            system = platform.system()
            if system == "Windows":
                # Windows: 使用 explorer /select 命令
                subprocess.run(['explorer', '/select,', str(file_path)])
            elif system == "Darwin":  # macOS
                # macOS: 使用 open -R 命令
                subprocess.run(['open', '-R', str(file_path)])
            elif system == "Linux":
                # Linux: 使用文件管理器打开包含文件的目录
                # 先尝试使用 nautilus --select-filename
                try:
                    subprocess.run(['nautilus', '--select-filename', str(file_path)])
                except FileNotFoundError:
                    # 如果 nautilus 不可用，尝试其他文件管理器
                    try:
                        subprocess.run(['dolphin', '--select', str(file_path)])
                    except FileNotFoundError:
                        # 最后尝试用默认方式打开目录
                        subprocess.run(['xdg-open', str(file_path.parent)])
            else:
                # 未知系统，尝试用默认方式打开父目录
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(file_path.parent)))
        except FileNotFoundError:
            self._show_message_box("warning", "错误", "无法找到系统文件管理器！")
        except Exception as e:
            self._show_message_box("warning", "错误", f"无法打开文件位置：{str(e)}")
    
    def apply_subtitle_rename(self):
        """应用字幕重命名计划"""
        if not self.subtitle_plan:
            return
        
        # 预估任务数量（只计算有字幕文件的重命名任务）
        task_count = sum(1 for row in self.subtitle_plan if row.sub and row.video and row.target_name)
        
        if task_count == 0:
            self._show_message_box("information", APP_NAME, "没有可执行的重命名任务（可能存在冲突或未匹配项）。")
            return
        
        ok = self._show_message_box(
            "question", APP_NAME,
            f"将重命名 {task_count} 个字幕文件，是否继续？"
        )
        if ok != QMessageBox.StandardButton.Yes:
            return
        
        # 执行重命名
        success, conflicts, conflict_list = self.subtitle_renamer.execute_plan(self.subtitle_plan, self.subtitle_root_dir)
        
        self.status_bar.showMessage(f"重命名完成：成功 {success} 项；冲突 {conflicts} 项。")
        
        conflict_msg = ""
        if conflict_list:
            conflict_msg = f"\n\n冲突文件：\n" + "\n".join(conflict_list[:5])
            if len(conflict_list) > 5:
                conflict_msg += f"\n...等 {len(conflict_list)} 个冲突"
        
        self._show_message_box("information", APP_NAME, f"重命名完成：成功 {success} 项。{conflict_msg}\n\n若有误，可点击'撤销上一次操作'。")
        
        # 重新扫描刷新
        self.scan_subtitles()
    
    def undo_subtitle_rename(self):
        """撤销字幕重命名操作"""
        if not self.subtitle_root_dir:
            return
        
        success, restored, error_msg = self.subtitle_renamer.undo_last_operation(self.subtitle_root_dir)
        
        if success:
            self._show_message_box("information", APP_NAME, f"已撤销 {restored} 项。")
            self.scan_subtitles()  # 重新扫描
        else:
            self._show_message_box("information", APP_NAME, error_msg)
    
    # ===== 通用方法 =====
    def update_time_display(self):
        """更新时间显示"""
        if self.audio_start_time > 0:
            elapsed = time.time() - self.audio_start_time
            self.audio_time_label.setText(f"已用时：{elapsed:.0f} 秒")
    
    def load_settings(self):
        """加载设置"""
        # 这里可以添加设置加载逻辑
        pass
    
    def save_settings(self):
        """保存设置"""
        # 这里可以添加设置保存逻辑
        pass
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.audio_extractor and self.audio_extractor.isRunning():
            reply = self._show_message_box(
                "question", "确认退出", 
                "正在处理文件，确定要退出吗？"
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.audio_extractor.stop()
                self.audio_extractor.wait()  # 等待线程结束
                event.accept()
            else:
                event.ignore()
        else:
            self.save_settings()
            event.accept()


def show_message_box_with_icon(message_type, title, text, parent=None):
    """显示带图标的消息框"""
    icon_path = get_images_path() / "logo.ico"
    icon = QIcon(str(icon_path)) if icon_path.exists() else QIcon()
    
    msg = QMessageBox(parent)
    msg.setWindowIcon(icon)
    msg.setWindowTitle(title)
    msg.setText(text)
    
    if message_type == "information":
        msg.setIcon(QMessageBox.Icon.Information)
    elif message_type == "warning":
        msg.setIcon(QMessageBox.Icon.Warning)
    elif message_type == "critical":
        msg.setIcon(QMessageBox.Icon.Critical)
    
    msg.exec()


def main():
    """主函数"""
    try:
        # 设置环境变量支持中文
        if sys.platform.startswith('win'):
            os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        print("Starting application...")  # 调试信息
        
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(APP_VERSION)
        
        print("Application created successfully")  # 调试信息
        
        # 检查登录状态
        login_manager = LoginManager()
        is_logged_in, logged_phone, user_data = login_manager.check_login_status()
        
        print(f"Login status: {is_logged_in}")  # 调试信息
        
        if not is_logged_in:
            # 显示登录对话框
            login_dialog = LoginDialog()
            if login_dialog.exec() != QDialog.DialogCode.Accepted:
                # 用户取消登录或登录失败，退出程序
                print("Login cancelled or failed")
                sys.exit(0)
            
            # 获取登录后的用户数据
            user_data = login_dialog.get_user_data()
        
        # 检查ffmpeg是否可用
        print("Checking ffmpeg...")  # 调试信息
        ffmpeg_path = find_ffmpeg()
        if not ffmpeg_path:
            show_message_box_with_icon(
                "critical", "错误", 
                f"找不到 FFmpeg 程序！\n\n"
                f"请确保 ffmpeg.exe 位于程序的 bin 目录中。"
            )
            sys.exit(1)
        
        # 创建并显示主窗口
        window = MainWindow()
        
        # 如果是首次登录，显示欢迎信息
        if not is_logged_in and user_data:
            user_info = user_data.get('user_info', {})
            nickname = user_info.get('nickname', logged_phone)
            phone = user_info.get('phone', logged_phone)
            
            show_message_box_with_icon(
                "information", "欢迎使用", 
                f"🎉 欢迎使用{APP_NAME}！\n\n"
                f"登录账号：{phone}\n"
                f"昵称：{nickname if nickname else '未设置'}\n\n"
                f"感谢您使用我们的产品！\n\n"
                f"功能说明：\n"
                f"• 音频提取：从视频文件中提取高质量音频\n"
                f"• 字幕重命名：智能匹配并重命名字幕文件",
                window
            )
        
        window.show()
        
        sys.exit(app.exec())
        
    except KeyboardInterrupt:
        # 处理Ctrl+C强制退出
        print("\n程序被用户中断，正在安全退出...")
        sys.exit(0)
    except Exception as e:
        # 处理其他未预期的异常
        import traceback
        print(f"\nApplication error: {e}")
        print("Full traceback:")
        traceback.print_exc()
        print("\nPress Enter to exit...")
        input()  # 等待用户按键，防止控制台立即关闭
        sys.exit(1)


if __name__ == "__main__":
    main()
