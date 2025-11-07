"""配置管理模块"""
import configparser
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from common.patterns import CacheSingleton
from common.log.logger import Logger

logger = Logger().get_logger()


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

"""
解决configparser读取参数会自动将大写字母转换为小写的问题
"""
class MyConfigParser(configparser.ConfigParser):
    def __init__(self, defaults=None):
        super().__init__(defaults=defaults)

    def optionxform(self, optionstr):
        return optionstr


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = 'config/config.ini', variables_file: str = 'config/variables.ini'):
        self.config_file = config_file
        self.variables_file = variables_file
        self.cache = CacheSingleton()
        self._config = MyConfigParser()
        self._variables = MyConfigParser()
        # 初始化变量池，将配置文件中的变量加载到缓存中去
        self._load_config()
        self._load_variables()
        self._initialize_cache()
        
    def _load_config(self):
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"配置文件不存在: {self.config_file}")
        
        self._config.read(self.config_file, encoding='utf-8')
    
    def _load_variables(self):
        """加载变量配置文件"""
        if os.path.exists(self.variables_file):
            self._variables.read(self.variables_file, encoding='utf-8')
            logger.info(f"已加载变量配置文件: {self.variables_file}")
        else:
            logger.warning(f"变量配置文件不存在: {self.variables_file}，将使用默认空配置")
            # 创建一个空的变量配置节
            self._variables.add_section('VARIABLES')
    
    def _initialize_cache(self):
        """初始化缓存，将变量配置加载到缓存中"""
        if 'VARIABLES' in self._variables:
            for key, value in self._variables['VARIABLES'].items():
                self.cache.set(key, value)
                logger.info(f"已加载变量到缓存: {key}={value}")
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量值
        
        Args:
            name: 变量名
            default: 默认值
            
        Returns:
            变量值或默认值
        """
        # 首先从缓存中获取
        value = self.cache.get(name)
        if value is not None:
            return value
            
        # 如果缓存中没有，尝试从变量配置中获取
        if 'VARIABLES' in self._variables and name in self._variables['VARIABLES']:
            value = self._variables['VARIABLES'][name]
            # 将值存入缓存
            self.cache.set(name, value)
            return value
            
        return default
    
    def set_variable(self, name: str, value: Any, persist: bool = False) -> None:
        """设置变量值
        
        Args:
            name: 变量名
            value: 变量值
            persist: 是否持久化到配置文件
        """
        # 设置到缓存
        self.cache.set(name, value)
        
        # 如果需要持久化，则写入配置文件
        if persist:
            if 'VARIABLES' not in self._variables:
                self._variables.add_section('VARIABLES')
                
            self._variables['VARIABLES'][name] = str(value)
            with open(self.variables_file, 'w', encoding='utf-8') as f:
                self._variables.write(f)
            logger.info(f"变量已持久化到配置文件: {name}={value}")
    
    def get_all_variables(self) -> Dict[str, str]:
        """获取所有变量
        
        Returns:
            所有变量的字典
        """
        # 首先获取配置文件中的变量
        variables = {}
        if 'VARIABLES' in self._variables:
            variables.update(dict(self._variables['VARIABLES']))
            
        # 然后获取缓存中的变量，缓存中的变量会覆盖配置文件中的同名变量
        variables.update(self.cache.get_all())
        
        return variables
    
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
            'report': self.report_config,
            'variables': self.get_all_variables()
        }