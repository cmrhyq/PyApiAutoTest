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
from selenium.webdriver.common.by import By

from utils.time.time_utils import dt_strftime


class ManagerConfig(object):
    # 项目目录
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 页面元素目录
    ELEMENT_PATH = os.path.join(BASE_DIR, 'page_element')

    @property
    def log_file(self):
        """日志目录"""
        log_dir = os.path.join(self.BASE_DIR, 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        return os.path.join(log_dir, '{}.log'.format(dt_strftime()))

    @property
    def system_ini_file(self):
        """配置文件"""
        ini_file = os.path.join(self.BASE_DIR, 'app_config.ini')
        if not os.path.exists(ini_file):
            raise FileNotFoundError(f"配置文件{ini_file}不存在！")
        return ini_file

    @property
    def test_data_folder(self):
        """测试文件"""
        test_data = os.path.join(self.BASE_DIR, 'data')
        if not os.path.exists(test_data):
            os.makedirs(test_data)
        return test_data


if __name__ == '__main__':
    cm = ManagerConfig()
    print(cm.BASE_DIR)
