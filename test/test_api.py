import allure
import json
import jmespath

from common.log import Logger
from core.validators.response_validator import ResponseValidator

# 配置日志记录
logger = Logger().get_logger()

@allure.feature("API自动化测试")
class TestAPI:
    """API测试类"""
    # TODO 从测试报告上看，要把每一个接口当成一个接口来执行，不能当成一个步骤来执行
    def test_api_cases(self, api_client, test_cases, cache):
        """执行所有API测试用例"""
        for case in test_cases:
            self._execute_test_case(api_client, case, cache)

    def _execute_test_case(self, api_client, case, cache):
        """执行单个测试用例"""
        # 提取测试用例信息
        name = case.get('name', 'Unknown')
        description = case.get('description', '')
        method = case.get('method', 'GET').upper()
        endpoint = case.get('endpoint', '')
        path_params = case.get('path_params', [])
        headers = case.get('headers', {})
        params = case.get('params', {})
        body = case.get('body', None)
        response_extract = case.get('response_extract', {})
        # expected_status = case.get('expected_status', 200)
        # expected_response = case.get('expected_response', None)
        # response_contains = case.get('response_contains', [])
        # response_schema = case.get('response_schema', None)

        # 如果路径中有参数，替换路径参数
        # TODO 实现 {name} 这类参数可以从缓存中读取或者从配置中中读取
        for param in path_params:
            endpoint = endpoint.replace(f"{{{param}}}", str(path_params.get(param, '')))

        # 设置Allure报告信息
        allure.dynamic.title(name)
        allure.dynamic.description(description)
        allure.dynamic.tag(method)
        allure.dynamic.label("severity", self._get_severity(method))

        # 添加测试步骤
        with allure.step(f"发送{method}请求到{endpoint}"):
            # 记录请求信息
            self._attach_request_info(method, endpoint, headers, params, body)

            # 准备请求参数
            kwargs = {}
            if headers:
                kwargs['headers'] = headers
            if params:
                kwargs['params'] = params
            if body:
                kwargs['json'] = body

            # 发送请求
            response = api_client._request(method, endpoint, **kwargs)

            # 记录响应信息
            self._attach_response_info(response)

        # 验证响应
        with allure.step("验证响应结果"):
            self._validate_response(response, case, name)

        if response_extract:
            with allure.step("提取响应结果"):
                self._extract_response(response, response_extract, cache)

        logger.info(f"测试用例 '{name}' 执行完成")

    def _get_severity(self, method):
        """根据HTTP方法获取严重程度"""
        severity_map = {
            'GET': 'normal',
            'POST': 'critical',
            'PUT': 'major',
            'DELETE': 'critical',
            'PATCH': 'major'
        }
        return severity_map.get(method, 'normal')

    def _attach_request_info(self, method, endpoint, headers, params, body):
        """附加请求信息到Allure报告"""
        request_info = {
            "method": method,
            "endpoint": endpoint,
            "headers": headers,
            "params": params,
            "body": body
        }
        allure.attach(
            json.dumps(request_info, ensure_ascii=False, indent=2),
            "请求信息",
            allure.attachment_type.JSON
        )

    def _attach_response_info(self, response):
        """附加响应信息到Allure报告"""
        response_info = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "response_time": f"{response.elapsed.total_seconds():.3f}s"
        }

        # 添加响应体
        try:
            response_info["body"] = response.json()
        except:
            response_info["body"] = response.text

        allure.attach(
            json.dumps(response_info, ensure_ascii=False, indent=2),
            "响应信息",
            allure.attachment_type.JSON
        )

        # 单独附加响应时间
        allure.attach(
            f"{response.elapsed.total_seconds():.3f}s",
            "响应时间",
            allure.attachment_type.TEXT
        )

    def _validate_response(self, response, case, test_name):
        """验证响应结果"""
        expected_status = case.get('expected_status', 200)
        expected_response = case.get('expected_response', None)
        response_contains = case.get('response_contains', [])
        response_schema = case.get('response_schema', None)

        # 验证状态码
        with allure.step(f"验证状态码为{expected_status}"):
            assert ResponseValidator.validate_status_code(response, expected_status), \
                f"测试用例 '{test_name}' 失败: 期望状态码 {expected_status}, 实际状态码 {response.status_code}"
            logger.info(f"测试用例 '{test_name}': 期望状态码 {expected_status}, 实际状态码 {response.status_code}")

        # 验证响应内容
        if expected_response is not None:
            with allure.step("验证响应内容"):
                allure.attach(
                    json.dumps(expected_response, ensure_ascii=False, indent=2),
                    "期望响应内容",
                    allure.attachment_type.JSON
                )
                assert ResponseValidator.validate_response_content(response, expected_response), \
                    f"测试用例 '{test_name}' 失败: 响应内容不匹配\n期望: {expected_response}\n实际: {response.text}"
                logger.info(f"测试用例 '{test_name}': 响应内容不匹配\n期望: {expected_response}\n实际: {response.text}")

        # 验证响应包含内容
        if response_contains:
            with allure.step(f"验证响应包含内容: {response_contains}"):
                assert ResponseValidator.validate_response_contains(response, response_contains), \
                    f"测试用例 '{test_name}' 失败: 响应内容不包含期望的文本"
                logger.error(f"测试用例 '{test_name}': 响应内容不包含期望的文本")

        # 验证响应schema
        if response_schema:
            with allure.step("验证响应格式"):
                allure.attach(
                    json.dumps(response_schema, ensure_ascii=False, indent=2),
                    "期望响应格式",
                    allure.attachment_type.JSON
                )
                assert ResponseValidator.validate_response_schema(response, response_schema), \
                    f"测试用例 '{test_name}' 失败: 响应schema验证失败"
                logger.error(f"测试用例 '{test_name}': 响应schema验证失败")

    def _extract_response(self, response, response_extract, cache):
        """根据规则提取响应数据"""
        extracted_data = {}
        
        try:
            # 尝试获取JSON响应
            response_data = response.json() if hasattr(response, 'json') else response
            
            # 遍历需要提取的字段
            for key, extract_path in response_extract.items():
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
                    value = jmespath.search(extract_path['jmespath'], response_data)
                else:
                    value = None

                # 存储提取的值
                extracted_data[key] = value
                # 缓存响应数据
                cache.set(key, value)
                
        except Exception as e:
            logger.error(f"提取响应数据时出错: {e}")

        allure.attach(
            json.dumps(extracted_data, ensure_ascii=False, indent=2),
            "提取的响应数据",
            allure.attachment_type.JSON
        )

        return extracted_data
