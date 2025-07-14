from typing import Dict, Optional, Union, Any
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from common.log import Logger

# 配置日志记录
logger = Logger().get_logger()


class HttpClient:
    def __init__(self, base_url: str, default_headers: Dict[str, str] = None, timeout: int = 30,
                 max_retries: int = 3, retry_delay: int = 1, pool_connections: int = 10, pool_maxsize: int = 10):
        """
        初始化 HTTP 客户端
        :param base_url: API 基础 URL
        :param default_headers: 默认请求头
        :param timeout: 请求超时时间，默认 30 秒
        :param max_retries: 最大重试次数，默认 3 次
        :param retry_delay: 重试延迟时间，默认 1 秒
        :param pool_connections: 连接池连接数，默认 10
        :param pool_maxsize: 连接池最大连接数，默认 10
        """
        self.base_url = base_url.rstrip('/')
        self.default_headers = default_headers or {}
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # 创建会话并配置连接池
        self.session = requests.Session()
        self.session.headers.update(self.default_headers)
        
        # 配置重试策略
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE", "PATCH"]
        )
        
        # 配置连接池适配器
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize
        )
        
        # 注册适配器
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """
        基础请求方法
        :param method: 请求方法，如 'GET', 'POST' 等
        :param url: 请求 URL
        :param kwargs: 其他 requests 请求参数
        :return: 响应对象或 None
        """
        start_time = time.time()
        try:
            # 构建完整URL
            full_url = f"{self.base_url}{url}"

            # 合并headers
            headers = self.default_headers.copy()
            if 'headers' in kwargs:
                headers.update(kwargs['headers'])
                kwargs['headers'] = headers

            # 设置超时
            kwargs.setdefault('timeout', self.timeout)
            
            # 记录请求信息
            logger.info(f'Request URL: {full_url}')
            logger.info(f'Request Method: {method}')
            logger.info(f'Request Headers: {headers}')
            if 'json' in kwargs:
                logger.info(f'Request Body (JSON): {kwargs.get("json")}')
            elif 'data' in kwargs:
                logger.info(f'Request Body (Form): {kwargs.get("data")}')
            
            # 发送请求
            response = self.session.request(method, full_url, **kwargs)
            
            # 计算请求耗时
            elapsed_time = time.time() - start_time
            
            # 记录响应信息
            logger.info(f'Response Status Code: {response.status_code} (took {elapsed_time:.2f}s)')
            try:
                response_json = response.json()
                logger.info(f'Response Body: {response_json}')
            except ValueError:
                logger.info(f'Response Body (text): {response.text[:500]}' + ('...' if len(response.text) > 500 else ''))

            return response
        except requests.exceptions.RequestException as e:
            elapsed_time = time.time() - start_time
            logger.error(f'Request failed after {elapsed_time:.2f}s: {str(e)}')
            return None

    def get(self, url, params=None, **kwargs):
        """
        发送 GET 请求
        :param url: 请求 URL
        :param params: 请求参数
        :param kwargs: 其他 requests 请求参数
        :return: 响应对象或 None
        """
        return self._request('GET', url, params=params, **kwargs)

    def post(self, url, data=None, json=None, **kwargs):
        """
        发送 POST 请求
        :param url: 请求 URL
        :param data: 表单数据
        :param json: JSON 数据
        :param kwargs: 其他 requests 请求参数
        :return: 响应对象或 None
        """
        return self._request('POST', url, data=data, json=json, **kwargs)

    def put(self, url, data=None, **kwargs):
        """
        发送 PUT 请求
        :param url: 请求 URL
        :param data: 表单数据
        :param kwargs: 其他 requests 请求参数
        :return: 响应对象或 None
        """
        return self._request('PUT', url, data=data, **kwargs)

    def delete(self, url, **kwargs):
        """
        发送 DELETE 请求
        :param url: 请求 URL
        :param kwargs: 其他 requests 请求参数
        :return: 响应对象或 None
        """
        return self._request('DELETE', url, **kwargs)

    def patch(self, url, data=None, **kwargs):
        """
        发送 PATCH 请求
        :param url: 请求 URL
        :param data: 表单数据
        :param kwargs: 其他 requests 请求参数
        :return: 响应对象或 None
        """
        return self._request('PATCH', url, data=data, **kwargs)

    def close(self):
        """
        关闭会话
        """
        self.session.close()


if __name__ == '__main__':
    # 使用示例
    client = HttpClient()
    response = client.get('https://httpbin.org/get')
    if response:
        print(response.json())
    client.close()