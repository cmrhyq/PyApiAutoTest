import json
import jsonpath_ng.ext as jsonpath # 用于 JSONPath 断言

from common.log import Logger

logger = Logger().get_logger()

def assert_response(response, asserts):
    """根据断言规则列表验证响应"""
    if not asserts:
        logger.info("No asserts defined for this test case.")
        return True

    is_passed = True
    try:
        response_json = response.json()
    except json.JSONDecodeError:
        response_json = None # 如果不是JSON，则无法进行JSONPath断言

    for assertion in asserts:
        assert_type = assertion.get("type")
        assert_value = assertion.get("value")

        if assert_type == "status_code":
            if response.status_code != assert_value:
                logger.error(f"Assert Failed: Expected status code {assert_value}, Got {response.status_code}")
                is_passed = False
        elif assert_type == "json_path":
            if response_json is None:
                logger.error(f"Assert Failed: Response is not JSON, cannot perform JSONPath assertion.")
                is_passed = False
                continue
            expr = assertion.get("expr")
            try:
                jsonpath_expr = jsonpath.parse(expr)
                matches = jsonpath_expr.find(response_json)
                if matches:
                    actual_value = matches[0].value
                    if actual_value != assert_value:
                        logger.error(f"Assert Failed: JSONPath '{expr}' expected '{assert_value}', Got '{actual_value}'")
                        is_passed = False
                else:
                    logger.error(f"Assert Failed: JSONPath '{expr}' found no match in response.")
                    is_passed = False
            except Exception as e:
                logger.error(f"Error parsing or executing JSONPath '{expr}': {e}")
                is_passed = False
        elif assert_type == "text_contains":
            if assert_value not in response.text:
                logger.error(f"Assert Failed: Response text does not contain '{assert_value}'")
                is_passed = False
        # 可以添加更多断言类型，例如 headers, cookies 等
        else:
            logger.warning(f"Unknown assert type: {assert_type}")

    return is_passed