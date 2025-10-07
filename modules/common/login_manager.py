#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登录管理器模块 - 基于服务器API的登录认证
"""

import os
import json
import uuid
import platform
import configparser
import requests
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from datetime import datetime, timedelta


class LoginManager:
    """登录管理器 - 处理用户登录和会话管理"""
    
    # API 基础地址 - 使用 HTTPS
    API_BASE_URL = "https://jjds.lanstar.top/api/v1"
    
    def __init__(self):
        # 优先使用用户目录，避免权限问题
        self.config_file = self._get_config_file_path()
        self.device_id = self._get_or_create_device_id()
    
    def _get_config_file_path(self) -> Path:
        """获取配置文件路径，优先使用用户目录"""
        try:
            # 方案1：使用用户AppData目录 (推荐)
            if os.name == 'nt':  # Windows
                appdata = os.environ.get('APPDATA')
                if appdata:
                    config_dir = Path(appdata) / "VideoProcessingTools"
                    config_dir.mkdir(exist_ok=True)
                    return config_dir / ".login_config"
            else:  # Linux/Mac
                home = Path.home()
                config_dir = home / ".VideoProcessingTools"
                config_dir.mkdir(exist_ok=True)
                return config_dir / ".login_config"
        except Exception:
            pass
        
        try:
            # 方案2：使用用户Documents目录
            documents = Path.home() / "Documents"
            if documents.exists():
                config_dir = documents / "VideoProcessingTools"
                config_dir.mkdir(exist_ok=True)
                return config_dir / ".login_config"
        except Exception:
            pass
        
        try:
            # 方案3：使用临时目录
            import tempfile
            temp_dir = Path(tempfile.gettempdir()) / "VideoProcessingTools"
            temp_dir.mkdir(exist_ok=True)
            return temp_dir / ".login_config"
        except Exception:
            pass
        
        # 方案4：最后尝试程序目录（可能有权限问题）
        return Path(__file__).parent.parent.parent / ".login_config"
    
    def _get_or_create_device_id(self) -> str:
        """获取或创建设备ID - 必须包含 'tool' 字样"""
        # 尝试从配置文件读取现有的 device_id
        try:
            if self.config_file.exists():
                config = configparser.ConfigParser()
                config.read(self.config_file, encoding='utf-8')
                
                if 'DEVICE' in config and 'device_id' in config['DEVICE']:
                    device_id = config['DEVICE']['device_id']
                    # 验证 device_id 是否包含 "tool"
                    if 'tool' in device_id.lower():
                        return device_id
        except Exception:
            pass
        
        # 生成新的 device_id
        system = platform.system().lower()
        machine_name = platform.node()
        unique_id = str(uuid.uuid4())
        
        # 格式：tool-{系统}-{机器名}-{UUID}
        device_id = f"tool-{system}-{machine_name}-{unique_id}"
        
        # 保存 device_id
        self._save_device_id(device_id)
        
        return device_id
    
    def _save_device_id(self, device_id: str) -> bool:
        """保存设备ID到配置文件"""
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            config = configparser.ConfigParser()
            
            # 如果文件已存在，先读取
            if self.config_file.exists():
                config.read(self.config_file, encoding='utf-8')
            
            # 更新或创建 DEVICE 节
            if 'DEVICE' not in config:
                config['DEVICE'] = {}
            
            config['DEVICE']['device_id'] = device_id
            config['DEVICE']['created_at'] = datetime.now().isoformat()
            
            # 写入文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                config.write(f)
            
            # 设置文件属性（Windows隐藏文件）
            self._set_file_attributes()
            
            return True
            
        except Exception as e:
            print(f"保存设备ID失败: {e}")
            return False
    
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
    
    def login(self, phone: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        登录到服务器
        
        Args:
            phone: 手机号
            password: 密码
        
        Returns:
            (成功状态, 消息, 用户数据字典)
        """
        try:
            # 清理手机号（只保留数字）
            phone_clean = ''.join(c for c in phone if c.isdigit())
            
            # 验证手机号格式
            if len(phone_clean) != 11:
                return False, "手机号格式不正确，请输入11位手机号", None
            
            # 验证密码
            if not password or len(password) < 6:
                return False, "密码长度不能少于6位", None
            
            # 准备登录数据
            login_data = {
                "phone": phone_clean,
                "password": password,
                "client_version": "ToolKit-v2.0.0",
                "system_info": f"{platform.system()} {platform.release()}",
                "device_id": self.device_id
            }
            
            # 发送登录请求
            url = f"{self.API_BASE_URL}/auth/login"
            response = requests.post(
                url, 
                json=login_data,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            # 解析响应
            result = response.json()
            
            # 检查响应状态
            if response.status_code == 200 and result.get('code') == 200:
                # 登录成功
                data = result.get('data', {})
                
                # 保存登录信息
                if self._save_login_info(phone_clean, data):
                    return True, "登录成功", data
                else:
                    return False, "登录成功但保存登录信息失败，下次启动需要重新登录", data
            else:
                # 登录失败，返回服务器消息
                message = result.get('message', '登录失败，请检查账号密码')
                return False, message, None
                
        except requests.exceptions.Timeout:
            return False, "连接服务器超时，请检查网络连接", None
        except requests.exceptions.ConnectionError:
            return False, "无法连接到服务器，请检查网络连接", None
        except requests.exceptions.RequestException as e:
            return False, f"网络请求失败: {str(e)}", None
        except Exception as e:
            return False, f"登录失败: {str(e)}", None
    
    def _save_login_info(self, phone: str, data: Dict[str, Any]) -> bool:
        """保存登录信息到本地"""
        try:
            # 确保目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Windows下如果文件是隐藏的，先取消隐藏属性
            if os.name == 'nt' and self.config_file.exists():
                try:
                    import ctypes
                    # FILE_ATTRIBUTE_NORMAL = 128
                    ctypes.windll.kernel32.SetFileAttributesW(str(self.config_file), 128)
                except:
                    pass
            
            config = configparser.ConfigParser()
            
            # 如果文件已存在，先读取
            if self.config_file.exists():
                config.read(self.config_file, encoding='utf-8')
            
            # 更新或创建 LOGIN 节
            if 'LOGIN' not in config:
                config['LOGIN'] = {}
            
            config['LOGIN']['phone'] = phone
            config['LOGIN']['logged_in'] = 'True'
            config['LOGIN']['login_time'] = datetime.now().isoformat()
            config['LOGIN']['token'] = data.get('token', '')
            config['LOGIN']['refresh_token'] = data.get('refresh_token', '')
            config['LOGIN']['expires_in'] = str(data.get('expires_in', 3600))
            
            # 保存用户信息
            user_info = data.get('user_info', {})
            config['LOGIN']['user_id'] = str(user_info.get('id', ''))
            config['LOGIN']['nickname'] = user_info.get('nickname', '')
            config['LOGIN']['role'] = user_info.get('role', '')
            
            # 写入文件
            with open(self.config_file, 'w', encoding='utf-8') as f:
                config.write(f)
            
            # 设置文件属性（Windows隐藏文件）
            self._set_file_attributes()
            
            return True
            
        except Exception as e:
            print(f"保存登录信息失败: {e}")
            return False
    
    def check_login_status(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        检查登录状态
        
        Returns:
            (是否已登录, 手机号, 用户数据字典)
        """
        # 检查多个可能的配置文件位置
        config_paths = self._get_all_config_paths()
        
        # 检查每个位置
        for config_path in config_paths:
            try:
                if config_path.exists():
                    config = configparser.ConfigParser()
                    config.read(config_path, encoding='utf-8')
                    
                    if 'LOGIN' in config:
                        logged_in = config['LOGIN'].get('logged_in', 'False')
                        phone = config['LOGIN'].get('phone', '')
                        token = config['LOGIN'].get('token', '')
                        
                        if logged_in == 'True' and phone and token:
                            # 检查 token 是否过期
                            login_time_str = config['LOGIN'].get('login_time', '')
                            expires_in = int(config['LOGIN'].get('expires_in', 3600))
                            
                            if login_time_str:
                                try:
                                    login_time = datetime.fromisoformat(login_time_str)
                                    expire_time = login_time + timedelta(seconds=expires_in)
                                    
                                    # 如果 token 已过期，清除登录状态
                                    if datetime.now() >= expire_time:
                                        # Token 已过期，尝试刷新
                                        refresh_token = config['LOGIN'].get('refresh_token', '')
                                        if refresh_token:
                                            # 这里可以实现 token 刷新逻辑
                                            # 暂时先返回未登录状态
                                            return False, "", None
                                        else:
                                            return False, "", None
                                except Exception:
                                    pass
                            
                            # 构建用户数据
                            user_data = {
                                'token': token,
                                'refresh_token': config['LOGIN'].get('refresh_token', ''),
                                'expires_in': expires_in,
                                'user_info': {
                                    'id': int(config['LOGIN'].get('user_id', 0)),
                                    'phone': phone,
                                    'nickname': config['LOGIN'].get('nickname', ''),
                                    'role': config['LOGIN'].get('role', '')
                                }
                            }
                            
                            # 更新主配置文件路径为找到的有效路径
                            self.config_file = config_path
                            return True, phone, user_data
            
            except Exception:
                continue
        
        return False, "", None
    
    def _get_all_config_paths(self) -> list:
        """获取所有可能的配置文件路径"""
        config_paths = [
            self.config_file,  # 主配置文件路径
        ]
        
        # 添加备用路径
        try:
            # Windows AppData路径
            if os.name == 'nt':
                appdata = os.environ.get('APPDATA')
                if appdata:
                    config_paths.append(Path(appdata) / "VideoProcessingTools" / ".login_config")
            
            # Documents路径
            documents = Path.home() / "Documents" / "VideoProcessingTools" / ".login_config"
            config_paths.append(documents)
            
            # 临时目录路径
            import tempfile
            temp_config = Path(tempfile.gettempdir()) / "VideoProcessingTools" / ".login_config"
            config_paths.append(temp_config)
            
            # 程序目录路径（兼容旧版本）
            program_config = Path(__file__).parent.parent.parent / ".login_config"
            config_paths.append(program_config)
            
        except Exception:
            pass
        
        return config_paths
    
    def logout(self) -> bool:
        """退出登录"""
        try:
            if self.config_file.exists():
                config = configparser.ConfigParser()
                config.read(self.config_file, encoding='utf-8')
                
                if 'LOGIN' in config:
                    config['LOGIN']['logged_in'] = 'False'
                    config['LOGIN']['token'] = ''
                    config['LOGIN']['refresh_token'] = ''
                    
                    with open(self.config_file, 'w', encoding='utf-8') as f:
                        config.write(f)
                    
                    return True
        except Exception as e:
            print(f"退出登录失败: {e}")
            return False
        
        return False
    
    def get_device_id(self) -> str:
        """获取设备ID"""
        return self.device_id
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """验证手机号格式"""
        phone_clean = ''.join(c for c in phone if c.isdigit())
        if len(phone_clean) != 11:
            return False
        if not phone_clean.startswith(('13', '14', '15', '16', '17', '18', '19')):
            return False
        return True

