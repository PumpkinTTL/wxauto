# -*- coding: utf-8 -*-
"""
Redis Lite 实现
用于实时日志传输和状态管理
"""
import json
import time
import threading
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque


class RedisLite:
    """
    轻量级Redis实现，用于实时日志和状态管理
    """

    def __init__(self):
        self._data = {}
        self._lists = defaultdict(deque)
        self._subscribers = defaultdict(list)
        self._lock = threading.RLock()
        self._running = True

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """
        设置键值对

        Args:
            key: 键名
            value: 值
            ex: 过期时间（秒）

        Returns:
            bool: 是否设置成功
        """
        try:
            with self._lock:
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)

                self._data[key] = {
                    'value': value,
                    'expire_time': time.time() + ex if ex else None
                }
                return True
        except Exception as e:
            print(f"RedisLite set error: {e}")
            return False

    def get(self, key: str) -> Any:
        """
        获取键值

        Args:
            key: 键名

        Returns:
            Any: 键对应的值，不存在或过期返回None
        """
        try:
            with self._lock:
                if key not in self._data:
                    return None

                item = self._data[key]

                # 检查是否过期
                if item['expire_time'] and time.time() > item['expire_time']:
                    del self._data[key]
                    return None

                value = item['value']

                # 尝试解析JSON
                if isinstance(value, str):
                    try:
                        return json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        return value

                return value
        except Exception as e:
            print(f"RedisLite get error: {e}")
            return None

    def delete(self, key: str) -> bool:
        """
        删除键

        Args:
            key: 键名

        Returns:
            bool: 是否删除成功
        """
        try:
            with self._lock:
                if key in self._data:
                    del self._data[key]
                    return True
                return False
        except Exception as e:
            print(f"RedisLite delete error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 键名

        Returns:
            bool: 键是否存在且未过期
        """
        return self.get(key) is not None

    def lpush(self, key: str, *values) -> int:
        """
        从列表左侧推入元素

        Args:
            key: 列表键名
            *values: 要推入的值

        Returns:
            int: 推入后列表长度
        """
        try:
            with self._lock:
                for value in values:
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value, ensure_ascii=False)
                    self._lists[key].appendleft(value)
                return len(self._lists[key])
        except Exception as e:
            print(f"RedisLite lpush error: {e}")
            return 0

    def rpush(self, key: str, *values) -> int:
        """
        从列表右侧推入元素

        Args:
            key: 列表键名
            *values: 要推入的值

        Returns:
            int: 推入后列表长度
        """
        try:
            with self._lock:
                for value in values:
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value, ensure_ascii=False)
                    self._lists[key].append(value)
                return len(self._lists[key])
        except Exception as e:
            print(f"RedisLite rpush error: {e}")
            return 0

    def lpop(self, key: str) -> Any:
        """
        从列表左侧弹出元素

        Args:
            key: 列表键名

        Returns:
            Any: 弹出的元素，列表为空返回None
        """
        try:
            with self._lock:
                if key in self._lists and self._lists[key]:
                    value = self._lists[key].popleft()
                    # 尝试解析JSON
                    if isinstance(value, str):
                        try:
                            return json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            return value
                    return value
                return None
        except Exception as e:
            print(f"RedisLite lpop error: {e}")
            return None

    def rpop(self, key: str) -> Any:
        """
        从列表右侧弹出元素

        Args:
            key: 列表键名

        Returns:
            Any: 弹出的元素，列表为空返回None
        """
        try:
            with self._lock:
                if key in self._lists and self._lists[key]:
                    value = self._lists[key].pop()
                    # 尝试解析JSON
                    if isinstance(value, str):
                        try:
                            return json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            return value
                    return value
                return None
        except Exception as e:
            print(f"RedisLite rpop error: {e}")
            return None

    def lrange(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """
        获取列表范围内的元素

        Args:
            key: 列表键名
            start: 开始索引
            end: 结束索引（-1表示到末尾）

        Returns:
            List[Any]: 范围内的元素列表
        """
        try:
            with self._lock:
                if key not in self._lists:
                    return []

                lst = list(self._lists[key])
                if end == -1:
                    result = lst[start:]
                else:
                    result = lst[start:end+1]

                # 解析JSON
                parsed_result = []
                for value in result:
                    if isinstance(value, str):
                        try:
                            parsed_result.append(json.loads(value))
                        except (json.JSONDecodeError, TypeError):
                            parsed_result.append(value)
                    else:
                        parsed_result.append(value)

                return parsed_result
        except Exception as e:
            print(f"RedisLite lrange error: {e}")
            return []

    def llen(self, key: str) -> int:
        """
        获取列表长度

        Args:
            key: 列表键名

        Returns:
            int: 列表长度
        """
        try:
            with self._lock:
                return len(self._lists.get(key, []))
        except Exception as e:
            print(f"RedisLite llen error: {e}")
            return 0

    def ltrim(self, key: str, start: int, end: int) -> bool:
        """
        修剪列表，只保留指定范围内的元素

        Args:
            key: 列表键名
            start: 开始索引
            end: 结束索引

        Returns:
            bool: 是否操作成功
        """
        try:
            with self._lock:
                if key in self._lists:
                    lst = list(self._lists[key])
                    if end == -1:
                        trimmed = lst[start:]
                    else:
                        trimmed = lst[start:end+1]
                    self._lists[key] = deque(trimmed)
                return True
        except Exception as e:
            print(f"RedisLite ltrim error: {e}")
            return False

    def flushall(self) -> bool:
        """
        清空所有数据

        Returns:
            bool: 是否清空成功
        """
        try:
            with self._lock:
                self._data.clear()
                self._lists.clear()
                return True
        except Exception as e:
            print(f"RedisLite flushall error: {e}")
            return False

    def keys(self, pattern: str = "*") -> List[str]:
        """
        获取匹配模式的所有键名

        Args:
            pattern: 匹配模式（简单支持*通配符）

        Returns:
            List[str]: 匹配的键名列表
        """
        try:
            with self._lock:
                all_keys = list(self._data.keys()) + list(self._lists.keys())

                if pattern == "*":
                    return all_keys

                # 简单的通配符匹配
                import fnmatch
                return [key for key in all_keys if fnmatch.fnmatch(key, pattern)]
        except Exception as e:
            print(f"RedisLite keys error: {e}")
            return []


# 全局实例
redis_lite = RedisLite()


class LogManager:
    """
    日志管理器，基于RedisLite实现实时日志功能
    """

    def __init__(self, redis_instance: RedisLite = None):
        self.redis = redis_instance or redis_lite
        self.log_key = "wechat:logs"
        self.status_key = "wechat:status"
        self.max_logs = 1000  # 最大日志条数

    def add_log(self, message: str, log_type: str = "info", module: str = "system") -> bool:
        """
        添加日志

        Args:
            message: 日志消息
            log_type: 日志类型 (info, warning, error, success)
            module: 模块名称

        Returns:
            bool: 是否添加成功
        """
        try:
            log_entry = {
                "time": time.strftime("%H:%M:%S"),
                "timestamp": time.time(),
                "message": message,
                "type": log_type,
                "module": module
            }

            # 添加到日志列表
            self.redis.rpush(self.log_key, log_entry)

            # 保持日志数量在限制内
            if self.redis.llen(self.log_key) > self.max_logs:
                self.redis.ltrim(self.log_key, -self.max_logs, -1)

            return True
        except Exception as e:
            print(f"LogManager add_log error: {e}")
            return False

    def get_logs(self, count: int = 100) -> List[Dict]:
        """
        获取最新的日志

        Args:
            count: 获取的日志数量

        Returns:
            List[Dict]: 日志列表
        """
        try:
            return self.redis.lrange(self.log_key, -count, -1)
        except Exception as e:
            print(f"LogManager get_logs error: {e}")
            return []

    def clear_logs(self) -> bool:
        """
        清空日志

        Returns:
            bool: 是否清空成功
        """
        try:
            return self.redis.delete(self.log_key)
        except Exception as e:
            print(f"LogManager clear_logs error: {e}")
            return False

    def set_status(self, key: str, value: Any) -> bool:
        """
        设置状态

        Args:
            key: 状态键
            value: 状态值

        Returns:
            bool: 是否设置成功
        """
        try:
            status_data = self.redis.get(self.status_key) or {}
            status_data[key] = value
            return self.redis.set(self.status_key, status_data)
        except Exception as e:
            print(f"LogManager set_status error: {e}")
            return False

    def get_status(self, key: str = None) -> Any:
        """
        获取状态

        Args:
            key: 状态键，为None时返回所有状态

        Returns:
            Any: 状态值
        """
        try:
            status_data = self.redis.get(self.status_key) or {}
            if key is None:
                return status_data
            return status_data.get(key)
        except Exception as e:
            print(f"LogManager get_status error: {e}")
            return None


# 全局日志管理器实例
log_manager = LogManager()


def get_redis() -> RedisLite:
    """获取Redis实例"""
    return redis_lite


def get_log_manager() -> LogManager:
    """获取日志管理器实例"""
    return log_manager


if __name__ == "__main__":
    # 测试代码
    print("测试 RedisLite...")

    # 测试基本操作
    redis_lite.set("test_key", "test_value")
    print(f"get test_key: {redis_lite.get('test_key')}")

    # 测试JSON
    redis_lite.set("test_json", {"name": "张三", "age": 25})
    print(f"get test_json: {redis_lite.get('test_json')}")

    # 测试列表
    redis_lite.rpush("test_list", "item1", "item2", {"key": "value"})
    print(f"lrange test_list: {redis_lite.lrange('test_list', 0, -1)}")

    # 测试日志管理器
    print("\n测试 LogManager...")
    log_manager.add_log("系统启动", "info", "system")
    log_manager.add_log("用户登录", "success", "auth")
    log_manager.add_log("连接失败", "error", "network")

    logs = log_manager.get_logs()
    for log in logs:
        print(f"[{log['time']}] {log['type'].upper()}: {log['message']}")

    # 测试状态管理
    log_manager.set_status("wechat_connected", True)
    log_manager.set_status("processing", False)
    print(f"\n状态: {log_manager.get_status()}")

    print("\nRedisLite 测试完成！")