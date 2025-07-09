from time import sleep

from common.log import Logger
from core.patterns.singleton.cache_singleton import CacheSingleton

logger = Logger().get_logger()


def cache_demo():
    """演示缓存单例的使用"""
    # 获取缓存实例
    cache = CacheSingleton()
    
    # 设置缓存
    cache.set("user_1", {"id": 1, "name": "张三", "role": "admin"})
    cache.set("config", {"debug": True, "timeout": 30})
    cache.set("temp_data", "这是临时数据", ttl=5)  # 5秒后过期
    
    # 获取缓存
    user = cache.get("user_1")
    logger.info(f"从缓存获取用户: {user}")
    
    # 获取另一个实例（实际上是同一个实例）
    another_cache = CacheSingleton()
    config = another_cache.get("config")
    logger.info(f"从另一个缓存实例获取配置: {config}")
    
    # 测试过期
    logger.info(f"临时数据 (过期前): {cache.get('temp_data')}")
    logger.info("等待6秒...")
    sleep(6)
    logger.info(f"临时数据 (过期后): {cache.get('temp_data')}")
    
    # 删除缓存
    cache.delete("user_1")
    logger.info(f"删除后尝试获取用户: {cache.get('user_1')}")
    
    # 获取所有缓存
    all_cache = cache.get_all()
    logger.info(f"所有缓存: {all_cache}")
    
    # 清空缓存
    cache.clear()
    logger.info(f"清空后的所有缓存: {cache.get_all()}")


if __name__ == "__main__":
    cache_demo()