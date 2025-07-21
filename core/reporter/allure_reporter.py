"""Allure报告处理模块"""
import json
import traceback
from typing import Dict, Any, List

import allure
from requests import Response

from common.log.logger import Logger
from common.patterns import CacheSingleton

logger = Logger().get_logger()


class AllureReporter:
    """Allure报告处理器"""
    
    def __init__(self):
        self.cache = CacheSingleton()
        self.severity_map = {
            'P0': allure.severity_level.BLOCKER,
            'P1': allure.severity_level.CRITICAL,
            'P2': allure.severity_level.NORMAL,
            'P3': allure.severity_level.MINOR,
            'P4': allure.severity_level.TRIVIAL
        }
    
    def setup_test_case_info(self, test_case_data: Dict[str, Any]) -> None:
        """设置测试用例基本信息"""
        test_case_id = test_case_data.get('test_case_id', 'N/A')
        module = test_case_data.get('module', 'General')
        name = test_case_data.get('name', 'Unnamed Test Case')
        description = test_case_data.get('description', '')
        priority = test_case_data.get('priority', 'P1')
        tags = test_case_data.get('tags', '').split(',') if test_case_data.get('tags') else []
        
        # Allure 报告相关信息
        allure.dynamic.story(module)
        allure.dynamic.title(f"{test_case_id}: {name}")
        allure.dynamic.description(description)
        
        # 设置优先级
        allure.dynamic.severity(self.severity_map.get(priority, allure.severity_level.NORMAL))
        
        # 添加标签
        for tag in tags:
            if tag.strip():
                allure.dynamic.tag(tag.strip())
    
    def attach_test_case_data(self, test_case_data: Dict[str, Any]) -> None:
        """附加测试用例数据"""
        with allure.step("测试用例数据"):
            allure.attach(
                json.dumps(self.cache.prepare_data(test_case_data), indent=2, ensure_ascii=False),
                name="Test Case Data",
                attachment_type=allure.attachment_type.JSON
            )
    
    def attach_dependency_result(self, dependency_id: str, dependency_result: Dict[str, Any]) -> None:
        """附加依赖执行结果"""
        # 记录依赖执行结果
        if dependency_result['response']:
            try:
                response_json = dependency_result['response'].json()
                allure.attach(
                    json.dumps(response_json, indent=2, ensure_ascii=False),
                    name=f"{dependency_id} Response",
                    attachment_type=allure.attachment_type.JSON
                )
            except json.JSONDecodeError:
                allure.attach(
                    dependency_result['response'].text,
                    name=f"{dependency_id} Response (Text)",
                    attachment_type=allure.attachment_type.TEXT
                )
        
        # 记录提取的变量
        if dependency_result['extracted_vars']:
            allure.attach(
                json.dumps(dependency_result['extracted_vars'], indent=2, ensure_ascii=False),
                name=f"{dependency_id} Extracted Variables",
                attachment_type=allure.attachment_type.JSON
            )
    
    def attach_request_info(self, method: str, path: str, headers: Dict, params: Dict, body: Any) -> None:
        """附加请求信息"""
        path = self.cache.prepare_data(path)
        headers = self.cache.prepare_data(headers)
        params = self.cache.prepare_data(params)
        body = self.cache.prepare_data(body)
        with allure.step(f"发送 {method} 请求到 {path}"):
            allure.attach(
                json.dumps(headers, indent=2, ensure_ascii=False),
                name="Request Headers",
                attachment_type=allure.attachment_type.JSON
            )
            
            if params:
                allure.attach(
                    json.dumps(params, indent=2, ensure_ascii=False),
                    name="Request Params",
                    attachment_type=allure.attachment_type.JSON
                )
            
            if body:
                if isinstance(body, dict):
                    allure.attach(
                        json.dumps(body, indent=2, ensure_ascii=False),
                        name="Request Body",
                        attachment_type=allure.attachment_type.JSON
                    )
                else:
                    allure.attach(
                        str(body),
                        name="Request Body",
                        attachment_type=allure.attachment_type.TEXT
                    )
    
    def attach_response_info(self, response: Response) -> None:
        """附加响应信息"""
        with allure.step("处理响应"):
            allure.attach(
                str(response.status_code),
                name="Status Code",
                attachment_type=allure.attachment_type.TEXT
            )
            
            allure.attach(
                str(response.elapsed.total_seconds()),
                name="Response Time (s)",
                attachment_type=allure.attachment_type.TEXT
            )
            
            allure.attach(
                str(dict(response.headers)),
                name="Response Headers",
                attachment_type=allure.attachment_type.TEXT
            )
            
            try:
                response_json = response.json()
                allure.attach(
                    json.dumps(response_json, indent=2, ensure_ascii=False),
                    name="Response Body",
                    attachment_type=allure.attachment_type.JSON
                )
            except json.JSONDecodeError:
                allure.attach(
                    response.text,
                    name="Response Body (Text)",
                    attachment_type=allure.attachment_type.TEXT
                )
                logger.warning("Response is not JSON, attaching response text.")
    
    def attach_extracted_variables(self, extracted_vars: Dict[str, Any]) -> None:
        """附加提取的变量"""
        with allure.step("提取响应变量"):
            allure.attach(
                json.dumps(extracted_vars, indent=2, ensure_ascii=False),
                name="Extracted Variables",
                attachment_type=allure.attachment_type.JSON
            )
            
            # 附加当前变量池
            current_vars = {k: v for k, v in self.cache._cache.items() if not k.startswith('_')}
            allure.attach(
                json.dumps(current_vars, indent=2, ensure_ascii=False),
                name="Current Variable Pool",
                attachment_type=allure.attachment_type.JSON
            )
    
    def attach_assertion_results(self, assertion_results: Any) -> List[str]:
        """附加断言结果
        
        Returns:
            失败的断言信息列表
        """
        failed_assertions = []
        
        with allure.step("执行断言"):
            # 处理断言结果
            if isinstance(assertion_results, list):
                for i, result in enumerate(assertion_results):
                    status = "✅ 通过" if result.success else "❌ 失败"
                    allure.attach(
                        f"规则: {result.rule}\n预期: {result.expected}\n实际: {result.actual}\n结果: {status}",
                        name=f"断言 {i + 1}",
                        attachment_type=allure.attachment_type.TEXT
                    )
                    
                    if not result.success:
                        failed_assertions.append(
                            f"断言失败: {result.rule} - 预期: {result.expected}, 实际: {result.actual}"
                        )
            elif not assertion_results:
                failed_assertions.append("断言失败: 未能执行任何断言")
        
        return failed_assertions
    
    def attach_exception(self, exception: Exception) -> None:
        """附加异常信息"""
        allure.attach(
            traceback.format_exc(),
            name="Exception",
            attachment_type=allure.attachment_type.TEXT
        )
    
    def attach_execution_time(self, elapsed_time: float) -> None:
        """附加执行时间"""
        allure.attach(
            f"{elapsed_time:.4f}s",
            name="Execution Time",
            attachment_type=allure.attachment_type.TEXT
        )
    
    def attach_request_response_info(self, test_case_data: Dict[str, Any], response: Response) -> None:
        """附加请求和响应信息"""
        method = test_case_data.get('method', 'GET')
        path = test_case_data.get('path', '')
        headers = test_case_data.get('headers', {})
        params = test_case_data.get('params', {})
        body = test_case_data.get('body', {})
        
        # 附加请求信息
        self.attach_request_info(method, path, headers, params, body)
        
        # 附加响应信息
        self.attach_response_info(response)
    
    def attach_dependency_results(self, dependency_results: Dict[str, Any]) -> None:
        """附加依赖执行结果"""
        for dependency_id, result in dependency_results.items():
            self.attach_dependency_result(dependency_id, result)
