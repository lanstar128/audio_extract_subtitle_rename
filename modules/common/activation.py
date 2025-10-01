#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
激活管理器模块
"""

import os
import time
import hashlib
import configparser
from pathlib import Path
from typing import Tuple, Optional

from config.app_config import SECRET_KEY


class ActivationManager:
    """激活管理器"""
    
    def __init__(self):
        # 优先使用用户目录，避免权限问题
        self.config_file = self._get_config_file_path()
    
    def _get_config_file_path(self):
        """获取配置文件路径，优先使用用户目录"""
        try:
            # 方案1：使用用户AppData目录 (推荐)
            if os.name == 'nt':  # Windows
                appdata = os.environ.get('APPDATA')
                if appdata:
                    config_dir = Path(appdata) / "VideoProcessingTools"
                    config_dir.mkdir(exist_ok=True)
                    return config_dir / ".activation_config"
            else:  # Linux/Mac
                home = Path.home()
                config_dir = home / ".VideoProcessingTools"
                config_dir.mkdir(exist_ok=True)
                return config_dir / ".activation_config"
        except Exception:
            pass
        
        try:
            # 方案2：使用用户Documents目录
            import tempfile
            documents = Path.home() / "Documents"
            if documents.exists():
                config_dir = documents / "VideoProcessingTools"
                config_dir.mkdir(exist_ok=True)
                return config_dir / ".activation_config"
        except Exception:
            pass
        
        try:
            # 方案3：使用临时目录
            import tempfile
            temp_dir = Path(tempfile.gettempdir()) / "VideoProcessingTools"
            temp_dir.mkdir(exist_ok=True)
            return temp_dir / ".activation_config"
        except Exception:
            pass
        
        # 方案4：最后尝试程序目录（可能有权限问题）
        return Path(__file__).parent.parent.parent / ".activation_config"
    
    @staticmethod
    def generate_code_for_phone(phone_number: str) -> str:
        """根据手机号生成激活码"""
        # 组合手机号和密钥
        combined = phone_number + SECRET_KEY
        
        # 生成MD5哈希
        hash_object = hashlib.md5(combined.encode('utf-8'))
        hash_hex = hash_object.hexdigest()
        
        # 取前12位并转为大写
        code = hash_hex[:12].upper()
        
        # 格式化为 XXXX-XXXX-XXXX
        formatted_code = f"{code[:4]}-{code[4:8]}-{code[8:12]}"
        
        return formatted_code
    
    def verify_activation(self, phone_number: str, activation_code: str) -> Tuple[bool, str]:
        """验证激活码"""
        try:
            # 清理输入（移除空格和连字符）
            phone_clean = ''.join(c for c in phone_number if c.isdigit())
            code_clean = activation_code.replace('-', '').replace(' ', '').upper()
            
            # 验证手机号格式
            if len(phone_clean) != 11:
                return False, "手机号格式不正确"
            
            # 生成正确的激活码
            correct_code = self.generate_code_for_phone(phone_clean)
            correct_code_clean = correct_code.replace('-', '')
            
            # 验证激活码
            if code_clean == correct_code_clean:
                return True, "激活成功"
            else:
                return False, "激活码不正确"
                
        except Exception as e:
            return False, f"验证失败：{str(e)}"
    
    def save_activation_status(self, phone_number: str) -> bool:
        """保存激活状态到本地"""
        last_error = ""
        
        # 尝试多个位置保存配置文件
        for attempt in range(3):
            try:
                # 确保目录存在
                self.config_file.parent.mkdir(parents=True, exist_ok=True)
                
                # 检查目录写权限
                if not os.access(self.config_file.parent, os.W_OK):
                    raise PermissionError(f"没有写权限：{self.config_file.parent}")
                
                config = configparser.ConfigParser()
                config['ACTIVATION'] = {
                    'phone': phone_number,
                    'activated': 'True',
                    'activation_time': str(int(time.time())),
                    'version': '2.0'
                }
                
                # 先写入临时文件，然后重命名（原子操作）
                temp_file = self.config_file.with_suffix('.tmp')
                with open(temp_file, 'w', encoding='utf-8') as f:
                    config.write(f)
                
                # 重命名为最终文件
                temp_file.replace(self.config_file)
                
                # 设置文件属性（Windows隐藏文件）
                self._set_file_attributes()
                
                return True
                
            except PermissionError as e:
                last_error = f"权限错误: {str(e)}"
                if attempt < 2:
                    # 尝试其他位置
                    self.config_file = self._get_alternative_config_path(attempt + 1)
                    continue
                    
            except Exception as e:
                last_error = f"保存失败: {str(e)}"
                if attempt < 2:
                    # 尝试其他位置
                    self.config_file = self._get_alternative_config_path(attempt + 1)
                    continue
        
        # 所有尝试都失败了，记录详细错误
        self._log_save_error(last_error)
        return False
    
    def _get_alternative_config_path(self, attempt: int) -> Path:
        """获取备用配置文件路径"""
        try:
            if attempt == 1:
                # 尝试用户Documents目录
                documents = Path.home() / "Documents" / "VideoProcessingTools"
                documents.mkdir(exist_ok=True)
                return documents / ".activation_config"
            elif attempt == 2:
                # 尝试临时目录
                import tempfile
                temp_dir = Path(tempfile.gettempdir()) / "VideoProcessingTools"
                temp_dir.mkdir(exist_ok=True)
                return temp_dir / ".activation_config"
        except Exception:
            pass
        return self.config_file
    
    def _set_file_attributes(self):
        """设置文件属性（Windows下隐藏文件）"""
        try:
            if os.name == 'nt':
                import ctypes
                # FILE_ATTRIBUTE_HIDDEN = 2
                ctypes.windll.kernel32.SetFileAttributesW(str(self.config_file), 2)
        except Exception:
            # 设置隐藏属性失败不影响功能
            pass
    
    def _log_save_error(self, error_msg: str):
        """记录保存错误信息"""
        try:
            error_log = Path(__file__).parent.parent.parent / "activation_error.log"
            with open(error_log, 'a', encoding='utf-8') as f:
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] 激活状态保存失败: {error_msg}\n")
                f.write(f"[{timestamp}] 尝试路径: {self.config_file}\n")
                f.write(f"[{timestamp}] 用户: {os.environ.get('USERNAME', 'Unknown')}\n\n")
        except Exception:
            # 记录日志失败也不影响主流程
            pass
    
    def check_activation_status(self) -> Tuple[bool, str]:
        """检查激活状态"""
        # 检查多个可能的配置文件位置
        config_paths = [
            self.config_file,  # 主配置文件路径
        ]
        
        # 添加备用路径
        try:
            # Windows AppData路径
            if os.name == 'nt':
                appdata = os.environ.get('APPDATA')
                if appdata:
                    config_paths.append(Path(appdata) / "VideoProcessingTools" / ".activation_config")
            
            # Documents路径
            documents = Path.home() / "Documents" / "VideoProcessingTools" / ".activation_config"
            config_paths.append(documents)
            
            # 临时目录路径
            import tempfile
            temp_config = Path(tempfile.gettempdir()) / "VideoProcessingTools" / ".activation_config"
            config_paths.append(temp_config)
            
            # 程序目录路径（兼容旧版本）
            program_config = Path(__file__).parent.parent.parent / ".activation_config"
            config_paths.append(program_config)
            
        except Exception:
            pass
        
        # 检查每个位置
        for config_path in config_paths:
            try:
                if config_path.exists():
                    config = configparser.ConfigParser()
                    config.read(config_path, encoding='utf-8')
                    
                    if 'ACTIVATION' in config:
                        activated = config['ACTIVATION'].get('activated', 'False')
                        phone = config['ACTIVATION'].get('phone', '')
                        
                        if activated == 'True' and phone:
                            # 更新主配置文件路径为找到的有效路径
                            self.config_file = config_path
                            return True, phone
                
            except Exception:
                continue
        
        return False, ""
    
    @staticmethod
    def is_admin() -> bool:
        """检查是否以管理员身份运行"""
        try:
            if os.name == 'nt':  # Windows
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin()
            else:  # Linux/Mac
                return os.geteuid() == 0
        except Exception:
            return False

