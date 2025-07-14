import json
import re
from typing import Dict, Any, List, Union, Optional
import jsonpath_ng.ext as jsonpath # 用于 JSONPath 断言
import allure

from common.log import Logger

logger = Logger().get_logger()

class AssertionResult:
    """断言结果类，用于存储断言结果信息"""
    def __init__(self, passed: bool, message: str = "", expected: Any = None, actual: Any = None):
        self.passed = passed
        self.message = message
        self.expected = expected
        self.actual = actual


def assert_response(response, asserts: List[Dict[str, Any]]) -> bool:
    """
    根据断言规则列表验证响应
    :param response: HTTP响应对象
    :param asserts: 断言规则列表
    :return: 是否全部断言通过
    """
    if not asserts:
        logger.info("No asserts defined for this test case.")
        return True

    is_passed = True
    
    # 尝试解析JSON响应
    response_json = None
    try:
        response_json = response.json()
    except json.JSONDecodeError:
        logger.warning("Response is not JSON, JSONPath assertions may fail.")
    
    # 记录响应信息到Allure报告
    allure.attach(
        json.dumps(response_json, indent=2, ensure_ascii=False) if response_json else response.text,
        name="Response Body",
        attachment_type=allure.attachment_type.JSON if response_json else allure.attachment_type.TEXT
    )
    
    # 记录响应头信息到Allure报告
    allure.attach(
        json.dumps(dict(response.headers), indent=2),
        name="Response Headers",
        attachment_type=allure.attachment_type.JSON
    )

    # 执行断言
    for assertion in asserts:
        assert_type = assertion.get("type")
        assert_value = assertion.get("value")
        result = _perform_assertion(response, response_json, assertion)
        
        # 记录断言结果
        if result.passed:
            logger.info(f"Assert Passed: {result.message}")
            allure.attach(
                f"Expected: {result.expected}\nActual: {result.actual}",
                name=f"✅ {assert_type} Assertion Passed",
                attachment_type=allure.attachment_type.TEXT
            )
        else:
            logger.error(f"Assert Failed: {result.message}")
            allure.attach(
                f"Expected: {result.expected}\nActual: {result.actual}",
                name=f"❌ {assert_type} Assertion Failed",
                attachment_type=allure.attachment_type.TEXT
            )
            is_passed = False

    return is_passed


def _perform_assertion(response, response_json: Optional[Dict], assertion: Dict) -> AssertionResult:
    """
    执行单个断言
    :param response: HTTP响应对象
    :param response_json: 解析后的JSON响应，可能为None
    :param assertion: 断言规则
    :return: 断言结果对象
    """
    assert_type = assertion.get("type")
    assert_value = assertion.get("value")
    operator = assertion.get("operator", "eq")  # 默认为等于操作符
    
    # 状态码断言
    if assert_type == "status_code":
        return _assert_status_code(response.status_code, assert_value, operator)
    
    # JSONPath断言
    elif assert_type == "json_path":
        if response_json is None:
            return AssertionResult(
                passed=False,
                message="Response is not JSON, cannot perform JSONPath assertion.",
                expected=f"Valid JSON with path {assertion.get('expr')}",
                actual="Non-JSON response"
            )
        return _assert_json_path(response_json, assertion.get("expr"), assert_value, operator)
    
    # 响应文本包含断言
    elif assert_type == "text_contains":
        return _assert_text_contains(response.text, assert_value)
    
    # 响应文本匹配正则表达式
    elif assert_type == "text_regex":
        return _assert_text_regex(response.text, assert_value)
    
    # 响应头断言
    elif assert_type == "header":
        header_name = assertion.get("name")
        return _assert_header(response.headers, header_name, assert_value, operator)
    
    # 响应时间断言
    elif assert_type == "response_time":
        return _assert_response_time(response.elapsed.total_seconds() * 1000, assert_value, operator)
    
    # 未知断言类型
    else:
        return AssertionResult(
            passed=False,
            message=f"Unknown assert type: {assert_type}",
            expected="Valid assertion type",
            actual=assert_type
        )


def _assert_status_code(actual: int, expected: int, operator: str) -> AssertionResult:
    """状态码断言"""
    passed = _compare_values(actual, expected, operator)
    return AssertionResult(
        passed=passed,
        message=f"Status code {_get_operator_text(operator)} {expected}" + ("" if passed else f", got {actual}"),
        expected=expected,
        actual=actual
    )


