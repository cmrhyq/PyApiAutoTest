import os
from typing import Dict, Any, List

import yaml

from config.manager_config import ManagerConfig


class DataLoader:
    """
    数据加载器，负责加载配置文件
    """
    def __init__(self):
        self.manager_config = ManagerConfig()
        self.env_file = self.manager_config.env_file
        self.test_folder = self.manager_config.test_file

    def load_env_config(self) -> Dict[str, Any]:
        """
        加载环境配置
        """
        with open(self.env_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def load_test_config(self, file_path) -> Dict[str, Any]:
        """
        加载测试配置
        :param file_path: 测试文件路径
        """
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def load_test_file(self) -> list[Any]:
        """
        获取目录下所有的测试配置文件
        """
        file_list = []
        files = os.listdir(self.test_folder)
        for file in files:
            if file.endswith("yaml"):
                file_list.append(os.path.join(self.test_folder, file))
        return file_list

    def get_current_env_config(self) -> Dict[str, Any]:
        """
        获取当前环境配置
        """
        env_config = self.load_env_config()
        current_env = env_config.get("current_env", "dev")
        return env_config["environments"][current_env]

    def get_test_cases(self, file_path) -> List[Dict[str, Any]]:
        """
        加载所有的测试用例
        """
        test_config = self.load_test_config(file_path)
        return test_config.get("test_cases", [])


if __name__ == '__main__':
    loader = DataLoader()
    # file_list = loader.load_test_file()
    # for file in file_list:
    #     print(loader.get_test_cases(file))
    print(loader.get_current_env_config())