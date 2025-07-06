import json
import os
import pytest
import logging
from datetime import datetime
from pathlib import Path
from pytest_metadata.plugin import metadata_key

from test.api.user_api import UserApi


# --------------------------------- 日志相关
def create_logger(log_file_path=None):
    logger = logging.getLogger('pytest')
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s (%(filename)s:%(lineno)s)',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    if not log_file_path:
        # timestamp = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
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

@pytest.fixture(scope='class')
def user_api():
    return UserApi()

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


# --------------------------------- 测试报告相关
def pytest_configure(config):
    # 设置元数据
    config.stash[metadata_key].update({
        "项目名称": "磐基接口自动化",
        "接口模块": "磐基接口模块",
        "接口地址": "http:***.com"
    })

    # 设置日志文件路径
    # time_now = datetime.now().strftime('%Y%m%d')
    time_now = datetime.now().strftime('%Y%m%d%H%M%S')
    config.option.log_file = os.path.join(config.rootdir, 'logs', f'pytest_{time_now}.log')


def pytest_html_report_title(report):
    report.title = "测试报告"


def pytest_html_results_summary(prefix, summary, postfix):
    prefix.extend([
        "<p>所属部门: 磐基自动化测试</p>",
        "<p>测试人员: Alan Huang</p>"
    ])


def pytest_html_results_table_header(cells):
    cells.insert(2, "<th>描述</th>")
    cells.insert(1, '<th class="sortable time" data-column-type="time">测试时间</th>')


def pytest_html_results_table_row(report, cells):
    cells.insert(2, f"<td>{report.description}</td>")
    cells.insert(1, f'<td class="col-time">{datetime.utcnow()}</td>')


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