import json
import os
from typing import Dict, Any, List

import yaml

from common.log import Logger
from config.manager.manager_config import ManagerConfig

logger = Logger().get_logger()

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
        logger.info(f"加载环境配置文件: {self.env_file}")
        with open(self.env_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def load_test_config(self, file_path) -> Dict[str, Any]:
        """
        加载测试配置
        :param file_path: 测试文件路径
        """
        logger.info(f"加载测试配置: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def load_test_file(self) -> list[Any]:
        """
        获取目录下所有的测试配置文件
        """
        file_list = []
        files = os.listdir(self.test_folder)
        logger.info(f"加载目录下的所有测试配置文件: {self.test_folder}")
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
    response = json.loads("""
{
  "userId": 1,
  "id": 1,
  "title": "sunt aut facere repellat provident occaecati excepturi optio reprehenderit",
  "body": "quia et suscipitsuscipit recusandae consequuntur expedita et cumreprehenderit molestiae ut ut quas totamnostrum rerum est autem sunt rem eveniet architecto"
}
    """)
    response_data = response.json() if hasattr(response, 'json') else response
    loader = DataLoader()
    file_list = loader.load_test_file()
    for file in file_list:
        cases = loader.get_test_cases(file)
        for case in cases:
            response_extract = case.get("response_extract", {})
            extracted_data = {}
            for key, extract_path in response_extract.items():
                print(type(response_data))
                # 处理嵌套路径，例如 "data.user.id"
                if isinstance(extract_path, str) and '.' in extract_path:
                    parts = extract_path.split('.')
                    value = response_data
                    for part in parts:
                        if isinstance(value, dict) and part in value:
                            value = value[part]
                        else:
                            value = None
                            break
                # 处理直接字段
                elif isinstance(extract_path, str):
                    value = response_data.get(extract_path)
                # 处理JMESPath或JSONPath表达式（如果需要）
                elif isinstance(extract_path, dict) and 'jmespath' in extract_path:
                    # 这里可以添加JMESPath支持，需要安装jmespath库
                    # import jmespath
                    # value = jmespath.search(extract_path['jmespath'], response_data)
                    logger.warning(f"JMESPath提取未实现: {extract_path}")
                    value = None
                else:
                    value = None

                # 存储提取的值
                extracted_data[key] = value
                print(extracted_data)