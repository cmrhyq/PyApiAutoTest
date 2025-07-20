import configparser
import pytest
import json
import shutil
import allure
import os
import time
import traceback
import concurrent.futures
from typing import Dict, List, Any
from datetime import datetime

from common.excel.excel_parser import read_test_cases_from_excel
from common.http.request_util import RequestUtil
from common.validators.assert_util import assert_response
from common.log.logger import Logger
from core.patterns.singleton import CacheSingleton

logger = Logger().get_logger()

# 读取配置
config = configparser.ConfigParser()
config.read('config/config.ini')

# API配置
BASE_URL = config['API']['base_url']
TIMEOUT = int(config['API'].get('timeout', '30'))
MAX_RETRIES = int(config['API'].get('max_retries', '3'))
RETRY_DELAY = int(config['API'].get('retry_delay', '1'))

# 测试配置
EXCEL_FILE = config['TEST'].get('excel_file', 'data/test_cases.xlsx')
PARALLEL_EXECUTION = config['TEST'].getboolean('parallel_execution', False)
MAX_WORKERS = int(config['TEST'].get('max_workers', '4'))

# 报告配置
ALLURE_RESULTS_DIR = config['REPORT'].get('allure_results_dir', './reports/allure-results')
ALLURE_REPORT_DIR = config['REPORT'].get('allure_report_dir', './reports/allure-report')

# 初始化缓存和请求工具
cache = CacheSingleton()
request_client = RequestUtil(
    base_url=BASE_URL,
    timeout=TIMEOUT,
    max_retries=MAX_RETRIES,
    retry_delay=RETRY_DELAY
)


