import requests
from common.log import Logger

# 配置日志记录
logger = Logger().get_logger()


class HttpClient:
    def __init__(self, timeout=10):
        """
        初始化 HTTP 客户端
        :param timeout: 请求超时时间，默认 10 秒
        """
        self.timeout = timeout
        self.session = requests.Session()

    def _request(self, method, url, **kwargs):
        """
        基础请求方法
        :param method: 请求方法，如 'GET', 'POST' 等
        :param url: 请求 URL
        :param kwargs: 其他 requests 请求参数
        :return: 响应对象或 None
        """
        try:
            kwargs.setdefault('timeout', self.timeout)
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()  # 检查响应状态码
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f'请求出错: {e}')
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