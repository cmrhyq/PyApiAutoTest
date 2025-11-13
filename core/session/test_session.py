"""测试会话管理模块"""
import os
import shutil
import time
import pytest
from datetime import datetime
from typing import Generator

from common.log.logger import Logger
from core.config.config_manager import ConfigManager
from core.patterns.singleton.cache_singleton import CacheSingleton

logger = Logger().get_logger()


class TestSession:
    """测试会话管理类，负责测试环境的初始化和清理"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.cache = CacheSingleton()
        self.report_config = config_manager.report_config
        self.test_config = config_manager.test_config
        self.api_config = config_manager.api_config
    
    def setup_session(self) -> Generator[None, None, None]:
        """会话级别的setup和teardown"""
        start_time = time.time()
        logger.info("===== Test Session Start =====")
        logger.info(
            f"Configuration: BASE_URL={self.config_manager.api_config.base_url}, "
            f"PARALLEL={self.config_manager.test_config.parallel_execution}, "
            f"MAX_WORKERS={self.config_manager.test_config.max_workers}"
        )
        
        # 清理变量池
        self.cache.clear()
        
        # 确保allure-results目录存在并清理旧文件
        self._prepare_allure_directories()
        
        # 记录测试开始时间
        self._write_environment_properties(start_time=True)
        
        yield
        
        # 会话结束，记录总耗时
        elapsed = time.time() - start_time
        logger.info(f"===== Test Session End (Total time: {elapsed:.2f}s) =====")
        
        # 记录测试结束时间
        self._write_environment_properties(start_time=False, elapsed=elapsed)
    
    def _prepare_allure_directories(self) -> None:
        """准备Allure报告目录"""
        allure_results_dir = self.report_config.allure_results_dir
        allure_report_dir = self.report_config.allure_report_dir
        
        # 确保allure-results目录存在
        if not os.path.exists(allure_results_dir):
            os.makedirs(allure_results_dir)
        else:
            # 清理旧的 Allure 报告结果
            for file in os.listdir(allure_results_dir):
                file_path = os.path.join(allure_results_dir, file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
        
        # 清理旧的报告目录
        if os.path.exists(allure_report_dir):
            shutil.rmtree(allure_report_dir)
    
    def _write_environment_properties(self, start_time: bool = True, elapsed: float = None) -> None:
        """写入环境属性文件"""
        env_file = os.path.join(self.report_config.allure_results_dir, "environment.properties")
        
        if start_time:
            with open(env_file, "w", encoding='utf-8') as f:
                f.write(f"BASE_URL={self.api_config.base_url}\n")
                f.write(f"START_TIME={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"PARALLEL_EXECUTION={self.test_config.parallel_execution}\n")
                f.write(f"MAX_WORKERS={self.test_config.max_workers}\n")
        else:
            with open(env_file, "a", encoding='utf-8') as f:
                f.write(f"END_TIME={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"DURATION={elapsed:.2f}s\n")


# 全局pytest fixture
@pytest.fixture(scope="session", autouse=True)
def setup_session() -> Generator[None, None, None]:
    """全局会话级别的setup和teardown"""
    from core.config import ConfigManager
    
    config_manager = ConfigManager()
    cache = CacheSingleton()
    
    start_time = time.time()
    logger.info("===== Test Session Start =====")
    logger.info(
        f"Configuration: BASE_URL={config_manager.api_config.base_url}, "
        f"PARALLEL={config_manager.test_config.parallel_execution}, "
        f"MAX_WORKERS={config_manager.test_config.max_workers}"
    )
    
    # 清理变量池
    cache.clear()
    
    # 确保allure-results目录存在并清理旧文件
    _prepare_allure_directories(config_manager.report_config)
    
    # 记录测试开始时间
    _write_environment_properties(config_manager, start_time=True)
    
    yield
    
    # 会话结束，记录总耗时
    elapsed = time.time() - start_time
    logger.info(f"===== Test Session End (Total time: {elapsed:.2f}s) =====")
    
    # 记录测试结束时间
    _write_environment_properties(config_manager, start_time=False, elapsed=elapsed)


def _prepare_allure_directories(report_config) -> None:
    """准备Allure报告目录"""
    allure_results_dir = report_config.allure_results_dir
    allure_report_dir = report_config.allure_report_dir
    
    # 确保allure-results目录存在
    if not os.path.exists(allure_results_dir):
        os.makedirs(allure_results_dir)
    else:
        # 清理旧的 Allure 报告结果
        for file in os.listdir(allure_results_dir):
            file_path = os.path.join(allure_results_dir, file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
    
    # 清理旧的报告目录
    if os.path.exists(allure_report_dir):
        shutil.rmtree(allure_report_dir)


def _write_environment_properties(config_manager, start_time: bool = True, elapsed: float = None) -> None:
    """写入环境属性文件"""
    env_file = os.path.join(config_manager.report_config.allure_results_dir, "environment.properties")
    
    if start_time:
        with open(env_file, "w", encoding='utf-8') as f:
            f.write(f"BASE_URL={config_manager.api_config.base_url}\n")
            f.write(f"START_TIME={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"PARALLEL_EXECUTION={config_manager.test_config.parallel_execution}\n")
            f.write(f"MAX_WORKERS={config_manager.test_config.max_workers}\n")
    else:
        with open(env_file, "a", encoding='utf-8') as f:
            f.write(f"END_TIME={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"DURATION={elapsed:.2f}s\n")