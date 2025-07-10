# test_runner.py
import pytest
import configparser
import os
import json
import shutil
import allure # 导入 allure 模块

from common.excel.excel_parser import read_test_cases_from_excel
from common.http.request_util import RequestUtil
from common.validators.assert_util import assert_response
from common.log import Logger
from core.patterns.singleton import CacheSingleton

cache = CacheSingleton()
logger = Logger().get_logger()

# 读取配置
# config = configparser.ConfigParser()
# config.read('config/config.ini')
BASE_URL = "https://jsonplaceholder.typicode.com"
EXCEL_FILE = 'data/test_cases.xlsx' # 假设 Excel 文件路径

# 实例化请求工具
request_client = RequestUtil(BASE_URL)

# 在所有测试开始前清理变量池
# 在文件开头导入部分添加
import os

# 在setup_session函数中添加以下代码（替换原有的清理代码）
@pytest.fixture(scope="session", autouse=True)
def setup_session(logger):
    logger.info("--- Test Session Start ---")
    cache.clear() # 清理变量池
    
    # 确保allure-results目录存在
    if not os.path.exists("allure-results"):
        os.makedirs("allure-results")
    else:
        # 清理旧的 Allure 报告结果
        for file in os.listdir("allure-results"):
            file_path = os.path.join("allure-results", file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
    
    if os.path.exists("allure-report"):
        shutil.rmtree("allure-report")
        
    yield
    logger.info("--- Test Session End ---")

# 用于存储所有测试用例的列表
all_test_cases = []
# 用于存储已处理的测试用例的字典，方便查找依赖
processed_test_cases_map = {}

# 读取并预处理所有测试用例
logger.info(f"Reading test cases from {EXCEL_FILE}...")
try:
    all_test_cases = read_test_cases_from_excel(EXCEL_FILE)
    # 将测试用例按 test_case_id 存储到字典中，方便查找依赖
    processed_test_cases_map = {case['test_case_id']: case for case in all_test_cases}
    logger.info(f"Successfully loaded {len(all_test_cases)} test cases.")
except Exception as e:
    logger.error(f"Failed to load test cases: {e}")
    exit(1) # 如果文件加载失败，直接退出

# Pytest Hooks 或 Fixtures 可以在这里定义
# 例如：如果需要每个用例开始前重置部分变量，可以定义一个 fixture
# @pytest.fixture(scope="function")
# def clear_variables_per_test():
#     # variable_manager.clear_variables() # 谨慎使用，这会清除所有变量，包括前置接口提取的
#     pass


# 动态生成 Pytest 测试函数
# 通过 pytest_generate_tests 钩子函数动态参数化
# 这样 pytest 会为每一条数据生成一个独立的测试用例
def pytest_generate_tests(metafunc):
    if "test_case_data" in metafunc.fixturenames:
        runnable_test_cases = [case for case in all_test_cases if case.get('is_run')]
        ids = [f"{case['test_case_id']}_{case['name']}" for case in runnable_test_cases]
        metafunc.parametrize("test_case_data", runnable_test_cases, ids=ids)

# 核心测试函数
@allure.epic("接口自动化测试")
@allure.feature("数据驱动测试")
def test_api_from_excel(test_case_data, logger):
    test_case_id = test_case_data.get('test_case_id', 'N/A')
    module = test_case_data.get('module', 'General')
    name = test_case_data.get('name', 'Unnamed Test Case')
    method = test_case_data.get('method')
    path = test_case_data.get('path')
    headers = test_case_data.get('headers')
    params = test_case_data.get('params')
    body = test_case_data.get('body')
    extract_vars = test_case_data.get('extract_vars', {})
    asserts = test_case_data.get('asserts', [])
    pre_condition_tc = test_case_data.get('pre_condition_tc')
    priority = test_case_data.get('priority', 'P1')
    description = test_case_data.get('description', '')

    # Allure 报告相关信息
    allure.dynamic.story(module)
    allure.dynamic.title(f"{test_case_id}: {name}")
    allure.dynamic.description(description)
    allure.dynamic.severity(priority.lower())
    allure.attach(json.dumps(test_case_data, indent=2, ensure_ascii=False), name="Test Case Data", attachment_type=allure.attachment_type.JSON)


    logger.info(f"\n--- Executing Test Case: {test_case_id} - {name} ---")

    # 处理前置依赖
    if pre_condition_tc:
        logger.info(f"Executing pre-condition test case: {pre_condition_tc}")
        # 查找依赖的测试用例数据
        dependent_case = processed_test_cases_map.get(pre_condition_tc)
        if not dependent_case:
            pytest.fail(f"Pre-condition test case '{pre_condition_tc}' not found.")

        with allure.step(f"前置条件: 执行依赖用例 {pre_condition_tc}"):
            try:
                # 递归调用自身执行依赖用例（如果依赖的用例也需要执行，这个地方需要更复杂的逻辑避免死循环）
                # 简化处理：假设依赖用例已经执行过或者只执行一次
                # 实际上，这里需要一个专门的函数来执行依赖，并且能够保证不重复执行
                # 为了简化，我们直接在这里模拟执行依赖的逻辑
                dependent_response = request_client.send_request(
                    dependent_case.get('method'),
                    dependent_case.get('path'),
                    headers=dependent_case.get('headers'),
                    params=dependent_case.get('params'),
                    body=dependent_case.get('body')
                )
                # 提取依赖用例的变量到变量池
                request_client.extract_variables_from_response(dependent_response, dependent_case.get('extract_vars', {}))
                allure.attach(json.dumps(dependent_response.json(), indent=2, ensure_ascii=False), name=f"{pre_condition_tc} Response", attachment_type=allure.attachment_type.JSON)
                allure.attach(f"提取的变量: {cache._cache}", name=f"{pre_condition_tc} Extracted Variables")
            except Exception as e:
                pytest.fail(f"Failed to execute pre-condition test case '{pre_condition_tc}': {e}")


    # 执行当前请求
    response = None
    try:
        with allure.step(f"发送 {method} 请求到 {path}"):
            response = request_client.send_request(method, path, headers=headers, params=params, body=body)
            # allure.attach(json.dumps(response.json(), indent=2, ensure_ascii=False), name="Response Body", attachment_type=allure.attachment_type.JSON)
            # allure.attach(str(response.status_code), name="Status Code", attachment_type=allure.attachment_type.TEXT)

        # 修正后的代码段：
        with allure.step("处理响应和断言"):
            allure.attach(str(response.status_code), name="Status Code",attachment_type=allure.attachment_type.TEXT)
            try:
                response_json_content = response.json()
                allure.attach(json.dumps(response_json_content, indent=2, ensure_ascii=False),name="Response Body", attachment_type=allure.attachment_type.JSON)
            except json.JSONDecodeError:
                allure.attach(response.text, name="Response Body (Text)",attachment_type=allure.attachment_type.TEXT)
                logger.warning("Response is not JSON, attaching response text.")

        # 提取变量
        if extract_vars:
            with allure.step("提取响应变量"):
                request_client.extract_variables_from_response(response, extract_vars)
                allure.attach(f"当前变量池: {cache._cache}", name="Current Variable Pool")

        # 执行断言
        with allure.step("执行断言"):
            assert_result = assert_response(response, asserts)
            if not assert_result:
                pytest.fail("Assertions failed for this test case.")

    except Exception as e:
        pytest.fail(f"Test case '{test_case_id}' failed with error: {e}")

    logger.info(f"--- Test Case: {test_case_id} - {name} Completed ---")