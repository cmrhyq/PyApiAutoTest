# common/request_util.py
import requests
import json
from common.log import Logger
import jsonpath_ng.ext as jsonpath # 用于 JSONPath 提取

from core.patterns.singleton import CacheSingleton

logger = Logger().get_logger()

class RequestUtil:
    def __init__(self, base_url="https://jsonplaceholder.typicode.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.cache = CacheSingleton()

    def _prepare_data(self, data):
        """递归替换请求数据中的占位符"""
        if isinstance(data, dict):
            return {k: self._prepare_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._prepare_data(elem) for elem in data]
        elif isinstance(data, str):
            return self.cache.replace_placeholder(data)
        else:
            return data

    def send_request(self, method, path, headers=None, params=None, body=None):
        full_url = f"{self.base_url}{path}"

        # 替换请求头、参数、请求体中的变量
        processed_headers = self._prepare_data(headers) if headers else {}
        processed_params = self._prepare_data(params) if params else {}
        processed_body = self._prepare_data(body) if body else {}

        logger.info(f"Sending {method} request to: {full_url}")
        logger.info(f"Headers: {processed_headers}")
        logger.info(f"Params: {processed_params}")
        logger.info(f"Body: {processed_body}")

        try:
            if method.upper() == "GET":
                response = self.session.get(full_url, headers=processed_headers, params=processed_params)
            elif method.upper() == "POST":
                response = self.session.post(full_url, headers=processed_headers, params=processed_params, json=processed_body)
            elif method.upper() == "PUT":
                response = self.session.put(full_url, headers=processed_headers, params=processed_params, json=processed_body)
            elif method.upper() == "DELETE":
                response = self.session.delete(full_url, headers=processed_headers, params=processed_params, json=processed_body)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            logger.info(f"Received response status: {response.status_code}")
            try:
                logger.info(f"Received response body: {response.json()}")
            except json.JSONDecodeError:
                logger.info(f"Received response body (text): {response.text}")
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {full_url}: {e}")
            raise

    def extract_variables_from_response(self, response, extract_rules):
        """从响应中提取变量并存入变量池"""
        try:
            response_json = response.json()
        except json.JSONDecodeError:
            logger.warning("Response is not JSON, cannot extract variables.")
            return

        for var_name, json_path_expr in extract_rules.items():
            try:
                jsonpath_expr = jsonpath.parse(json_path_expr)
                matches = jsonpath_expr.find(response_json)
                if matches:
                    extracted_value = matches[0].value
                    self.cache.set(var_name, extracted_value)
                    logger.info(f"Extracted variable '{var_name}' with value: {extracted_value}")
                else:
                    logger.warning(f"JSONPath '{json_path_expr}' found no match for variable '{var_name}'.")
            except Exception as e:
                logger.error(f"Error extracting variable '{var_name}' with JSONPath '{json_path_expr}': {e}")