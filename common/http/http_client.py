from typing import Dict

import requests
from common.log import Logger

# 配置日志记录
logger = Logger().get_logger()


class HttpClient:
    def __init__(self, base_url: str, default_headers: Dict[str, str] = None, timeout: int = 30):
        """
        初始化 HTTP 客户端
        :param timeout: 请求超时时间，默认 10 秒
        """
        self.base_url = base_url.rstrip('/')
        self.default_headers = default_headers or {}
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(self.default_headers)

    def _request(self, method, url, **kwargs):
        """
        基础请求方法
        :param method: 请求方法，如 'GET', 'POST' 等
        :param url: 请求 URL
        :param kwargs: 其他 requests 请求参数
        :return: 响应对象或 None
        """
        try:
            """发送HTTP请求"""
            url = f"{self.base_url}{url}"

            # 合并headers
            headers = self.default_headers.copy()
            if 'headers' in kwargs:
                headers.update(kwargs['headers'])
                kwargs['headers'] = headers

            # 设置超时
            kwargs.setdefault('timeout', self.timeout)
            # 发送请求
            response = self.session.request(method, url, **kwargs)

            logger.info(f'Request URL: {url}')
            logger.info(f'Request Method: {method}')
            logger.info(f'Request Headers: {kwargs.get("headers", {})}')
            logger.info(f'Request Body: {kwargs.get("json", {})}')
            logger.info(f'Response Status Code: {response.status_code}')
            logger.info(f'Response Body: {response.json()}')

            return response
        except requests.exceptions.RequestException as e:
            logger.error(f'发送请求出错: {e}')
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