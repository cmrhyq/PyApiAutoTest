"""
@File read_config_ini.py
@Contact cmrhyq@163.com
@License (C)Copyright 2022-2025, AlanHuang
@Modify Time 2024/6/21 9:43
@Author Alan Huang
@Version 0.0.1
@Description None
"""
import configparser
from core.config.manager_config import ManagerConfig


class ReadConfigIni(object):
    """
    配置文件
    """
    def __init__(self):
        self.manager_config = ManagerConfig()
        self.config = configparser.RawConfigParser()  # 当有%的符号时请使用Raw读取
        self.config.read(self.manager_config.system_ini_file, encoding='utf-8')

    def _get(self, section, option):
        """获取"""
        return self.config.get(section, option)

    def _set(self, section, option, value):
        """更新"""
        self.config.set(section, option, value)
        with open(self.manager_config.system_ini_file, 'w') as f:
            self.config.write(f)

    @property
    def interface_url(self):
        return self._get("interface", 'url')

    @property
    def interface_username(self):
        return self._get("interface", 'username')

    @property
    def interface_password(self):
        return self._get("interface", 'password')

    @property
    def mail_host(self):
        return self._get("mail", 'host')

    @property
    def mail_port(self):
        return self._get("mail", 'port')

    @property
    def mail_sender(self):
        return self._get("mail", 'sender')

    @property
    def mail_license(self):
        return self._get("mail", 'license')