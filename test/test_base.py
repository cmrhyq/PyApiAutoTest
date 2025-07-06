import requests
from common.log import Logger
from core.config.ini.read_config_ini import ReadConfigIni

logger = Logger().get_logger()

class TestBase:
    def __init__(self):
        self.config = ReadConfigIni()
        self.base_url = self.config.interface_url
        self.session = requests.Session()

    def send_request(self, method, path, **kwargs):
        url = self.base_url + path
        try:
            response = self.session.request(method, url, **kwargs)
            logger.info(f'Request URL: {url}')
            logger.info(f'Request Method: {method}')
            logger.info(f'Request Headers: {kwargs.get("headers", {})}')
            logger.info(f'Request Body: {kwargs.get("json", {})}')
            logger.info(f'Response Status Code: {response.status_code}')
            logger.info(f'Response Body: {response.json()}')
            return response
        except Exception as e:
            logger.error(f'Request failed: {str(e)}')
            raise