#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登录对话框组件
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QMessageBox,
                             QDialogButtonBox, QCheckBox)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QIcon, QDesktopServices

from pathlib import Path
from config.app_config import get_images_path
from modules.common.login_manager import LoginManager


class LoginDialog(QDialog):
    """登录对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.login_manager = LoginManager()
        self.user_data = None  # 保存登录成功后的用户数据
        self.init_ui()
    
    def _get_icon(self):
        """获取应用图标"""
        icon_path = get_images_path() / "logo.ico"
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
        self.setWindowTitle("用户登录")
        self.setFixedSize(500, 690)
        self.setModal(True)
        
        # 设置窗口图标
        icon_path = get_images_path() / "logo.ico"
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
            
            QCheckBox {
                color: #1a1a1a;
                font-size: 13px;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #d0d7de;
                border-radius: 4px;
                background-color: #ffffff;
            }
            
            QCheckBox::indicator:checked {
                background-color: #007AFF;
                border-color: #007AFF;
                image: url(none);
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
        subtitle_label = QLabel("请登录您的账号以使用软件")
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
        
        # 密码输入
        password_label = QLabel("密码：")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入您的密码...")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.textChanged.connect(self.on_input_changed)
        self.password_input.returnPressed.connect(self.login_user)  # 回车登录
        input_layout.addWidget(password_label)
        input_layout.addWidget(self.password_input)
        
        # 记住密码选项（可选功能，暂时隐藏）
        # self.remember_cb = QCheckBox("记住密码")
        # input_layout.addWidget(self.remember_cb)
        
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
        info_label = QLabel("💡 请使用您在官网注册的账号登录")
        info_label.setStyleSheet("color: #666; font-size: 12px; margin: 10px 0;")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 按钮区域
        button_box = QDialogButtonBox()
        self.login_btn = QPushButton("登录")
        self.login_btn.clicked.connect(self.login_user)
        self.login_btn.setEnabled(False)
        
        self.exit_btn = QPushButton("退出")
        self.exit_btn.clicked.connect(self.reject)
        
        button_box.addButton(self.login_btn, QDialogButtonBox.ButtonRole.AcceptRole)
        button_box.addButton(self.exit_btn, QDialogButtonBox.ButtonRole.RejectRole)
        
        layout.addWidget(button_box)
        
        layout.addStretch()
    
    def on_input_changed(self):
        """输入内容变化时检查"""
        phone = self.phone_input.text().strip()
        password = self.password_input.text().strip()
        
        # 过滤手机号，只保留数字
        phone_digits = ''.join(c for c in phone if c.isdigit())
        if phone_digits != phone:
            self.phone_input.setText(phone_digits)
            return
        
        # 检查是否可以登录
        can_login = (
            len(phone_digits) == 11 and 
            phone_digits.startswith(('13', '14', '15', '16', '17', '18', '19')) and
            len(password) >= 6
        )
        
        self.login_btn.setEnabled(can_login)
    
    def login_user(self):
        """登录用户"""
        # 如果登录按钮被禁用，不执行登录
        if not self.login_btn.isEnabled():
            return
        
        phone = self.phone_input.text().strip()
        password = self.password_input.text().strip()
        
        # 禁用登录按钮，防止重复点击
        self.login_btn.setEnabled(False)
        self.login_btn.setText("登录中...")
        
        # 执行登录
        success, message, user_data = self.login_manager.login(phone, password)
        
        # 恢复登录按钮
        self.login_btn.setText("登录")
        self.on_input_changed()  # 重新检查是否可以启用
        
        if success:
            # 保存用户数据
            self.user_data = user_data
            
            # 显示成功消息
            user_info = user_data.get('user_info', {})
            nickname = user_info.get('nickname', phone)
            
            self._show_message_box(
                "information", "登录成功", 
                f"🎉 登录成功！\n\n"
                f"欢迎，{nickname}！\n\n"
                f"您现在可以开始使用软件了。"
            )
            self.accept()
        else:
            # 显示错误消息
            self._show_message_box("warning", "登录失败", f"❌ {message}")
    
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
    
    def get_user_data(self):
        """获取登录成功后的用户数据"""
        return self.user_data

