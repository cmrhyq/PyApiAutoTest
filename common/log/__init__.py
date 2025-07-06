from .logger import Logger

# 创建默认日志实例
default_logger = Logger(name="app").get_logger()

# 导出常用的日志方法
debug = default_logger.debug
info = default_logger.info
warning = default_logger.warning
error = default_logger.error
critical = default_logger.critical

# 导出日志装饰器
log_execution = Logger.log_execution

__all__ = [
    "Logger",
    "debug", "info", "warning", "error", "critical",
    "log_execution"
]