import time
import random
from functools import wraps

from common.log import Logger

logger = Logger().get_logger()

def retry_on_failure(retries=3, delay=1):
    """装饰器：如果测试失败，则自动重试"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    logger.info(f"Test {func.__name__} failed: {e}. Retrying {attempts}/{retries}...")
                    time.sleep(delay)
            raise Exception(f"Test {func.__name__} failed after {retries} retries")
        return wrapper
    return decorator

# 示例：测试类
class NetworkTest:
    @retry_on_failure(retries=3, delay=2)
    def unstable_test(self):
        """模拟不稳定的测试（30% 失败概率）"""
        if random.random() < 0.3:
            raise Exception("Random network failure")
        logger.info("Test executed successfully")

# 运行测试
test = NetworkTest()
test.unstable_test()