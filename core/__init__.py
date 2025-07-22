"""Core模块 - API自动化测试框架的核心组件"""

__version__ = "1.0.0"
__author__ = "API Test Framework"

# 导出主要组件
from .config import ConfigManager, APIConfig, TestConfig, ReportConfig
from .session import TestSession
from .manager import TestCaseManager
from .executor import TestExecutor
from .reporter import AllureReporter

__all__ = [
    'ConfigManager',
    'APIConfig',
    'TestConfig', 
    'ReportConfig',
    'TestSession',
    'TestCaseManager',
    'TestExecutor',
    'AllureReporter'
]