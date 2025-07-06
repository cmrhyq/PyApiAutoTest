import jsonschema
from typing import Any, Dict, List
from common.log import Logger

# 配置日志记录
logger = Logger().get_logger()


class AssertionHelper:
    @staticmethod
    def assert_status_code(response, expected_code: int):
        """断言状态码"""
        actual_code = response.status_code
        assert actual_code == expected_code, f"期望状态码 {expected_code}, 实际状态码 {actual_code}"
        logger.info(f"状态码断言通过: {actual_code}")

    @staticmethod
    def assert_response_time(response, max_time: int):
        """断言响应时间"""
        response_time = response.elapsed.total_seconds() * 1000
        assert response_time <= max_time, f"响应时间超时: {response_time}ms > {max_time}ms"
        logger.info(f"响应时间断言通过: {response_time}ms")

    @staticmethod
    def assert_json_schema(response, schema: Dict[str, Any]):
        """断言JSON Schema"""
        try:
            json_data = response.json()
            jsonschema.validate(json_data, schema)
            logger.info("JSON Schema 验证通过")
        except jsonschema.ValidationError as e:
            logger.error(f"JSON Schema 验证失败: {e}")
            raise AssertionError(f"JSON Schema 验证失败: {e}")
        except ValueError as e:
            logger.error(f"响应不是有效的JSON: {e}")
            raise AssertionError(f"响应不是有效的JSON: {e}")

    @staticmethod
    def assert_contains(response, expected_values: List[str]):
        """断言响应包含指定内容"""
        response_text = response.text
        for value in expected_values:
            assert value in response_text, f"响应中未找到期望的内容: {value}"
            logger.info(f"包含断言通过: {value}")

    @staticmethod
    def assert_json_path(response, json_path: str, expected_value: Any):
        """断言JSON路径对应的值"""
        try:
            json_data = response.json()
            actual_value = AssertionHelper._get_json_path_value(json_data, json_path)
            assert actual_value == expected_value, f"JSON路径 {json_path} 的值不匹配: 期望 {expected_value}, 实际 {actual_value}"
            logger.info(f"JSON路径断言通过: {json_path} = {actual_value}")
        except (KeyError, TypeError) as e:
            logger.error(f"JSON路径 {json_path} 不存在: {e}")
            raise AssertionError(f"JSON路径 {json_path} 不存在: {e}")

    @staticmethod
    def _get_json_path_value(data: Dict[str, Any], path: str) -> Any:
        """获取JSON路径对应的值"""
        keys = path.split('.')
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current[key]
            else:
                raise KeyError(f"无法访问路径: {path}")
        return current

    @staticmethod
    def assert_headers(response, expected_headers: Dict[str, str]):
        """断言响应头"""
        actual_headers = response.headers
        for header, expected_value in expected_headers.items():
            assert header in actual_headers, f"响应头中缺少: {header}"
            actual_value = actual_headers[header]
            assert actual_value == expected_value, f"响应头 {header} 的值不匹配: 期望 {expected_value}, 实际 {actual_value}"
            logger.info(f"响应头断言通过: {header} = {actual_value}")


# 全局断言助手实例
assert_helper = AssertionHelper()