class TestSession:
    """测试会话管理类，负责测试环境的初始化和清理"""

    @staticmethod
    @pytest.fixture(scope="session", autouse=True)
    def setup_session():
        """会话级别的setup和teardown"""
        start_time = time.time()
        logger.info("===== Test Session Start =====")
        logger.info(f"Configuration: BASE_URL={BASE_URL}, PARALLEL={PARALLEL_EXECUTION}, MAX_WORKERS={MAX_WORKERS}")

        # 清理变量池
        cache.clear()

        # 确保allure-results目录存在并清理旧文件
        TestSession._prepare_allure_directories()

        # 记录测试开始时间
        with open(os.path.join(ALLURE_RESULTS_DIR, "environment.properties"), "w") as f:
            f.write(f"BASE_URL={BASE_URL}\n")
            f.write(f"START_TIME={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"PARALLEL_EXECUTION={PARALLEL_EXECUTION}\n")
            f.write(f"MAX_WORKERS={MAX_WORKERS}\n")

        yield

        # 会话结束，记录总耗时
        elapsed = time.time() - start_time
        logger.info(f"===== Test Session End (Total time: {elapsed:.2f}s) =====")

        # 记录测试结束时间
        with open(os.path.join(ALLURE_RESULTS_DIR, "environment.properties"), "a") as f:
            f.write(f"END_TIME={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"DURATION={elapsed:.2f}s\n")

    @staticmethod
    def _prepare_allure_directories():
        """准备Allure报告目录"""
        # 确保allure-results目录存在
        if not os.path.exists(ALLURE_RESULTS_DIR):
            os.makedirs(ALLURE_RESULTS_DIR)
        else:
            # 清理旧的 Allure 报告结果
            for file in os.listdir(ALLURE_RESULTS_DIR):
                file_path = os.path.join(ALLURE_RESULTS_DIR, file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)

        # 清理旧的报告目录
        if os.path.exists(ALLURE_REPORT_DIR):
            shutil.rmtree(ALLURE_REPORT_DIR)


class TestCaseManager:
    """测试用例管理类，负责测试用例的加载、依赖分析和执行"""

    # 用于存储所有测试用例的列表
    all_test_cases: List[Dict[str, Any]] = []

    # 用于存储已处理的测试用例的字典，方便查找依赖
    processed_test_cases_map: Dict[str, Dict[str, Any]] = {}

    # 用于存储已执行的测试用例结果
    executed_test_cases: Dict[str, Dict[str, Any]] = {}

    # 依赖关系图
    dependency_graph: Dict[str, List[str]] = {}

    @classmethod
    def load_test_cases(cls):
        """加载并预处理所有测试用例"""
        logger.info(f"Reading test cases from {EXCEL_FILE}...")
        try:
            cls.all_test_cases = read_test_cases_from_excel(EXCEL_FILE)

            # 将测试用例按 test_case_id 存储到字典中，方便查找依赖
            cls.processed_test_cases_map = {case['test_case_id']: case for case in cls.all_test_cases}

            # 构建依赖关系图
            cls._build_dependency_graph()

            # 检查循环依赖
            cls._check_circular_dependencies()

            logger.info(f"Successfully loaded {len(cls.all_test_cases)} test cases.")
            return True
        except Exception as e:
            logger.error(f"Failed to load test cases: {e}")
            return False

    @classmethod
    def _build_dependency_graph(cls):
        """构建测试用例依赖关系图"""
        cls.dependency_graph = {}

        for case in cls.all_test_cases:
            case_id = case['test_case_id']
            pre_condition = case.get('pre_condition_tc')

            # 初始化依赖图
            if case_id not in cls.dependency_graph:
                cls.dependency_graph[case_id] = []

            # 添加依赖关系
            if pre_condition:
                if pre_condition not in cls.dependency_graph:
                    cls.dependency_graph[pre_condition] = []
                cls.dependency_graph[pre_condition].append(case_id)

    @classmethod
    def _check_circular_dependencies(cls):
        """检查循环依赖"""
        visited = {}
        rec_stack = {}

        def is_cyclic_util(case_id):
            visited[case_id] = True
            rec_stack[case_id] = True

            # 检查所有依赖此用例的用例
            for dependent in cls.dependency_graph.get(case_id, []):
                # 如果未访问，则递归检查
                if not visited.get(dependent, False):
                    if is_cyclic_util(dependent):
                        return True
                # 如果在递归栈中，则存在循环
                elif rec_stack.get(dependent, False):
                    return True

            # 回溯时从递归栈中移除
            rec_stack[case_id] = False
            return False

        # 检查所有用例
        for case_id in cls.dependency_graph:
            if not visited.get(case_id, False):
                if is_cyclic_util(case_id):
                    raise ValueError(f"Circular dependency detected in test cases involving {case_id}")

    @classmethod
    def get_runnable_test_cases(cls):
        """获取可运行的测试用例"""
        return [case for case in cls.all_test_cases if case.get('is_run')]


# 加载测试用例
if not TestCaseManager.load_test_cases():
    logger.critical("Failed to load test cases. Exiting...")
    exit(1)


# 动态生成 Pytest 测试函数
def pytest_generate_tests(metafunc):
    """通过 pytest_generate_tests 钩子函数动态参数化"""
    if "test_case_data" in metafunc.fixturenames:
        runnable_test_cases = TestCaseManager.get_runnable_test_cases()

        ids = [f"{case['test_case_id']}_{case['name']}" for case in runnable_test_cases]
        metafunc.parametrize("test_case_data", runnable_test_cases, ids=ids)



class TestExecutor:
    """测试执行器类，负责执行测试用例"""

    @staticmethod
    def execute_test_case(test_case_data: Dict[str, Any], is_dependency: bool = False) -> Dict[str, Any]:
        """执行单个测试用例

        Args:
            test_case_data: 测试用例数据
            is_dependency: 是否作为依赖执行

        Returns:
            包含执行结果的字典
        """
        test_case_id = test_case_data.get('test_case_id', 'N/A')

        # 如果已经执行过，直接返回结果
        if test_case_id in TestCaseManager.executed_test_cases and not is_dependency:
            return TestCaseManager.executed_test_cases[test_case_id]

        start_time = time.time()
        result = {
            'test_case_id': test_case_id,
            'success': False,
            'response': None,
            'error': None,
            'duration': 0,
            'extracted_vars': {}
        }

        try:
            # 执行前置依赖
            pre_condition_tc = test_case_data.get('pre_condition_tc')
            if pre_condition_tc:
                TestExecutor._execute_dependency(pre_condition_tc)

            # 执行当前请求
            method = test_case_data.get('method')
            path = test_case_data.get('path')
            headers = test_case_data.get('headers')
            params = test_case_data.get('params')
            body = test_case_data.get('body')
            extract_vars = test_case_data.get('extract_vars', {})
            asserts = test_case_data.get('asserts', [])

            # 发送请求
            response = request_client.send_request(method, path, headers=headers, params=params, body=body)
            result['response'] = response

            # 提取变量
            if extract_vars:
                extracted = request_client.extract_variables_from_response(response, extract_vars)
                result['extracted_vars'] = extracted

            # 执行断言
            assertion_results = assert_response(response, asserts)
            result['assertion_results'] = assertion_results
            result['success'] = all(ar.success for ar in assertion_results) if isinstance(assertion_results,
                                                                                          list) else assertion_results

        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
        finally:
            result['duration'] = time.time() - start_time

            # 存储执行结果
            if not is_dependency:
                TestCaseManager.executed_test_cases[test_case_id] = result

        return result

    @staticmethod
    def _execute_dependency(dependency_id: str) -> Dict[str, Any]:
        """执行依赖测试用例

        Args:
            dependency_id: 依赖的测试用例ID

        Returns:
            依赖测试用例的执行结果
        """
        # 检查依赖是否已执行
        if dependency_id in TestCaseManager.executed_test_cases:
            return TestCaseManager.executed_test_cases[dependency_id]

        # 获取依赖测试用例数据
        dependent_case = TestCaseManager.processed_test_cases_map.get(dependency_id)
        if not dependent_case:
            raise ValueError(f"Dependency test case '{dependency_id}' not found.")

        # 执行依赖测试用例
        logger.info(f"Executing dependency test case: {dependency_id}")
        result = TestExecutor.execute_test_case(dependent_case, is_dependency=True)

        # 检查依赖执行结果
        if not result['success']:
            raise ValueError(f"Dependency test case '{dependency_id}' failed: {result['error']}")

        return result

    @classmethod
    def execute_test_cases_in_parallel(cls, test_cases: List[Dict[str, Any]], max_workers: int = 4) -> Dict[
        str, Dict[str, Any]]:
        """并行执行多个测试用例

        Args:
            test_cases: 测试用例列表
            max_workers: 最大工作线程数

        Returns:
            测试用例ID到执行结果的映射
        """
        results = {}

        # 按照依赖关系对测试用例进行排序
        sorted_test_cases = cls._sort_test_cases_by_dependency(test_cases)

        # 分批执行测试用例
        batches = cls._create_execution_batches(sorted_test_cases)
        logger.info(f"Created {len(batches)} execution batches for parallel processing")

        for batch_index, batch in enumerate(batches):
            logger.info(f"Executing batch {batch_index + 1}/{len(batches)} with {len(batch)} test cases")

            # 使用线程池并行执行当前批次的测试用例
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, len(batch))) as executor:
                # 提交所有任务
                future_to_case = {executor.submit(cls.execute_test_case, case): case for case in batch}

                # 收集结果
                for future in concurrent.futures.as_completed(future_to_case):
                    case = future_to_case[future]
                    case_id = case.get('test_case_id')
                    try:
                        result = future.result()
                        results[case_id] = result
                        status = "✅ 成功" if result['success'] else "❌ 失败"
                        logger.info(f"Test case {case_id} completed: {status} in {result['duration']:.2f}s")
                    except Exception as e:
                        logger.error(f"Test case {case_id} raised an exception: {e}")
                        results[case_id] = {
                            'test_case_id': case_id,
                            'success': False,
                            'error': str(e),
                            'duration': 0
                        }

        return results

    @classmethod
    def _sort_test_cases_by_dependency(cls, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """根据依赖关系对测试用例进行排序

        Args:
            test_cases: 测试用例列表

        Returns:
            排序后的测试用例列表
        """
        # 创建依赖图
        dependency_graph = {}
        for case in test_cases:
            case_id = case['test_case_id']
            dependency_graph[case_id] = case.get('pre_condition_tc')

        # 拓扑排序
        sorted_cases = []
        visited = set()
        temp_visited = set()

        def visit(case_id):
            if case_id in temp_visited:
                raise ValueError(f"Circular dependency detected involving {case_id}")

            if case_id not in visited:
                temp_visited.add(case_id)

                # 访问依赖
                dependency = dependency_graph.get(case_id)
                if dependency:
                    visit(dependency)

                temp_visited.remove(case_id)
                visited.add(case_id)
                sorted_cases.append(case_id)

        # 对每个测试用例执行拓扑排序
        for case in test_cases:
            case_id = case['test_case_id']
            if case_id not in visited:
                visit(case_id)

        # 根据排序结果重新排列测试用例
        case_map = {case['test_case_id']: case for case in test_cases}
        return [case_map[case_id] for case_id in sorted_cases if case_id in case_map]

    @classmethod
    def _create_execution_batches(cls, sorted_test_cases: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """创建测试用例执行批次

        将测试用例分成多个批次，每个批次中的测试用例可以并行执行
        同一批次中的测试用例之间没有依赖关系

        Args:
            sorted_test_cases: 按依赖关系排序的测试用例列表

        Returns:
            测试用例批次列表
        """
        batches = []
        current_batch = []
        processed_dependencies = set()

        for case in sorted_test_cases:
            case_id = case['test_case_id']
            dependency = case.get('pre_condition_tc')

            # 如果没有依赖，或者依赖已经处理过，则可以加入当前批次
            if not dependency or dependency in processed_dependencies:
                current_batch.append(case)
            else:
                # 如果有未处理的依赖，则开始新的批次
                if current_batch:
                    batches.append(current_batch)
                    # 记录已处理的测试用例ID
                    for processed_case in current_batch:
                        processed_dependencies.add(processed_case['test_case_id'])
                    current_batch = [case]
                else:
                    current_batch.append(case)

        # 添加最后一个批次
        if current_batch:
            batches.append(current_batch)

        return batches


# 核心测试函数
@allure.epic("API自动化测试")
@allure.feature("数据驱动测试")
def test_api_from_excel(test_case_data):
    """从Excel数据执行API测试"""
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
    severity_map = {'P0': allure.severity_level.BLOCKER, 'P1': allure.severity_level.CRITICAL,
                    'P2': allure.severity_level.NORMAL, 'P3': allure.severity_level.MINOR,
                    'P4': allure.severity_level.TRIVIAL}
    allure.dynamic.severity(severity_map.get(priority, allure.severity_level.NORMAL))

    # 添加标签
    for tag in tags:
        if tag.strip():
            allure.dynamic.tag(tag.strip())

    # 记录测试用例数据
    with allure.step("测试用例数据"):
        allure.attach(json.dumps(cache.prepare_data(test_case_data), indent=2, ensure_ascii=False),
                      name="Test Case Data",
                      attachment_type=allure.attachment_type.JSON)

    # 记录开始执行
    logger.info(f"\n--- Executing Test Case: {test_case_id} - {name} ---")

    # 执行测试用例
    with allure.step(f"执行测试用例 {test_case_id}"):
        start_time = time.time()
        pre_condition_tc = test_case_data.get('pre_condition_tc')

        # 处理前置依赖
        if pre_condition_tc:
            with allure.step(f"执行前置依赖: {pre_condition_tc}"):
                try:
                    dependency_result = TestExecutor._execute_dependency(pre_condition_tc)

                    # 记录依赖执行结果
                    if dependency_result['response']:
                        try:
                            response_json = dependency_result['response'].json()
                            allure.attach(json.dumps(response_json, indent=2, ensure_ascii=False),
                                          name=f"{pre_condition_tc} Response",
                                          attachment_type=allure.attachment_type.JSON)
                        except json.JSONDecodeError:
                            allure.attach(dependency_result['response'].text,
                                          name=f"{pre_condition_tc} Response (Text)",
                                          attachment_type=allure.attachment_type.TEXT)

                    # 记录提取的变量
                    if dependency_result['extracted_vars']:
                        allure.attach(json.dumps(dependency_result['extracted_vars'], indent=2, ensure_ascii=False),
                                      name=f"{pre_condition_tc} Extracted Variables",
                                      attachment_type=allure.attachment_type.JSON)
                except Exception as e:
                    logger.error(f"Failed to execute dependency {pre_condition_tc}: {e}")
                    pytest.fail(f"Failed to execute dependency {pre_condition_tc}: {e}")

        # 执行当前测试用例
        try:
            # 获取测试数据
            method = test_case_data.get('method')
            path = cache.prepare_data(test_case_data.get('path'))
            headers = cache.prepare_data(test_case_data.get('headers', {}))
            params = cache.prepare_data(test_case_data.get('params', {}))
            body = cache.prepare_data(test_case_data.get('body'))
            extract_vars = test_case_data.get('extract_vars', {})
            asserts = test_case_data.get('asserts', [])

            # 发送请求
            with allure.step(f"发送 {method} 请求到 {path}"):
                allure.attach(json.dumps(headers, indent=2, ensure_ascii=False),
                              name="Request Headers",
                              attachment_type=allure.attachment_type.JSON)

                if params:
                    allure.attach(json.dumps(params, indent=2, ensure_ascii=False),
                                  name="Request Params",
                                  attachment_type=allure.attachment_type.JSON)

                if body:
                    if isinstance(body, dict):
                        allure.attach(json.dumps(body, indent=2, ensure_ascii=False),
                                      name="Request Body",
                                      attachment_type=allure.attachment_type.JSON)
                    else:
                        allure.attach(str(body),
                                      name="Request Body",
                                      attachment_type=allure.attachment_type.TEXT)

                response = request_client.send_request(method, path, headers=headers, params=params, body=body)

            # 处理响应
            with allure.step("处理响应"):
                allure.attach(str(response.status_code),
                              name="Status Code",
                              attachment_type=allure.attachment_type.TEXT)

                allure.attach(str(response.elapsed.total_seconds()),
                              name="Response Time (s)",
                              attachment_type=allure.attachment_type.TEXT)

                allure.attach(str(dict(response.headers)),
                              name="Response Headers",
                              attachment_type=allure.attachment_type.TEXT)

                try:
                    response_json = response.json()
                    allure.attach(json.dumps(response_json, indent=2, ensure_ascii=False),
                                  name="Response Body",
                                  attachment_type=allure.attachment_type.JSON)
                except json.JSONDecodeError:
                    allure.attach(response.text,
                                  name="Response Body (Text)",
                                  attachment_type=allure.attachment_type.TEXT)
                    logger.warning("Response is not JSON, attaching response text.")

            # 提取变量
            if extract_vars:
                with allure.step("提取响应变量"):
                    extracted = request_client.extract_variables_from_response(response, extract_vars)
                    allure.attach(json.dumps(extracted, indent=2, ensure_ascii=False),
                                  name="Extracted Variables",
                                  attachment_type=allure.attachment_type.JSON)
                    allure.attach(json.dumps({k: v for k, v in cache._cache.items() if not k.startswith('_')}, indent=2,
                                             ensure_ascii=False),
                                  name="Current Variable Pool",
                                  attachment_type=allure.attachment_type.JSON)

            # 执行断言
            with allure.step("执行断言"):
                assertion_results = assert_response(response, asserts)

                # 处理断言结果
                if isinstance(assertion_results, list):
                    for i, result in enumerate(assertion_results):
                        status = "✅ 通过" if result.success else "❌ 失败"
                        allure.attach(
                            f"规则: {result.rule}\n预期: {result.expected}\n实际: {result.actual}\n结果: {status}",
                            name=f"断言 {i + 1}",
                            attachment_type=allure.attachment_type.TEXT)

                    if not all(result.success for result in assertion_results):
                        failed_assertions = [result for result in assertion_results if not result.success]
                        failure_message = "\n".join(
                            [f"断言失败: {result.rule} - 预期: {result.expected}, 实际: {result.actual}"
                             for result in failed_assertions])
                        pytest.fail(failure_message)
                elif not assertion_results:
                    pytest.fail("断言失败: 未能执行任何断言")

        except Exception as e:
            logger.error(f"Test case '{test_case_id}' failed: {e}")
            allure.attach(traceback.format_exc(), name="Exception", attachment_type=allure.attachment_type.TEXT)
            pytest.fail(f"Test case '{test_case_id}' failed: {e}")

        # 记录执行时间
        elapsed = time.time() - start_time
        allure.attach(f"{elapsed:.4f}s", name="Execution Time", attachment_type=allure.attachment_type.TEXT)
        logger.info(f"--- Test Case: {test_case_id} - {name} Completed in {elapsed:.4f}s ---")