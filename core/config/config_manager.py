"""配置管理模块"""
import configparser
import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class APIConfig:
    """API配置类"""
    base_url: str
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 1


@dataclass
class MailConfig:
    """邮件配置类"""
    host: str = "smtp.163.com"
    port: int = 465
    sender: str = "123@163.com"
    license: str = "your_license_key_here"  # 使用实际的授权码或密码


@dataclass
class LogConfig:
    """日志配置类"""
    level: str = 'INFO'
    rotation: str = '00:00'
    retention: str = '30 days'
    compression: str = 'zip'


@dataclass
class TestConfig:
    """测试配置类"""
    excel_file: str = 'data/test_cases.xlsx'
    parallel_execution: bool = False
    max_workers: int = 4


@dataclass
class ReportConfig:
    """报告配置类"""
    allure_results_dir: str = './reports/allure-results'
    allure_report_dir: str = './reports/allure-report'
    html_report_dir: str = './reports/html-report'
    junit_report_dir: str = "./reports/junit-report"


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = 'config/config.ini'):
        self.config_file = config_file
        self._config = configparser.ConfigParser()
        self._load_config()
        
    def _load_config(self):
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"配置文件不存在: {self.config_file}")
        
        self._config.read(self.config_file, encoding='utf-8')
    
    @property
    def api_config(self) -> APIConfig:
        """获取API配置"""
        api_section = self._config['API']
        return APIConfig(
            base_url=api_section['base_url'],
            timeout=int(api_section.get('timeout', '30')),
            max_retries=int(api_section.get('max_retries', '3')),
            retry_delay=int(api_section.get('retry_delay', '1'))
        )

    @property
    def mail_config(self) -> MailConfig:
        """获取邮件配置"""
        mail_section = self._config['MAIL']
        return MailConfig(
            host=mail_section['host'],
            port=int(mail_section.get('port', '25')),
            sender=mail_section['sender'],
            license=mail_section['license']
        )

    @property
    def log_config(self) -> LogConfig:
        """获取日志配置"""
        log_section = self._config['LOG']
        return LogConfig(
            level=log_section.get('level', 'INFO'),
            rotation=log_section.get('rotation', '00:00'),
            retention=log_section.get('retention', '30 days'),
            compression=log_section.get('compression', 'zip')
        )
    
    @property
    def test_config(self) -> TestConfig:
        """获取测试配置"""
        test_section = self._config['TEST']
        return TestConfig(
            excel_file=test_section.get('excel_file', 'data/test_cases.xlsx'),
            parallel_execution=test_section.getboolean('parallel_execution', False),
            max_workers=int(test_section.get('max_workers', '4'))
        )
    
    @property
    def report_config(self) -> ReportConfig:
        """获取报告配置"""
        report_section = self._config['REPORT']
        return ReportConfig(
            allure_results_dir=report_section.get('allure_results_dir', './reports/allure-results'),
            allure_report_dir=report_section.get('allure_report_dir', './reports/allure-report'),
            html_report_dir=report_section.get('html_report_dir', './reports/html-report'),
            junit_report_dir= report_section.get('junit_report_dir', './reports/junit-report')
        )
    
    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置"""
        return {
            'api': self.api_config,
            'mail': self.mail_config,
            'log': self.log_config,
            'test': self.test_config,
            'report': self.report_config
        }