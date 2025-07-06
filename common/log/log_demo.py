# 方式1：直接使用默认日志
from common.log import info, error
info("普通信息")
error("错误信息")

# 方式2：创建自定义logger
from common.log import Logger
custom_logger = Logger().get_logger()
custom_logger.info("自定义日志")

# 方式3：使用日志装饰器
from common.log import log_execution

@log_execution(level="INFO")
def some_function(x, y):
    return x + y