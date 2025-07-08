# 全局缓存系统

这个模块提供了一个基于单例模式的全局缓存系统，可以在整个项目的任何地方使用，无需依赖外部中间件。

## 特性

- 基于单例模式，确保全局唯一实例
- 支持设置缓存过期时间（TTL）
- 线程安全，可在多线程环境下使用
- 提供完整的缓存操作API：设置、获取、删除、清空等
- 自动清理过期数据

## 使用方法

### 导入缓存类

```python
from core.patterns.singleton import CacheSingleton
```

### 获取缓存实例

```python
cache = CacheSingleton()
```

### 设置缓存

```python
# 设置永不过期的缓存
cache.set("user_info", {"id": 1, "name": "张三"})

# 设置带过期时间的缓存（单位：秒）
cache.set("session_token", "abc123xyz", ttl=3600)  # 1小时后过期
```

### 获取缓存

```python
# 获取缓存，如果不存在或已过期则返回None
user_info = cache.get("user_info")

# 获取缓存，指定默认值
token = cache.get("api_token", default="default_token")
```

### 删除缓存

```python
# 删除单个缓存项
cache.delete("user_info")

# 清空所有缓存
cache.clear()
```

### 获取所有缓存

```python
# 获取所有未过期的缓存项
all_cache = cache.get_all()
```

## 示例

```python
from core.patterns.singleton import CacheSingleton

# 获取缓存实例
cache = CacheSingleton()

# 设置缓存
cache.set("config", {"debug": True, "timeout": 30})

# 在其他模块中获取相同的缓存实例
from core.patterns.singleton import CacheSingleton
other_cache = CacheSingleton()  # 实际上是同一个实例

# 获取之前设置的缓存
config = other_cache.get("config")  # 返回 {"debug": True, "timeout": 30}
```

## 注意事项

1. 缓存数据存储在内存中，应用重启后数据会丢失
2. 适合存储临时数据、配置信息、API响应等
3. 不适合存储大量数据，可能导致内存占用过高
4. 对于需要持久化的数据，建议使用数据库存储