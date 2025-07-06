import os
import allure
import yaml

from common.log import Logger
from test.test_base import TestBase

logger = Logger().get_logger()

def read_yaml(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    else:
        logger.error(f"YAML file not found: {file_path}")
        return {}

@allure.feature("文章接口测试")
class PostTest:
    def setup_class(self):
        self.api = TestBase()
        data_path = './data/api_test_data.yaml'
        self.test_data = read_yaml(data_path)

    @allure.story("获取文章列表")
    @allure.title("获取文章列表")
    def test_get_posts(self):
        test_case = self.test_data.get('test_get_posts')
        response = self.api.send_request(
            method=test_case['method'],
            path=test_case['path']
        )
        body_json = response.json()
        assert response.status_code == test_case['expected_status']
        assert body_json[0]["userId"] == 1