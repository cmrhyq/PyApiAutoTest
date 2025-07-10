from typing import Dict, Any, List
import jsonschema
import json

from common.log import Logger

# 配置日志记录
logger = Logger().get_logger()

class ResponseValidator:
    """响应验证器"""

    @staticmethod
    def validate_status_code(response, expected_status: int) -> bool:
        """验证状态码"""
        return response.status_code == expected_status

    @staticmethod
    def validate_response_content(response, expected_response: Any) -> bool:
        """验证响应内容"""
        if expected_response is None:
            return True

        try:
            actual_response = response.json()
        except json.JSONDecodeError:
            return False

        if isinstance(expected_response, dict):
            return ResponseValidator._validate_dict(actual_response, expected_response)
        else:
            return actual_response == expected_response

    @staticmethod
    def _validate_dict(actual: Dict, expected: Dict) -> bool:
        """验证字典类型的响应"""
        for key, value in expected.items():
            if key not in actual:
                return False
            if isinstance(value, dict):
                if not ResponseValidator._validate_dict(actual[key], value):
                    return False
            elif actual[key] != value:
                return False
        return True

    @staticmethod
    def validate_response_contains(response, contains_list: List[str]) -> bool:
        """验证响应是否包含指定内容"""
        try:
            response_text = response.text
            for item in contains_list:
                if item not in response_text:
                    return False
            return True
        except Exception:
            return False

    @staticmethod
    def validate_response_schema(response, schema: Dict[str, Any]) -> bool:
        """验证响应schema"""
        try:
            response_json = response.json()
            jsonschema.validate(response_json, schema)
            return True
        except (json.JSONDecodeError, jsonschema.ValidationError):
            return False