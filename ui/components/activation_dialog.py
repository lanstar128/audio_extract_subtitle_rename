#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
激活对话框组件
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QMessageBox,
                             QDialogButtonBox)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QIcon, QDesktopServices

from pathlib import Path
from config.app_config import get_images_path
from modules.common.activation import ActivationManager


class ActivationDialog(QDialog):
    """激活对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.activation_manager = ActivationManager()
        self.init_ui()
    
    def _get_icon(self):
        """获取应用图标"""
        icon_path = get_images_path() / "video_audio_extractor.png"
        if icon_path.exists():
            return QIcon(str(icon_path))
        return QIcon()
    
    def _show_message_box(self, message_type, title, text):
        """显示带图标的消息框"""
        msg = QMessageBox(self)
        msg.setWindowIcon(self._get_icon())
        msg.setWindowTitle(title)
        msg.setText(text)
        
        if message_type == "information":
            msg.setIcon(QMessageBox.Icon.Information)
        elif message_type == "warning":
            msg.setIcon(QMessageBox.Icon.Warning)
        elif message_type == "critical":
            msg.setIcon(QMessageBox.Icon.Critical)
        
        msg.exec()
    
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("软件激活")
        self.setFixedSize(500, 690)
        self.setModal(True)
        
        # 设置窗口图标
        icon_path = get_images_path() / "video_audio_extractor.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            
            QLabel {
                color: #1a1a1a;
                font-size: 13px;
            }
            
            QLabel#title_label {
                font-size: 18px;
                font-weight: bold;
                color: #007AFF;
                margin: 20px 0;
            }
            
            QLabel#subtitle_label {
                font-size: 14px;
                color: #666;
                margin-bottom: 20px;
            }
            
            QLineEdit {
                background-color: #ffffff;
                border: 2px solid #d0d7de;
                border-radius: 6px;
                padding: 12px 16px;
                font-size: 14px;
                color: #1a1a1a;
            }
            
            QLineEdit:focus {
                border-color: #007AFF;
                outline: none;
            }
            
            QPushButton {
                background-color: #007AFF;
                border: none;
                color: #ffffff;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                min-height: 16px;
            }
            
            QPushButton:hover {
                background-color: #0056CC;
            }
            
            QPushButton:pressed {
                background-color: #004999;
            }
            
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #a8a8a8;
                border: 1px solid #e1e5e9;
            }
            
            /* 广告区域样式 */
            #ad_container {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #f8f9fa, stop:1 #e9ecef);
                border: 2px solid #007AFF;
                border-radius: 12px;
                padding: 20px;
                margin: 15px 0;
            }
            
            #ad_title {
                font-size: 16px;
                font-weight: bold;
                color: #007AFF;
                margin-bottom: 8px;
            }
            
            #ad_subtitle {
                font-size: 14px;
                color: #495057;
                margin-bottom: 12px;
                line-height: 1.4;
            }
            
            #ad_features {
                font-size: 13px;
                color: #6c757d;
                margin-bottom: 15px;
                line-height: 1.6;
            }
            
            #ad_button {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #28a745, stop:1 #20c997);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                min-height: 14px;
            }
            
            #ad_button:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #218838, stop:1 #1e7e34);
            }
            
            #ad_button:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #1e7e34, stop:1 #155724);
            }
        """)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("视频处理工具集")
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 副标题
        subtitle_label = QLabel("请输入您的手机号和激活码来激活软件")
        subtitle_label.setObjectName("subtitle_label")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)
        
        # 输入区域
        input_layout = QVBoxLayout()
        input_layout.setSpacing(15)
        
        # 手机号输入
        phone_label = QLabel("手机号：")
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("请输入您的11位手机号...")
        self.phone_input.textChanged.connect(self.on_input_changed)
        input_layout.addWidget(phone_label)
        input_layout.addWidget(self.phone_input)
        
        # 激活码输入
        code_label = QLabel("激活码：")
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("请输入激活码，格式：XXXX-XXXX-XXXX")
        self.code_input.textChanged.connect(self.on_input_changed)
        input_layout.addWidget(code_label)
        input_layout.addWidget(self.code_input)
        
        layout.addLayout(input_layout)
        
        # 广告区域
        ad_container = QFrame()
        ad_container.setObjectName("ad_container")
        ad_layout = QVBoxLayout(ad_container)
        ad_layout.setSpacing(8)
        
        # 广告标题
        ad_title = QLabel("🎬 智剪大师 - 知识博主专业剪辑神器")
        ad_title.setObjectName("ad_title")
        ad_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ad_layout.addWidget(ad_title)
        
        # 广告副标题
        ad_subtitle = QLabel("告别繁琐剪辑，0.1秒精准定位金句，让创作效率提升10倍！")
        ad_subtitle.setObjectName("ad_subtitle")
        ad_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ad_subtitle.setWordWrap(True)
        ad_layout.addWidget(ad_subtitle)
        
        # 特色功能
        features_text = ("⚡ 毫秒级素材检索，海量视频瞬间定位\n"
                        "🎯 智能字幕搜索，金句提取一键完成\n"
                        "🧩 跨源混剪拼接，释放无限创意可能")
        ad_features = QLabel(features_text)
        ad_features.setObjectName("ad_features")
        ad_features.setAlignment(Qt.AlignmentFlag.AlignLeft)
        ad_layout.addWidget(ad_features)
        
        # 广告按钮
        ad_button = QPushButton("🚀 立即了解智剪大师")
        ad_button.setObjectName("ad_button")
        ad_button.clicked.connect(self.open_zhijian_website)
        ad_layout.addWidget(ad_button)
        
        layout.addWidget(ad_container)
        
        # 说明文字
        info_label = QLabel("💡 激活码由我们在您购买产品时提供，如有疑问请联系客服")
        info_label.setStyleSheet("color: #666; font-size: 12px; margin: 10px 0;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 按钮区域
        button_box = QDialogButtonBox()
        self.activate_btn = QPushButton("激活软件")
        self.activate_btn.clicked.connect(self.activate_software)
        self.activate_btn.setEnabled(False)
        
        self.exit_btn = QPushButton("退出")
        self.exit_btn.clicked.connect(self.reject)
        
        button_box.addButton(self.activate_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton(self.exit_btn, QDialogButtonBox.ButtonRole.RejectRole)
        
        layout.addWidget(button_box)
        
        layout.addStretch()
    
    def on_input_changed(self):
        """输入内容变化时检查"""
        phone = self.phone_input.text().strip()
        code = self.code_input.text().strip()
        
        # 过滤手机号，只保留数字
        phone_digits = ''.join(c for c in phone if c.isdigit())
        if phone_digits != phone:
            self.phone_input.setText(phone_digits)
            return
        
        # 检查是否可以激活
        can_activate = (
            len(phone_digits) == 11 and 
            phone_digits.startswith(('13', '14', '15', '16', '17', '18', '19')) and
            len(code.replace('-', '').replace(' ', '')) >= 12
        )
        
        self.activate_btn.setEnabled(can_activate)
    
    def activate_software(self):
        """激活软件"""
        phone = self.phone_input.text().strip()
        code = self.code_input.text().strip()
        
        # 验证激活码
        success, message = self.activation_manager.verify_activation(phone, code)
        
        if success:
            # 保存激活状态
            if self.activation_manager.save_activation_status(phone):
                self._show_message_box(
                    "information", "激活成功", 
                    f"🎉 软件激活成功！\n\n手机号：{phone}\n\n您现在可以开始使用软件了。"
                )
                self.accept()
            else:
                # 保存失败，提供详细的解决方案
                error_message = (
                    "❌ 激活验证成功，但保存激活状态失败！\n\n"
                    "可能的原因和解决方案：\n"
                    "1. 权限不足：请尝试以管理员身份运行程序\n"
                    "2. 磁盘空间不足：请清理磁盘空间\n"
                    "3. 安全软件阻止：请暂时关闭杀毒软件\n"
                    "4. 文件被占用：请重启程序后重试\n\n"
                    f"配置文件路径：{self.activation_manager.config_file}\n\n"
                    "如果问题持续，请联系技术支持。"
                )
                
                reply = self._show_message_box_with_retry(
                    "warning", "保存失败", error_message
                )
                
                if reply == "retry":
                    # 用户选择重试
                    self.activate_software()
                elif reply == "admin":
                    # 尝试以管理员身份运行
                    if self.activation_manager.is_admin():
                        # 已经是管理员，显示其他解决方案
                        self._show_message_box(
                            "information", "提示", 
                            "程序已经以管理员身份运行。\n\n"
                            "请检查：\n"
                            "1. 磁盘空间是否充足\n"
                            "2. 安全软件是否阻止文件写入\n"
                            "3. 文件是否被其他程序占用\n\n"
                            "您可以尝试重启程序后再次激活。"
                        )
                    else:
                        # 提示用户以管理员身份运行
                        self._show_admin_run_instructions()
        else:
            self._show_message_box("warning", "激活失败", f"❌ {message}\n\n请检查您的手机号和激活码是否正确。")
    
    def _show_message_box_with_retry(self, message_type, title, text):
        """显示带重试选项的消息框"""
        from PyQt6.QtWidgets import QPushButton
        
        msg = QMessageBox(self)
        msg.setWindowIcon(self._get_icon())
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.Icon.Warning)
        
        # 添加自定义按钮
        retry_btn = msg.addButton("重试", QMessageBox.ButtonRole.AcceptRole)
        admin_btn = msg.addButton("以管理员身份运行", QMessageBox.ButtonRole.HelpRole)
        cancel_btn = msg.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        
        msg.exec()
        
        if msg.clickedButton() == retry_btn:
            return "retry"
        elif msg.clickedButton() == admin_btn:
            return "admin"
        else:
            return "cancel"
    
    def _show_admin_run_instructions(self):
        """显示管理员运行说明"""
        instructions = (
            "以管理员身份运行程序的步骤：\n\n"
            "1. 完全关闭当前程序\n"
            "2. 找到程序图标或快捷方式\n"
            "3. 右键点击程序图标\n"
            "4. 选择\"以管理员身份运行\"\n"
            "5. 在弹出的用户账户控制对话框中点击\"是\"\n"
            "6. 重新进行激活操作\n\n"
            "注意：管理员权限只是为了保存激活信息，\n"
            "正常使用时不需要管理员权限。"
        )
        
        self._show_message_box("information", "运行说明", instructions)
    
    def open_zhijian_website(self):
        """打开智剪大师官网"""
        try:
            url = QUrl("https://videosage.lanstar.top/index.html")
            QDesktopServices.openUrl(url)
        except Exception as e:
            self._show_message_box(
                "warning", "提示", 
                f"无法打开网页链接，请手动访问：\nhttps://videosage.lanstar.top/index.html\n\n错误信息：{str(e)}"
            )
