"""重构后的测试运行器"""
import pytest
import allure
import time
import os
from typing import Dict, Any

from common.http.request_util import RequestUtil
from common.log.logger import Logger
from core.config import ConfigManager
from core.session import TestSession
from core.manager import TestCaseManager
from core.executor import TestExecutor
from core.reporter import AllureReporter
from common.patterns import CacheSingleton

logger = Logger().get_logger()

# 初始化配置管理器
# 从环境变量中获取配置文件路径和变量配置文件路径
config_file = os.environ.get('CONFIG_FILE', 'config/config.ini')
vars_config_file = os.environ.get('VARS_CONFIG_FILE', 'config/variables.ini')
config_manager = ConfigManager(config_file, vars_config_file)
configs = config_manager.get_all_configs()

# 初始化各个组件
cache = CacheSingleton()
request_client = RequestUtil(
    base_url=configs['api'].base_url,
    timeout=configs['api'].timeout,
    max_retries=configs['api'].max_retries,
    retry_delay=configs['api'].retry_delay
)
test_case_manager = TestCaseManager(configs['test'].excel_file)
test_executor = TestExecutor(request_client, test_case_manager)
test_session = TestSession(config_manager)
allure_reporter = AllureReporter()


# 加载测试用例
if not test_case_manager.load_test_cases():
    logger.critical("Failed to load test cases. Exiting...")
    exit(1)


# 动态生成 Pytest 测试函数
def pytest_generate_tests(metafunc):
    """通过 pytest_generate_tests 钩子函数动态参数化"""
    if "test_case_data" in metafunc.fixturenames:
        runnable_test_cases = test_case_manager.get_runnable_test_cases()
        ids = [f"{case['test_case_id']}_{case['name']}" for case in runnable_test_cases]
        metafunc.parametrize("test_case_data", runnable_test_cases, ids=ids)


# 核心测试函数
@allure.epic("API自动化测试")
@allure.feature("数据驱动测试")
def test_api_from_excel(test_case_data):
    """从Excel数据执行API测试"""
    test_case_id = test_case_data.get('test_case_id', 'N/A')
    
    # 设置Allure报告信息
    allure_reporter.setup_test_case_info(test_case_data)
    
    # 记录测试用例数据
    allure_reporter.attach_test_case_data(test_case_data)
    
    # 记录开始执行
    logger.info(f"\n--- Executing Test Case: {test_case_id} - {test_case_data.get('name', 'Unnamed')} ---")
    
    # 执行测试用例
    with allure.step(f"执行测试用例 {test_case_id}"):
        start_time = time.time()
        
        try:
            # 使用重构后的TestExecutor执行测试用例
            result = test_executor.execute_test_case(test_case_data)
            
            # 记录执行结果到Allure报告
            if result.get('dependency_results'):
                allure_reporter.attach_dependency_results(result['dependency_results'])
            
            if result.get('response'):
                allure_reporter.attach_request_response_info(
                    test_case_data, result['response']
                )
            
            if result.get('extracted_vars'):
                allure_reporter.attach_extracted_variables(result['extracted_vars'])
            
            if result.get('assertion_results'):
                allure_reporter.attach_assertion_results(result['assertion_results'])
            
            # 检查测试结果
            if not result['success']:
                if result.get('error'):
                    allure_reporter.attach_exception(result['error'])
                pytest.fail(result.get('error', '测试用例执行失败'))
                
        except Exception as e:
            logger.error(f"Test case '{test_case_id}' failed: {e}")
            allure_reporter.attach_exception(str(e))
            pytest.fail(f"Test case '{test_case_id}' failed: {e}")
        
        # 记录执行时间
        elapsed = time.time() - start_time
        allure_reporter.attach_execution_time(elapsed)
        logger.info(f"--- Test Case: {test_case_id} Completed in {elapsed:.4f}s ---")