def _assert_json_path(response_json: Dict, expr: str, expected: Any, operator: str) -> AssertionResult:
    """JSONPath断言"""
    try:
        jsonpath_expr = jsonpath.parse(expr)
        matches = jsonpath_expr.find(response_json)
        
        if not matches:
            return AssertionResult(
                passed=False,
                message=f"JSONPath '{expr}' found no match in response.",
                expected=f"Path '{expr}' exists",
                actual="Path not found"
            )
        
        actual_value = matches[0].value
        passed = _compare_values(actual_value, expected, operator)
        
        return AssertionResult(
            passed=passed,
            message=f"JSONPath '{expr}' {_get_operator_text(operator)} {expected}" + ("" if passed else f", got {actual_value}"),
            expected=expected,
            actual=actual_value
        )
    except Exception as e:
        return AssertionResult(
            passed=False,
            message=f"Error parsing or executing JSONPath '{expr}': {e}",
            expected=f"Valid JSONPath expression",
            actual=f"Error: {str(e)}"
        )


def _assert_text_contains(text: str, substring: str) -> AssertionResult:
    """文本包含断言"""
    passed = substring in text
    return AssertionResult(
        passed=passed,
        message=f"Response text {'contains' if passed else 'does not contain'} '{substring}'",
        expected=f"Text containing '{substring}'",
        actual=f"Text {'containing' if passed else 'not containing'} '{substring}'"
    )


def _assert_text_regex(text: str, pattern: str) -> AssertionResult:
    """正则表达式匹配断言"""
    try:
        regex = re.compile(pattern)
        match = regex.search(text)
        passed = match is not None
        
        return AssertionResult(
            passed=passed,
            message=f"Response text {'matches' if passed else 'does not match'} regex pattern '{pattern}'",
            expected=f"Text matching pattern '{pattern}'",
            actual=f"Text {'matching' if passed else 'not matching'} pattern"
        )
    except re.error as e:
        return AssertionResult(
            passed=False,
            message=f"Invalid regex pattern '{pattern}': {e}",
            expected="Valid regex pattern",
            actual=f"Invalid pattern: {str(e)}"
        )


def _assert_header(headers: Dict, header_name: str, expected: str, operator: str) -> AssertionResult:
    """响应头断言"""
    if header_name.lower() not in {k.lower() for k in headers.keys()}:
        return AssertionResult(
            passed=False,
            message=f"Header '{header_name}' not found in response",
            expected=f"Header '{header_name}' exists",
            actual="Header not found"
        )
    
    # 不区分大小写查找头部
    actual_header_name = next(k for k in headers.keys() if k.lower() == header_name.lower())
    actual_value = headers[actual_header_name]
    
    passed = _compare_values(actual_value, expected, operator)
    return AssertionResult(
        passed=passed,
        message=f"Header '{header_name}' {_get_operator_text(operator)} '{expected}'" + ("" if passed else f", got '{actual_value}'"),
        expected=expected,
        actual=actual_value
    )


def _assert_response_time(actual_ms: float, expected_ms: float, operator: str) -> AssertionResult:
    """响应时间断言"""
    passed = _compare_values(actual_ms, expected_ms, operator)
    return AssertionResult(
        passed=passed,
        message=f"Response time {_get_operator_text(operator)} {expected_ms}ms" + ("" if passed else f", got {actual_ms:.2f}ms"),
        expected=f"{expected_ms}ms",
        actual=f"{actual_ms:.2f}ms"
    )


def _compare_values(actual: Any, expected: Any, operator: str) -> bool:
    """根据操作符比较两个值"""
    if operator == "eq":
        return actual == expected
    elif operator == "ne":
        return actual != expected
    elif operator == "gt":
        return actual > expected
    elif operator == "ge":
        return actual >= expected
    elif operator == "lt":
        return actual < expected
    elif operator == "le":
        return actual <= expected
    elif operator == "contains":
        return expected in actual
    elif operator == "not_contains":
        return expected not in actual
    else:
        logger.warning(f"Unknown operator: {operator}, falling back to equality check")
        return actual == expected


def _get_operator_text(operator: str) -> str:
    """获取操作符的文本表示"""
    op_map = {
        "eq": "equals",
        "ne": "not equals",
        "gt": "greater than",
        "ge": "greater than or equal to",
        "lt": "less than",
        "le": "less than or equal to",
        "contains": "contains",
        "not_contains": "does not contain"
    }
    return op_map.get(operator, operator)