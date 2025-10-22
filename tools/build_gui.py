#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包工具 - GUI版本
"""

import os
import sys
import subprocess
import shutil
import re
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QGroupBox, QGridLayout, QTextEdit, QMessageBox,
                            QProgressBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QIcon


class BuildThread(QThread):
    """打包线程"""
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(bool)
    
    def __init__(self, project_root, tools_dir):
        super().__init__()
        self.project_root = project_root
        self.tools_dir = tools_dir
        
    def run(self):
        """执行打包流程"""
        try:
            # 步骤1: PyInstaller打包
            self.log_signal.emit("=" * 60)
            self.log_signal.emit("步骤 1/3: 使用PyInstaller打包...")
            self.log_signal.emit("=" * 60)
            self.progress_signal.emit(10)
            
            if not self.build_exe():
                self.finished_signal.emit(False)
                return
            
            self.progress_signal.emit(40)
            
            # 步骤2: Inno Setup制作安装包
            self.log_signal.emit("\n" + "=" * 60)
            self.log_signal.emit("步骤 2/3: 使用Inno Setup制作安装包...")
            self.log_signal.emit("=" * 60)
            
            if not self.build_installer():
                self.finished_signal.emit(False)
                return
            
            self.progress_signal.emit(80)
            
            # 步骤3: 清理临时文件
            self.log_signal.emit("\n" + "=" * 60)
            self.log_signal.emit("步骤 3/3: 清理临时文件...")
            self.log_signal.emit("=" * 60)
            
            if not self.cleanup():
                self.log_signal.emit("警告: 清理临时文件时出现问题")
            
            self.progress_signal.emit(100)
            
            # 显示最终结果
            self.log_signal.emit("\n" + "=" * 60)
            self.log_signal.emit("打包完成！")
            self.log_signal.emit("=" * 60)
            
            installer_dir = self.project_root / 'installer'
            if installer_dir.exists():
                installer_files = list(installer_dir.glob('*.exe'))
                if installer_files:
                    installer_file = installer_files[0]
                    size_mb = installer_file.stat().st_size / 1024 / 1024
                    self.log_signal.emit(f"\n安装包位置: {installer_file}")
                    self.log_signal.emit(f"文件大小: {size_mb:.1f} MB")
            
            self.finished_signal.emit(True)
            
        except Exception as e:
            self.log_signal.emit(f"\n错误: {str(e)}")
            self.finished_signal.emit(False)
    
    def build_exe(self):
        """PyInstaller打包"""
        os.chdir(self.project_root)
        
        # 清理之前的构建
        self.log_signal.emit("清理之前的构建文件...")
        build_dirs = ['build', 'dist']
        for build_dir in build_dirs:
            if Path(build_dir).exists():
                shutil.rmtree(build_dir)
                self.log_signal.emit(f"  删除 {build_dir}/")
        
        # 执行PyInstaller打包
        self.log_signal.emit("执行PyInstaller打包...")
        spec_file = self.tools_dir / 'app.spec'
        
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            str(spec_file)
        ]
        
        try:
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
            
            self.log_signal.emit("PyInstaller打包完成！")
            
            # 检查输出文件
            dist_dir = self.project_root / 'dist' / 'audio_subtitle_tools'
            if dist_dir.exists():
                exe_file = dist_dir / 'audio_subtitle_tools.exe'
                if exe_file.exists():
                    size_mb = exe_file.stat().st_size / 1024 / 1024
                    self.log_signal.emit(f"可执行文件位置: {exe_file}")
                    self.log_signal.emit(f"文件大小: {size_mb:.1f} MB")
                    return True
                else:
                    self.log_signal.emit("错误: 未找到可执行文件")
                    return False
            else:
                self.log_signal.emit("错误: 未找到输出目录")
                return False
                
        except subprocess.CalledProcessError as e:
            self.log_signal.emit(f"PyInstaller打包失败: {e}")
            return False
        except Exception as e:
            self.log_signal.emit(f"打包过程出错: {e}")
            return False
    
    def build_installer(self):
        """Inno Setup制作安装包"""
        # 检查dist目录是否存在
        dist_dir = self.project_root / 'dist' / 'audio_subtitle_tools'
        if not dist_dir.exists():
            self.log_signal.emit("错误: 未找到PyInstaller输出目录")
            return False
        
        # 查找Inno Setup
        possible_paths = [
            r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
            r"C:\Program Files\Inno Setup 6\ISCC.exe", 
            r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
            r"C:\Program Files\Inno Setup 5\ISCC.exe",
        ]
        
        iscc_path = None
        for path in possible_paths:
            if Path(path).exists():
                iscc_path = path
                break
        
        if not iscc_path:
            self.log_signal.emit("错误: 未找到Inno Setup编译器")
            self.log_signal.emit("请从以下地址下载并安装Inno Setup:")
            self.log_signal.emit("https://jrsoftware.org/isinfo.php")
            return False
        
        self.log_signal.emit(f"找到Inno Setup编译器: {iscc_path}")
        
        # 创建installer目录
        installer_dir = self.project_root / 'installer'
        installer_dir.mkdir(exist_ok=True)
        
        # Inno Setup脚本路径
        iss_file = self.tools_dir / 'setup.iss'
        
        # 执行Inno Setup编译
        self.log_signal.emit("执行Inno Setup编译...")
        
        try:
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
            
            self.log_signal.emit("Inno Setup编译完成！")
            
            # 检查输出文件
            setup_files = list(installer_dir.glob('*.exe'))
            if setup_files:
                setup_file = setup_files[0]
                size_mb = setup_file.stat().st_size / 1024 / 1024
                self.log_signal.emit(f"安装包位置: {setup_file}")
                self.log_signal.emit(f"文件大小: {size_mb:.1f} MB")
                return True
            else:
                self.log_signal.emit("错误: 未找到生成的安装包")
                return False
                
        except subprocess.CalledProcessError as e:
            self.log_signal.emit(f"Inno Setup编译失败: {e}")
            return False
        except Exception as e:
            self.log_signal.emit(f"编译过程出错: {e}")
            return False
    
    def cleanup(self):
        """清理临时文件"""
        os.chdir(self.project_root)
        
        # 清理目录列表
        cleanup_dirs = ['build', 'dist']
        
        for dir_name in cleanup_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                try:
                    shutil.rmtree(dir_path)
                    self.log_signal.emit(f"删除目录: {dir_name}/")
                except Exception as e:
                    self.log_signal.emit(f"删除 {dir_name}/ 失败: {e}")
        
        # 清理spec产生的临时文件
        spec_cache = self.project_root / '__pycache__'
        if spec_cache.exists():
            try:
                shutil.rmtree(spec_cache)
                self.log_signal.emit("删除缓存: __pycache__/")
            except Exception as e:
                self.log_signal.emit(f"删除__pycache__/失败: {e}")
        
        self.log_signal.emit("清理完成！")
        return True


class BuildToolGUI(QMainWindow):
    """打包工具GUI主窗口"""
    
    def __init__(self):
        super().__init__()
        self.project_root = Path(__file__).parent.parent
        self.tools_dir = Path(__file__).parent
        self.version_info_file = self.tools_dir / 'version_info.txt'
        self.setup_iss_file = self.tools_dir / 'setup.iss'
        
        self.init_ui()
        self.load_config()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("视频处理工具集 - 打包工具")
        self.setMinimumSize(800, 700)
        
        # 设置图标
        icon_path = self.project_root / 'resources' / 'images' / 'logo.ico'
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 版本信息组
        version_group = self.create_version_group()
        main_layout.addWidget(version_group)
        
        # 应用信息组
        app_info_group = self.create_app_info_group()
        main_layout.addWidget(app_info_group)
        
        # 操作按钮
        button_layout = self.create_button_layout()
        main_layout.addLayout(button_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        main_layout.addWidget(self.progress_bar)
        
        # 日志输出
        log_label = QLabel("打包日志:")
        main_layout.addWidget(log_label)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(200)
        main_layout.addWidget(self.log_text)
        
        # 应用样式
        self.apply_style()
        
    def create_version_group(self):
        """创建版本信息组"""
        group = QGroupBox("📋 版本信息")
        layout = QGridLayout()
        layout.setSpacing(10)
        
        # 主版本号
        layout.addWidget(QLabel("主版本号:"), 0, 0)
        self.major_version = QLineEdit()
        self.major_version.setPlaceholderText("如: 2")
        layout.addWidget(self.major_version, 0, 1)
        
        # 次版本号
        layout.addWidget(QLabel("次版本号:"), 0, 2)
        self.minor_version = QLineEdit()
        self.minor_version.setPlaceholderText("如: 1")
        layout.addWidget(self.minor_version, 0, 3)
        
        # 修订号
        layout.addWidget(QLabel("修订号:"), 1, 0)
        self.patch_version = QLineEdit()
        self.patch_version.setPlaceholderText("如: 0")
        layout.addWidget(self.patch_version, 1, 1)
        
        # 构建标识
        layout.addWidget(QLabel("构建标识:"), 1, 2)
        self.build_label = QLineEdit()
        self.build_label.setPlaceholderText("如: beta-02")
        layout.addWidget(self.build_label, 1, 3)
        
        group.setLayout(layout)
        return group
        
    def create_app_info_group(self):
        """创建应用信息组"""
        group = QGroupBox("💼 应用信息")
        layout = QGridLayout()
        layout.setSpacing(10)
        
        # 应用名称
        layout.addWidget(QLabel("应用名称:"), 0, 0)
        self.app_name = QLineEdit()
        self.app_name.setPlaceholderText("如: 智剪大师")
        layout.addWidget(self.app_name, 0, 1)
        
        # 英文名称
        layout.addWidget(QLabel("英文名称:"), 0, 2)
        self.app_name_en = QLineEdit()
        self.app_name_en.setPlaceholderText("如: VideoSage")
        layout.addWidget(self.app_name_en, 0, 3)
        
        # 公司名称
        layout.addWidget(QLabel("公司名称:"), 1, 0)
        self.company_name = QLineEdit()
        self.company_name.setPlaceholderText("如: 岚舞科技")
        layout.addWidget(self.company_name, 1, 1)
        
        # 域名
        layout.addWidget(QLabel("域名:"), 1, 2)
        self.domain = QLineEdit()
        self.domain.setPlaceholderText("如: lanstar.top")
        layout.addWidget(self.domain, 1, 3)
        
        # 描述
        layout.addWidget(QLabel("描述:"), 2, 0)
        self.description = QLineEdit()
        self.description.setPlaceholderText("如: 视频搜索重塑神器")
        layout.addWidget(self.description, 2, 1, 1, 3)
        
        group.setLayout(layout)
        return group
        
    def create_button_layout(self):
        """创建按钮布局"""
        layout = QHBoxLayout()
        layout.setSpacing(15)
        
        # 刷新版本信息按钮
        self.refresh_btn = QPushButton("🔄 刷新版本信息")
        self.refresh_btn.clicked.connect(self.load_config)
        self.refresh_btn.setMinimumHeight(40)
        layout.addWidget(self.refresh_btn)
        
        # 更新版本配置按钮
        self.update_btn = QPushButton("📝 更新版本配置")
        self.update_btn.clicked.connect(self.update_config)
        self.update_btn.setMinimumHeight(40)
        layout.addWidget(self.update_btn)
        
        # 开始打包按钮
        self.build_btn = QPushButton("🚀 开始打包")
        self.build_btn.clicked.connect(self.start_build)
        self.build_btn.setMinimumHeight(40)
        layout.addWidget(self.build_btn)
        
        return layout
        
    def apply_style(self):
        """应用样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: "Microsoft YaHei UI", "Segoe UI", sans-serif;
                font-size: 10pt;
            }
            QGroupBox {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 10px;
                font-weight: bold;
                font-size: 11pt;
            }
            QGroupBox::title {
                color: #4a9eff;
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 5px 10px;
                background-color: #2d2d2d;
            }
            QLabel {
                background-color: transparent;
                color: #cccccc;
                font-size: 10pt;
            }
            QLineEdit {
                background-color: #3d3d3d;
                border: 2px solid #4d4d4d;
                border-radius: 5px;
                padding: 8px;
                color: #ffffff;
                selection-background-color: #4a9eff;
                font-size: 10pt;
            }
            QLineEdit:focus {
                border: 2px solid #4a9eff;
            }
            QPushButton {
                background-color: #0d7377;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #14a085;
            }
            QPushButton:pressed {
                background-color: #0a5d5f;
            }
            QPushButton:disabled {
                background-color: #3d3d3d;
                color: #666666;
            }
            QTextEdit {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                padding: 8px;
                color: #ffffff;
                font-family: "Consolas", "Courier New", monospace;
                font-size: 9pt;
            }
            QProgressBar {
                background-color: #2d2d2d;
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                text-align: center;
                color: #ffffff;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4a9eff;
                border-radius: 3px;
            }
        """)
        
    def load_config(self):
        """加载配置"""
        try:
            # 读取version_info.txt
            if self.version_info_file.exists():
                content = self.version_info_file.read_text(encoding='utf-8')
                
                # 解析版本号
                filevers_match = re.search(r'filevers=\((\d+),(\d+),(\d+),(\d+)\)', content)
                if filevers_match:
                    self.major_version.setText(filevers_match.group(1))
                    self.minor_version.setText(filevers_match.group(2))
                    self.patch_version.setText(filevers_match.group(3))
                
                # 解析应用信息
                company_match = re.search(r"StringStruct\(u'CompanyName', u'(.+?)'\)", content)
                if company_match:
                    self.company_name.setText(company_match.group(1))
                
                desc_match = re.search(r"StringStruct\(u'FileDescription', u'(.+?)'\)", content)
                if desc_match:
                    self.description.setText(desc_match.group(1))
                
                product_match = re.search(r"StringStruct\(u'ProductName', u'(.+?)'\)", content)
                if product_match:
                    self.app_name.setText(product_match.group(1))
            
            # 读取setup.iss
            if self.setup_iss_file.exists():
                content = self.setup_iss_file.read_text(encoding='utf-8')
                
                # 解析英文名称和域名（从AppName中提取）
                app_name_match = re.search(r'AppName=(.+)', content)
                if app_name_match:
                    self.app_name_en.setText(app_name_match.group(1).strip())
                
                # 解析域名
                url_match = re.search(r'AppPublisherURL=(.+)', content)
                if url_match and url_match.group(1).strip():
                    self.domain.setText(url_match.group(1).strip())
                
                # 解析构建标识（从版本号中提取）
                version_match = re.search(r'AppVersion=(\d+\.\d+\.\d+)', content)
                if version_match:
                    # 检查是否有构建标识
                    output_match = re.search(r'OutputBaseFilename=.*?_v\d+\.\d+\.\d+(?:-(.+?))?_', content)
                    if output_match and output_match.group(1):
                        self.build_label.setText(output_match.group(1))
            
            self.append_log("配置加载成功")
            
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载配置失败: {str(e)}")
            self.append_log(f"加载配置失败: {str(e)}")
    
    def update_config(self, show_message=True):
        """更新配置文件"""
        try:
            # 获取输入值
            major = self.major_version.text() or "2"
            minor = self.minor_version.text() or "0"
            patch = self.patch_version.text() or "0"
            build = self.build_label.text() or ""
            
            app_name = self.app_name.text() or "视频处理工具集"
            app_name_en = self.app_name_en.text() or "Video Tools"
            company = self.company_name.text() or "Development Team"
            domain = self.domain.text() or ""
            desc = self.description.text() or "视频处理工具集 - 音频提取和字幕重命名"
            
            version_str = f"{major}.{minor}.{patch}"
            if build:
                version_display = f"{version_str}-{build}"
            else:
                version_display = version_str
            
            # 更新version_info.txt
            self.update_version_info(major, minor, patch, company, desc, app_name, version_display)
            
            # 更新setup.iss
            self.update_setup_iss(major, minor, patch, build, app_name_en, company, domain)
            
            if show_message:
                QMessageBox.information(self, "成功", "版本配置已更新！")
            self.append_log("版本配置更新成功")
            return True
            
        except Exception as e:
            if show_message:
                QMessageBox.critical(self, "错误", f"更新配置失败: {str(e)}")
            self.append_log(f"更新配置失败: {str(e)}")
            return False
    
    def update_version_info(self, major, minor, patch, company, desc, product, version_display):
        """更新version_info.txt"""
        content = f"""# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=({major},{minor},{patch},0),
    prodvers=({major},{minor},{patch},0),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x4,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'080404B0',
        [StringStruct(u'CompanyName', u'{company}'),
        StringStruct(u'FileDescription', u'{desc}'),
        StringStruct(u'FileVersion', u'{version_display}'),
        StringStruct(u'InternalName', u'{product}'),
        StringStruct(u'LegalCopyright', u'Copyright © 2025 {company}'),
        StringStruct(u'OriginalFilename', u'{product}.exe'),
        StringStruct(u'ProductName', u'{product}'),
        StringStruct(u'ProductVersion', u'{version_display}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [2052, 1200])])
  ]
)
"""
        self.version_info_file.write_text(content, encoding='utf-8')
    
    def update_setup_iss(self, major, minor, patch, build, app_name_en, company, domain):
        """更新setup.iss"""
        version_str = f"{major}.{minor}.{patch}"
        if build:
            output_filename = f"视频处理工具集_v{version_str}-{build}_安装包"
        else:
            output_filename = f"视频处理工具集_v{version_str}_安装包"
        
        publisher_url = f"https://{domain}" if domain else ""
        
        content = f"""[Setup]
