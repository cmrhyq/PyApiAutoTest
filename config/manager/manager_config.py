"""
@File manager_config.py
@Contact cmrhyq@163.com
@License (C)Copyright 2022-2025, AlanHuang
@Modify Time 2024/6/21 9:34
@Author Alan Huang
@Version 0.0.1
@Description None
"""
import os

from utils.time.time_utils import dt_strftime


class ManagerConfig(object):
    # 项目目录
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    @property
    def log_file(self):
        """日志目录"""
        log_dir = os.path.join(self.BASE_DIR, 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        return os.path.join(log_dir, '{}.log'.format(dt_strftime()))

    @property
    def env_file(self):
        """测试文件"""
        env_file = os.path.join(self.BASE_DIR, 'config', 'env_config.yaml')
        if not os.path.exists(env_file):
            raise FileNotFoundError(f"配置文件{env_file}不存在")
        return env_file

    @property
    def test_file(self):
        """测试文件目录"""
        test_folder = os.path.join(self.BASE_DIR, 'data')
        if not os.path.exists(test_folder):
            os.makedirs(test_folder)
        return test_folder
