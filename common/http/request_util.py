# common/request_util.py
import requests
import json
import time
from typing import Dict, Any, Optional, Union, List
from requests.exceptions import RequestException, Timeout, ConnectionError

from common.log import Logger
import jsonpath_ng.ext as jsonpath # 用于 JSONPath 提取
from common.http.http_client import HttpClient
from core.patterns.singleton import CacheSingleton

logger = Logger().get_logger()

class RequestUtil:
    def __init__(self, base_url: str, timeout: int = 30, 
                 max_retries: int = 3, retry_delay: int = 1):
        """
        初始化请求工具类
        :param base_url: API 基础 URL
        :param timeout: 请求超时时间，默认 30 秒
        :param max_retries: 最大重试次数，默认 3 次
        :param retry_delay: 重试延迟时间，默认 1 秒
        """
        self.base_url = base_url
        self.http_client = HttpClient(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            default_headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        )
        self.cache = CacheSingleton()

    def send_request(self, method: str, path: str, headers: Dict = None, params: Dict = None, 
                   body: Dict = None, timeout: int = None, verify: bool = True) -> requests.Response:
        """
        发送HTTP请求
        :param method: HTTP方法 (GET, POST, PUT, DELETE等)
        :param path: 请求路径
        :param headers: 请求头
        :param params: URL参数
        :param body: 请求体
        :param timeout: 超时时间(秒)
        :param verify: 是否验证SSL证书
        :return: 响应对象
        :raises: RequestException 如果请求失败
        """
        # 替换请求头、参数、请求体中的变量
        processed_path = self.cache.prepare_data(path) if path else ''
        processed_headers = self.cache.prepare_data(headers) if headers else {}
        processed_params = self.cache.prepare_data(params) if params else {}
        processed_body = self.cache.prepare_data(body) if body else {}

        # 记录请求开始时间
        start_time = time.time()
        
        try:
            # 使用HTTP客户端发送请求
            if method.upper() == "GET":
                response = self.http_client.get(processed_path, params=processed_params, headers=processed_headers, timeout=timeout, verify=verify)
            elif method.upper() == "POST":
                response = self.http_client.post(processed_path, json=processed_body, params=processed_params, headers=processed_headers, timeout=timeout, verify=verify)
            elif method.upper() == "PUT":
                response = self.http_client.put(processed_path, json=processed_body, params=processed_params, headers=processed_headers, timeout=timeout, verify=verify)
            elif method.upper() == "DELETE":
                response = self.http_client.delete(processed_path, params=processed_params, headers=processed_headers, timeout=timeout, verify=verify)
            elif method.upper() == "PATCH":
                response = self.http_client.patch(processed_path, json=processed_body, params=processed_params, headers=processed_headers, timeout=timeout, verify=verify)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            if response is None:
                raise RequestException(f"Request failed: No response returned for {method} {path}")
                
            # 记录请求耗时
            elapsed_time = time.time() - start_time
            logger.debug(f"Request completed in {elapsed_time:.2f}s")
            
            return response
            
        except Timeout as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Request timeout after {elapsed_time:.2f}s: {str(e)}")
            raise
        except ConnectionError as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Connection error after {elapsed_time:.2f}s: {str(e)}")
            raise
        except RequestException as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Request failed after {elapsed_time:.2f}s: {str(e)}")
            raise

    def extract_variables_from_response(self, response: requests.Response, extract_rules: Dict[str, str], ttl: Optional[int] = None) -> Dict[str, Any]:
        """
        从响应中提取变量并存入变量池
        :param response: HTTP响应对象
        :param extract_rules: 提取规则，格式为 {变量名: JSONPath表达式}
        :param ttl: 变量的生存时间(秒)，None表示永不过期
        :return: 提取的变量字典 {变量名: 值}
        """
        extracted_vars = {}
        
        # 尝试解析JSON响应
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            logger.warning("Response is not JSON, trying to extract from text response.")
            # 如果不是JSON，尝试从文本响应中提取
            for var_name, pattern in extract_rules.items():
                if pattern.startswith('$.') or pattern.startswith('$['):
                    logger.warning(f"Cannot use JSONPath '{pattern}' on non-JSON response for variable '{var_name}'.")
                    continue
                    
                # 对于非JSONPath模式，可以实现简单的文本提取逻辑
                # 这里只是一个示例，可以根据需要扩展
                extracted_vars[var_name] = response.text
                self.cache.set(var_name, response.text, ttl)
                logger.info(f"Extracted text variable '{var_name}' with length: {len(response.text)} chars")
            return extracted_vars

        # 从JSON响应中提取变量
        for var_name, json_path_expr in extract_rules.items():
            try:
                jsonpath_expr = jsonpath.parse(json_path_expr)
                matches = jsonpath_expr.find(response_json)
                if matches:
                    extracted_value = matches[0].value
                    extracted_vars[var_name] = extracted_value
                    self.cache.set(var_name, extracted_value, ttl)
                    
                    # 对于大型值，只记录类型和摘要信息
                    if isinstance(extracted_value, (dict, list)) and len(str(extracted_value)) > 100:
                        value_type = type(extracted_value).__name__
                        value_size = len(str(extracted_value))
                        logger.info(f"Extracted variable '{var_name}' with {value_type} value (size: {value_size} chars)")
                    else:
                        logger.info(f"Extracted variable '{var_name}' with value: {extracted_value}")
                else:
                    logger.warning(f"JSONPath '{json_path_expr}' found no match for variable '{var_name}'.")
            except Exception as e:
                logger.error(f"Error extracting variable '{var_name}' with JSONPath '{json_path_expr}': {e}")
                
        return extracted_vars