AppName={app_name_en}
AppVersion={version_str}
AppPublisher={company}
AppPublisherURL={publisher_url}
AppSupportURL={publisher_url}
AppUpdatesURL={publisher_url}
AppId={{{{A5B3C2D1-E4F5-6789-ABCD-EF0123456789}}
DefaultDirName={{autopf}}\\audio_subtitle_tools
DefaultGroupName=音频字幕工具
AllowNoIcons=yes
LicenseFile=
InfoAfterFile=
OutputDir=..\\installer
OutputBaseFilename={output_filename}
SetupIconFile=..\\resources\\images\\logo.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
DisableReadyPage=yes
ShowLanguageDialog=no
LanguageDetectionMethod=uilanguage
UninstallDisplayIcon={{app}}\\audio_subtitle_tools.exe
; 版本控制设置
VersionInfoVersion={version_str}
; 卸载旧版本设置
UninstallRestartComputer=no
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "chinesesimp"; MessagesFile: "ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{{cm:CreateQuickLaunchIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
Source: "..\\dist\\audio_subtitle_tools\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{{group}}\\音频字幕工具"; Filename: "{{app}}\\audio_subtitle_tools.exe"
Name: "{{group}}\\{{cm:UninstallProgram,音频字幕工具}}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\音频字幕工具"; Filename: "{{app}}\\audio_subtitle_tools.exe"; Tasks: desktopicon
Name: "{{userappdata}}\\Microsoft\\Internet Explorer\\Quick Launch\\音频字幕工具"; Filename: "{{app}}\\audio_subtitle_tools.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{{app}}\\audio_subtitle_tools.exe"; Description: "{{cm:LaunchProgram,{app_name_en}}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{{app}}"

[Code]
// 检测并卸载旧版本
function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{{#SetupSetting("AppId")}}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

function UnInstallOldVersion(): Integer;
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  Result := 0;
  sUnInstallString := GetUninstallString();
  if sUnInstallString <> '' then begin
    sUnInstallString := RemoveQuotes(sUnInstallString);
    if Exec(sUnInstallString, '/SILENT /NORESTART /SUPPRESSMSGBOXES','', SW_HIDE, ewWaitUntilTerminated, iResultCode) then
      Result := 3
    else
      Result := 2;
  end else
    Result := 1;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep=ssInstall) then
  begin
    if (IsUpgrade()) then
    begin
      UnInstallOldVersion();
    end;
  end;
end;

function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
  OldVersion: String;
begin
  Result := True;
  
  // 检测是否已安装旧版本
  if IsUpgrade() then
  begin
    if MsgBox('检测到系统中已安装旧版本的程序。' #13#13 '安装程序将自动卸载旧版本后继续安装新版本。' #13#13 '是否继续？', mbConfirmation, MB_YESNO) = IDYES then
    begin
      Result := True;
    end
    else
    begin
      Result := False;
    end;
  end;
end;
"""
        self.setup_iss_file.write_text(content, encoding='utf-8')
    
    def start_build(self):
        """开始打包"""
        # 清空日志
        self.log_text.clear()
        self.progress_bar.setValue(0)
        
        # 获取版本信息用于日志显示
        major = self.major_version.text() or "2"
        minor = self.minor_version.text() or "0"
        patch = self.patch_version.text() or "0"
        build = self.build_label.text() or ""
        version_str = f"{major}.{minor}.{patch}"
        if build:
            version_display = f"{version_str}-{build}"
        else:
            version_display = version_str
        
        # 显示打包信息
        self.append_log("=" * 60)
        self.append_log("开始打包流程")
        self.append_log("=" * 60)
        self.append_log(f"版本号: {version_display}")
        self.append_log(f"应用名称: {self.app_name.text() or '视频处理工具集'}")
        self.append_log(f"公司名称: {self.company_name.text() or 'Development Team'}")
        self.append_log("=" * 60)
        self.append_log("")
        
        # 先更新配置（不显示消息框）
        if not self.update_config(show_message=False):
            QMessageBox.critical(self, "错误", "更新配置失败，无法开始打包")
            return
        
        # 禁用按钮
        self.build_btn.setEnabled(False)
        self.update_btn.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        
        # 创建并启动打包线程
        self.build_thread = BuildThread(self.project_root, self.tools_dir)
        self.build_thread.log_signal.connect(self.append_log)
        self.build_thread.progress_signal.connect(self.update_progress)
        self.build_thread.finished_signal.connect(self.build_finished)
        self.build_thread.start()
    
    def append_log(self, text):
        """追加日志"""
        self.log_text.append(text)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
    
    def update_progress(self, value):
        """更新进度"""
        self.progress_bar.setValue(value)
    
    def build_finished(self, success):
        """打包完成"""
        # 启用按钮
        self.build_btn.setEnabled(True)
        self.update_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "成功", "打包完成！")
        else:
            QMessageBox.critical(self, "失败", "打包失败，请查看日志")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = BuildToolGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

