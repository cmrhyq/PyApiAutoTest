from pathlib import Path
from typing import Optional, Union, Dict
from loguru import logger
import sys
import os
import functools
import time
import inspect
import json
import traceback
from datetime import datetime


class Logger:
    """
    增强型日志工具类
    支持：
    1. 控制台彩色输出
    2. 文件日志按时间/大小切割
    3. 日志装饰器，用于记录函数执行时间和参数
    4. 支持多实例，不同模块使用不同的日志配置
    5. 支持日志压缩和保留策略
    6. 支持结构化日志输出
    7. 支持异常堆栈跟踪
    8. 支持上下文管理器
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
        log_path: Union[str, Path] = None,
        level: str = None,
        rotation: str = None,
        retention: str = None,
        compression: str = None,
        colorize: bool = None,
        format_string: Optional[str] = None,
        env_prefix: str = "LOG"
    ):
        # 避免重复初始化
        if hasattr(self, 'initialized'):
            return
        self.initialized = True
        
        # 从环境变量或配置文件加载配置
        self.name = name
        self.env_prefix = env_prefix
        
        # 从配置文件或环境变量加载配置
        import configparser
        config = configparser.ConfigParser()
        try:
            config.read('config/config.ini')
            log_config = config['LOG'] if 'LOG' in config else {}
        except:
            log_config = {}
        
        # 配置优先级：参数 > 配置文件 > 环境变量 > 默认值
        self.level = level or log_config.get('level') or os.environ.get(f"{env_prefix}_LEVEL") or "DEBUG"
        self.rotation = rotation or log_config.get('rotation') or os.environ.get(f"{env_prefix}_ROTATION") or "00:00"
        self.retention = retention or log_config.get('retention') or os.environ.get(f"{env_prefix}_RETENTION") or "30 days"
        self.compression = compression or log_config.get('compression') or os.environ.get(f"{env_prefix}_COMPRESSION") or "zip"
        self.colorize = colorize if colorize is not None else True
        
        # 日志路径
        default_log_path = Path.cwd() / "logs"
        if log_path:
            self.log_path = Path(log_path)
        else:
            log_path_str = log_config.get('path') or os.environ.get(f"{env_prefix}_PATH")
            self.log_path = Path(log_path_str) if log_path_str else default_log_path
        
        # 确保日志目录存在
        self.log_path.mkdir(parents=True, exist_ok=True)
        
        # 默认日志格式
        self.format_string = format_string or log_config.get('format') or os.environ.get(f"{env_prefix}_FORMAT") or (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        # 配置logger
        self._configure_logger()
        
        # 绑定logger实例
        self.logger = logger.bind(name=name)
        
        # 添加上下文信息
        self.context = {}
        
        # 记录启动信息
        self.logger.info(f"===== Logger '{name}' initialized at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} =====")
    
    def _configure_logger(self):
        """配置日志处理器"""
        # 移除默认处理器
        logger.remove()
        
        # 添加控制台处理器
        logger.add(
            sys.stdout,
            format=self.format_string,
            filter=lambda record: record["extra"].get("name") == self.name,
            level=self.level,
            colorize=self.colorize,
            backtrace=True,  # 显示异常回溯
            diagnose=True    # 显示诊断信息
        )
        
        # 添加文件处理器 - 常规日志
        log_file = self.log_path / f"{self.name}.log"
        logger.add(
            str(log_file),
            format=self.format_string,
            filter=lambda record: record["extra"].get("name") == self.name and record["level"].no < 40,  # INFO及以下级别
            level=self.level,
            rotation=self.rotation,
            retention=self.retention,
            compression=self.compression,
            encoding="utf-8",
            enqueue=True  # 异步写入
        )
        
        # 添加文件处理器 - 错误日志（单独文件）
        error_log_file = self.log_path / f"{self.name}_error.log"
        logger.add(
            str(error_log_file),
            format=self.format_string,
            filter=lambda record: record["extra"].get("name") == self.name and record["level"].no >= 40,  # ERROR及以上级别
            level="ERROR",
            rotation=self.rotation,
            retention=self.retention,
            compression=self.compression,
            encoding="utf-8",
            enqueue=True  # 异步写入
        )
    
    def set_context(self, **kwargs):
        """设置日志上下文信息"""
        self.context.update(kwargs)
        self.logger = self.logger.bind(**kwargs)
        return self
    
    def clear_context(self):
        """清除日志上下文信息"""
        self.context = {}
        self.logger = logger.bind(name=self.name)
        return self
    
    def get_logger(self):
        """获取logger实例"""
        return self.logger
    
    def log_json(self, level: str, message: str, **kwargs):
        """记录JSON格式的结构化日志"""
        log_func = getattr(self.logger, level.lower())
        # 合并上下文和传入的参数
        data = {**self.context, **kwargs}
        if data:
            # 格式化为JSON字符串
            json_str = json.dumps(data, ensure_ascii=False, default=str)
            log_func(f"{message} | {json_str}")
        else:
            log_func(message)
    
    def exception(self, message: str, exc_info=True, **kwargs):
        """记录异常信息"""
        # 获取当前异常信息
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_type:
            # 格式化异常堆栈
            stack_trace = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            self.logger.opt(exception=exc_info).error(f"{message}\n{stack_trace}", **kwargs)
        else:
            self.logger.error(message, **kwargs)
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        if exc_type:
            self.exception(f"Exception occurred: {exc_val}")
        return False  # 不抑制异常
    
    def log_execution(self, level: str = "DEBUG", log_args: bool = True, log_result: bool = True):
        """函数执行日志装饰器"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 获取调用者信息
                caller_frame = inspect.currentframe().f_back
                caller_info = inspect.getframeinfo(caller_frame) if caller_frame else None
                caller_location = f"{caller_info.filename}:{caller_info.lineno}" if caller_info else "unknown"
                
                # 获取日志函数
                log = getattr(self.logger, level.lower())
                
                # 记录函数调用
                if log_args:
                    # 安全地格式化参数，避免大对象
                    def safe_repr(obj):
                        try:
                            s = repr(obj)
                            if len(s) > 100:
                                return f"{s[:97]}..."
                            return s
                        except:
                            return "<unprintable>"
                    
                    func_args = ', '.join([safe_repr(a) for a in args] + 
                                         [f"{k}={safe_repr(v)}" for k, v in kwargs.items()])
                    log(f"Calling {func.__name__}({func_args}) from {caller_location}")
                else:
                    log(f"Calling {func.__name__}() from {caller_location}")
                
                # 记录执行时间
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    elapsed_time = time.time() - start_time
                    
                    if log_result:
                        # 安全地记录结果
                        try:
                            result_repr = repr(result)
                            if len(result_repr) > 100:
                                result_repr = f"{result_repr[:97]}..."
                            log(f"{func.__name__} completed in {elapsed_time:.4f}s with result: {result_repr}")
                        except:
                            log(f"{func.__name__} completed in {elapsed_time:.4f}s with unprintable result")
                    else:
                        log(f"{func.__name__} completed in {elapsed_time:.4f}s")
                    
                    return result
                except Exception as e:
                    elapsed_time = time.time() - start_time
                    self.exception(f"{func.__name__} failed after {elapsed_time:.4f}s")
                    raise
            return wrapper
        return decorator
    
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
    
    # 静态方法装饰器，用于快速创建日志装饰器
    @staticmethod
    def static_log_execution(level: str = "DEBUG", log_args: bool = True, log_result: bool = True):
        """静态函数执行日志装饰器，适用于不想创建Logger实例的场景"""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                logger_instance = Logger()
                return logger_instance.log_execution(level, log_args, log_result)(func)(*args, **kwargs)
            return wrapper
        return decorator