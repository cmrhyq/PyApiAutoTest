import json

import allure
import pytest
import logging
from datetime import datetime
from pathlib import Path

from core.http.http_client import HttpClient
from core.loader.data_loader import DataLoader
from core.patterns.singleton import CacheSingleton


@pytest.fixture(scope="session")
def data_loader():
    """数据加载器fixture"""
    return DataLoader()


@pytest.fixture(scope="session")
def api_client(data_loader):
    """API客户端fixture"""
    env_config = data_loader.get_current_env_config()

    # 添加环境信息到Allure报告
    allure.dynamic.label("environment", data_loader.load_env_config().get('current_env', 'unknown'))

    # 附加环境配置信息
    allure.attach(
        json.dumps(env_config, ensure_ascii=False, indent=2),
        "环境配置",
        allure.attachment_type.JSON
    )

    return HttpClient(
        base_url=env_config['base_url'],
        default_headers=env_config.get('headers', {}),
        timeout=env_config.get('timeout', 30)
    )


@pytest.fixture(scope="session")
def cache():
    return CacheSingleton()


@pytest.fixture(scope="session")
def test_cases(data_loader):
    """测试用例fixture"""
    # TODO 实现读取目录下的所有的测试用例文件然后再去执行测试
    cases = data_loader.get_test_cases("I:\\Code\\4.python_code\\PyApiAutoTest\\data\\api_test_data.yaml")

    # 附加测试用例配置信息
    allure.attach(
        json.dumps(cases, ensure_ascii=False, indent=2),
        "测试用例配置",
        allure.attachment_type.JSON
    )

    return cases


def pytest_configure(config):
    """pytest配置钩子"""
    # 设置Allure报告信息
    if hasattr(config, '_allure_config'):
        config._allure_config.title = "API自动化测试报告"
        config._allure_config.description = "基于pytest+requests的API自动化测试"


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """生成测试报告的钩子"""
    outcome = yield
    rep = outcome.get_result()

    # 只处理测试执行阶段
    if rep.when == "call":
        # 获取测试用例信息
        if hasattr(item, 'callspec') and 'case' in item.callspec.params:
            case = item.callspec.params['case']

            # 设置测试用例标签
            if 'method' in case:
                allure.dynamic.tag(case['method'])

            # 如果测试失败，附加更多信息
            if rep.failed:
                allure.attach(
                    rep.longrepr.reprcrash.message if hasattr(rep.longrepr, 'reprcrash') else str(rep.longrepr),
                    "失败信息",
                    allure.attachment_type.TEXT
                )


# --------------------------------- 日志相关
def create_logger(log_file_path=None):
    logger = logging.getLogger('pytest')
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s (%(filename)s:%(lineno)s)',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    if not log_file_path:
        timestamp = datetime.now().strftime("%Y-%m-%d")
        # timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_dir = Path("./logs")
        log_dir.mkdir(exist_ok=True)
        log_file_path = log_dir / f"pytest_{timestamp}.log"

    file_handler = logging.FileHandler(
        log_file_path,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    return logger

@pytest.fixture(scope="session")
def logger(pytestconfig):
    """Provide logger fixture for test cases"""
    return create_logger(pytestconfig.option.log_file)


@pytest.fixture(autouse=True)
def log_test_info(request, logger):
    """Automatically log test start and end"""
    test_name = request.node.name
    logger.info(f"Starting test: {test_name}")

    yield

    if hasattr(request.node, 'rep_call'):
        result = "PASSED" if request.node.rep_call.passed else "FAILED"
        logger.info(f"Test completed: {test_name}, Result: {result}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to get test results and handle test information"""
    outcome = yield
    report = outcome.get_result()

    # 设置测试结果属性
    setattr(item, f"rep_{report.when}", report)

    # 设置描述信息（来自docstring）
    report.description = str(item.function.__doc__)

    # 处理错误日志
    if call.excinfo is not None:
        msg = {
            "module": item.location[0],
            "function": item.name,
            "line": item.location[1],
            "message": str(call.excinfo.value).replace("\n", ":")
        }
        logging.error(json.dumps(msg, indent=4, ensure_ascii=False))

    """测试报告钩子"""
    if call.when == "call":
        if call.excinfo is not None:
            logging.error(f"测试失败: {item.name}, 错误: {call.excinfo.value}")
        else:
            logging.info(f"测试成功: {item.name}")