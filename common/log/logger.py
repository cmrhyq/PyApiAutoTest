from pathlib import Path
from typing import Optional, Union, Dict, Any
from loguru import logger
import sys
import functools
import time


class Logger:
    """
    增强型日志工具类
    支持：
    1. 控制台彩色输出
    2. 文件日志按时间/大小切割
    3. 日志装饰器，用于记录函数执行时间和参数
    4. 支持多实例，不同模块使用不同的日志配置
    5. 支持日志压缩和保留策略
    """
    
    _instances: Dict[str, 'Logger'] = {}
    
    def __new__(cls, name: str = "app", *args, **kwargs):
        """单例模式，相同name返回相同实例"""
        if name not in cls._instances:
            cls._instances[name] = super().__new__(cls)
        return cls._instances[name]
    
    def __init__(
        self,
        name: str = "app",
        log_path: Union[str, Path] = Path.cwd() / "logs",
        level: str = "DEBUG",
        rotation: str = "00:00",
        retention: str = "30 days",
        compression: str = "zip",
        colorize: bool = True,
        format_string: Optional[str] = None
    ):
        # 避免重复初始化
        if hasattr(self, 'initialized'):
            return
        self.initialized = True
        
        self.name = name
        self.log_path = Path(log_path)
        self.level = level
        
        # 确保日志目录存在
        self.log_path.mkdir(parents=True, exist_ok=True)
        
        # 默认日志格式
        self.format_string = format_string or (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        # 配置logger
        self._configure_logger(colorize, rotation, retention, compression)
        
        # 绑定logger实例
        self.logger = logger.bind(name=name)
    
    def _configure_logger(self, colorize: bool, rotation: str, retention: str, compression: str):
        """配置日志处理器"""
        # 移除默认处理器
        logger.remove()
        
        # 添加控制台处理器
        logger.add(
            sys.stdout,
            format=self.format_string,
            filter=lambda record: record["extra"].get("name") == self.name,
            level=self.level,
            colorize=colorize
        )
        
        # 添加文件处理器
        log_file = self.log_path / f"{self.name}.log"
        logger.add(
            str(log_file),
            format=self.format_string,
            filter=lambda record: record["extra"].get("name") == self.name,
            level=self.level,
            rotation=rotation,
            retention=retention,
            compression=compression,
            encoding="utf-8",
            enqueue=True  # 异步写入
        )
    
    @staticmethod
    def log_execution(level: str = "DEBUG"):
        """函数执行日志装饰器"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                logger_instance = Logger()
                log = getattr(logger_instance.logger, level.lower())
                
                # 记录函数开始执行
                log(f"开始执行函数: {func.__name__}")
                log(f"参数: args={args}, kwargs={kwargs}")
                
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    log(f"函数 {func.__name__} 执行成功，耗时: {time.time() - start_time:.3f}秒")
                    return result
                except Exception as e:
                    log(f"函数 {func.__name__} 执行失败，耗时: {time.time() - start_time:.3f}秒")
                    log(f"错误信息: {str(e)}")
                    raise
            return wrapper
        return decorator
    
    def get_logger(self):
        """获取logger实例"""
        return self.logger
    
    # 便捷属性访问
    @property
    def debug(self): return self.logger.debug
    
    @property
    def info(self): return self.logger.info
    
    @property
    def warning(self): return self.logger.warning
    
    @property
    def error(self): return self.logger.error
    
    @property
    def critical(self): return self.logger.critical