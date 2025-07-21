import threading
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from common.log.logger import Logger

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

    def replace_placeholder(self, data_str):
        """替换字符串中的 ${variable_name} 占位符"""
        if not isinstance(data_str, str):
            return data_str  # 只处理字符串

        import re
        def replace_match(match):
            var_name = match.group(1)
            var_value = self.get(var_name)
            if var_value is None:
                # 如果变量不存在，可能需要报错或者返回原始占位符
                logger.error(f"Placeholder ${var_name} found but variable not set.")
                return match.group(0)  # 返回原始占位符，避免请求错误
            return str(var_value)  # 确保返回字符串

        return re.sub(r'\$\{(\w+)\}', replace_match, data_str)

    def prepare_data(self, data: Any) -> Any:
        """
        递归替换请求数据中的占位符
        :param data: 需要处理的数据
        :return: 处理后的数据
        """
        if isinstance(data, dict):
            return {k: self.prepare_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.prepare_data(elem) for elem in data]
        elif isinstance(data, str):
            # 检查字符串是否包含占位符 ${var_name}
            if '${' in data and '}' in data:
                try:
                    return self.replace_placeholder(data)
                except Exception as e:
                    logger.warning(f"Error replacing placeholder in '{data}': {e}")
                    return data
            return data
        else:
            return data