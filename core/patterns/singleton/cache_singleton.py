import threading
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from common.log import Logger

logger = Logger().get_logger()

class CacheSingleton:
    _instance = None  # 单例实例
    _lock = threading.Lock()  # 线程安全锁

    def __new__(cls):
        with cls._lock:  # 确保多线程下只有一个实例
            if cls._instance is None:
                cls._instance = super(CacheSingleton, cls).__new__(cls)
                cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """初始化缓存"""
        self._cache: Dict[str, Dict[str, Any]] = {}

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），如果不设置则永不过期
        """
        cache_item = {
            'value': value,
            'expire_time': datetime.now() + timedelta(seconds=ttl) if ttl else None
        }
        with self._lock:
            self._cache[key] = cache_item
            logger.debug(f"Cache set: {key}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取缓存值

        Args:
            key: 缓存键
            default: 如果键不存在或已过期时返回的默认值

        Returns:
            缓存值或默认值
        """
        with self._lock:
            if key not in self._cache:
                return default

            cache_item = self._cache[key]
            if cache_item['expire_time'] and datetime.now() > cache_item['expire_time']:
                del self._cache[key]
                logger.debug(f"Cache expired: {key}")
                return default

            logger.debug(f"Cache hit: {key}")
            return cache_item['value']

    def delete(self, key: str) -> bool:
        """删除缓存项

        Args:
            key: 缓存键

        Returns:
            是否成功删除
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache deleted: {key}")
                return True
            return False

    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
            logger.debug("Cache cleared")

    def get_all(self) -> Dict[str, Any]:
        """获取所有未过期的缓存项

        Returns:
            包含所有未过期缓存项的字典
        """
        result = {}
        with self._lock:
            now = datetime.now()
            for key, item in list(self._cache.items()):
                if item['expire_time'] is None or now <= item['expire_time']:
                    result[key] = item['value']
                else:
                    del self._cache[key]
                    logger.debug(f"Cache expired: {key}")
        return result